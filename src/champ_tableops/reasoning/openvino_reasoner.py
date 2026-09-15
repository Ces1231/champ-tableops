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
    """Build a constrained prompt whose output maps to the TableOps task contract."""
    return f"""You are the CHAMP TableOps task reasoner.
Convert the user command into exactly one JSON object and nothing else.

Supported task for this hackathon milestone:
- action: place
- object: plate
- target: place_setting_1

If the command requests anything outside that capability, return:
{{"supported": false, "reason": "short explanation"}}

If supported, return exactly:
{{"supported": true, "action": "place", "object": "plate", "target": "place_setting_1"}}

User command: {command!r}
JSON:"""


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

    expected = ("place", "plate", "place_setting_1")
    actual = (action, object_name, target)
    if actual != expected:
        raise OpenVINOReasoningError(
            "OpenVINO reasoner produced a task outside the verified controller contract: "
            f"action={action!r}, object={object_name!r}, target={target!r}."
        )

    return TaskIntent(
        action="place",
        object_name="plate",
        target="place_setting_1",
        source_command=command,
    )


class OpenVINOReasoner:
    """OpenVINO GenAI adapter that emits the same TaskIntent used by Milestone 3."""

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
    """Resolve a command with OpenVINO when configured, preserving a safe fallback.

    backend="auto" uses OpenVINO when a model path is supplied. If initialization or
    generation fails, the known-good deterministic Milestone 3 parser remains available
    so the physical demo is not lost because of an AI-runtime issue.
    """
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
