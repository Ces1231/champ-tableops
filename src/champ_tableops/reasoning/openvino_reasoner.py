from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Callable

from champ_tableops.reasoning.command_parser import (
    TaskIntent,
    UnsupportedCommandError,
    parse_command,
)


class OpenVINOReasoningError(RuntimeError):
    """Raised when the OpenVINO reasoning backend cannot produce a safe task."""


@dataclass(frozen=True)
class ReasoningResult:
    intent: TaskIntent
    backend: str
    fallback_used: bool = False
    fallback_reason: str | None = None
    raw_response: str | None = None


PipelineFactory = Callable[[str, str], Any]


def build_reasoning_prompt(command: str) -> str:
    """Build a constrained classifier prompt for the verified TableOps tasks."""
    return f"""You are a strict task classifier for CHAMP TableOps.
Your job is ONLY to map the user's command to one of the verified JSON task contracts below.
Return exactly one JSON object and no explanation.

VERIFIED TASK A — one plate / one place setting:
{{"supported": true, "action": "place", "object": "plate", "target": "place_setting_1"}}

VERIFIED TASK B — two plates / two place settings / bimanual table setting:
{{"supported": true, "action": "set_table", "object": "plates", "target": "place_settings_1_2"}}

UNSUPPORTED:
{{"supported": false, "reason": "short explanation"}}

Classification rules:
- "Set the plate.", "Place the plate.", and "Set the table for one." are Task A.
- "Set the table for two.", "Set a table for two.", and equivalent requests for TWO place settings are Task B.
- The exact command "Set the table for two." is explicitly supported. It MUST return Task B.
- Do not reject a supported command merely because it is phrased as an instruction.
- Do not invent any task fields or values outside the contracts above.

Examples:
User: Set the plate.
Assistant: {{"supported": true, "action": "place", "object": "plate", "target": "place_setting_1"}}

User: Set the table for two.
Assistant: {{"supported": true, "action": "set_table", "object": "plates", "target": "place_settings_1_2"}}

User: Wash the dishes.
Assistant: {{"supported": false, "reason": "Dish washing is not a verified TableOps task."}}

Now classify this command.
User: {command}
Assistant:"""


def _response_text(response: Any) -> str:
    if isinstance(response, str):
        return response.strip()

    texts = getattr(response, "texts", None)
    if texts:
        return str(texts[0]).strip()

    raise OpenVINOReasoningError(
        f"OpenVINO GenAI returned an unsupported response type: {type(response).__name__}"
    )


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end < start:
        raise OpenVINOReasoningError(
            f"OpenVINO reasoner did not return a JSON object: {text!r}"
        )

    try:
        payload = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise OpenVINOReasoningError(
            f"OpenVINO reasoner returned invalid JSON: {exc.msg}"
        ) from exc

    if not isinstance(payload, dict):
        raise OpenVINOReasoningError("OpenVINO reasoner JSON must be an object.")
    return payload


def _intent_from_payload(payload: dict[str, Any], command: str) -> TaskIntent:
    if payload.get("supported") is not True:
        reason = str(payload.get("reason") or "Command is outside the supported task set.")
        raise UnsupportedCommandError(reason)

    action = payload.get("action")
    object_name = payload.get("object")
    target = payload.get("target")
    actual = (action, object_name, target)

    verified_tasks = {
        ("place", "plate", "place_setting_1"),
        ("set_table", "plates", "place_settings_1_2"),
    }
    if actual not in verified_tasks:
        raise OpenVINOReasoningError(
            "OpenVINO reasoner produced a task outside the verified controller contract: "
            f"action={action!r}, object={object_name!r}, target={target!r}."
        )

    return TaskIntent(
        action=str(action),
        object_name=str(object_name),
        target=str(target),
        source_command=command,
    )


class OpenVINOReasoner:
    """OpenVINO GenAI adapter that emits a verified TableOps TaskIntent."""

    def __init__(
        self,
        model_path: str | Path,
        *,
        device: str = "CPU",
        pipeline_factory: PipelineFactory | None = None,
    ) -> None:
        self.model_path = str(Path(model_path).expanduser())
        self.device = device

        if pipeline_factory is None:
            model_dir = Path(self.model_path)
            if not model_dir.exists():
                raise OpenVINOReasoningError(
                    f"OpenVINO model directory does not exist: {model_dir}"
                )
            try:
                import openvino_genai as ov_genai
            except ImportError as exc:
                raise OpenVINOReasoningError(
                    "openvino-genai is not installed. Install requirements-openvino.txt."
                ) from exc
            pipeline_factory = lambda path, selected_device: ov_genai.LLMPipeline(
                path, selected_device
            )

        try:
            self.pipeline = pipeline_factory(self.model_path, self.device)
        except Exception as exc:  # backend errors vary by OpenVINO release/device
            raise OpenVINOReasoningError(
                f"Unable to initialize OpenVINO GenAI on {self.device}: {exc}"
            ) from exc

    def reason(self, command: str) -> ReasoningResult:
        prompt = build_reasoning_prompt(command)
        try:
            response = self.pipeline.generate(
                prompt,
                max_new_tokens=96,
                do_sample=False,
                apply_chat_template=True,
            )
        except Exception as exc:
            raise OpenVINOReasoningError(
                f"OpenVINO GenAI generation failed: {exc}"
            ) from exc

        text = _response_text(response)
        payload = _extract_json(text)
        intent = _intent_from_payload(payload, command)
        return ReasoningResult(
            intent=intent,
            backend="openvino_genai",
            raw_response=text,
        )


def reason_command(
    command: str,
    *,
    backend: str = "auto",
    model_path: str | Path | None = None,
    device: str = "CPU",
    pipeline_factory: PipelineFactory | None = None,
) -> ReasoningResult:
    """Resolve a command with OpenVINO when configured, preserving a safe fallback."""
    backend = backend.lower().strip()
    if backend not in {"auto", "deterministic", "openvino"}:
        raise ValueError(f"Unknown reasoning backend: {backend}")

    if backend == "deterministic":
        return ReasoningResult(intent=parse_command(command), backend="deterministic")

    if backend == "openvino" and model_path is None:
        raise OpenVINOReasoningError(
            "--reasoner openvino requires --openvino-model or "
            "CHAMP_TABLEOPS_OPENVINO_MODEL."
        )

    if model_path is not None:
        try:
            return OpenVINOReasoner(
                model_path,
                device=device,
                pipeline_factory=pipeline_factory,
            ).reason(command)
        except UnsupportedCommandError:
            raise
        except OpenVINOReasoningError as exc:
            if backend == "openvino":
                raise
            return ReasoningResult(
                intent=parse_command(command),
                backend="deterministic",
                fallback_used=True,
                fallback_reason=str(exc),
            )

    return ReasoningResult(intent=parse_command(command), backend="deterministic")
