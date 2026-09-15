from __future__ import annotations

from types import SimpleNamespace

import pytest

from champ_tableops.reasoning.command_parser import UnsupportedCommandError
from champ_tableops.reasoning.openvino_reasoner import (
    OpenVINOReasoner,
    OpenVINOReasoningError,
    build_reasoning_prompt,
    reason_command,
)


class FakePipeline:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def generate(self, prompt, **kwargs):
        self.calls.append((prompt, kwargs))
        return self.response


def factory_for(response):
    pipeline = FakePipeline(response)

    def factory(model_path, device):
        assert model_path
        assert device == "CPU"
        return pipeline

    return pipeline, factory


def test_openvino_reasoner_maps_json_to_verified_task():
    pipeline, factory = factory_for(
        '{"supported": true, "action": "place", "object": "plate", '
        '"target": "place_setting_1"}'
    )

    result = OpenVINOReasoner(
        "fake-model",
        pipeline_factory=factory,
    ).reason("Please set a plate for me.")

    assert result.backend == "openvino_genai"
    assert result.intent.action == "place"
    assert result.intent.object_name == "plate"
    assert result.intent.target == "place_setting_1"
    assert len(pipeline.calls) == 1
    assert pipeline.calls[0][1]["do_sample"] is False
    assert pipeline.calls[0][1]["apply_chat_template"] is True


def test_bimanual_prompt_explicitly_marks_showcase_command_supported():
    prompt = build_reasoning_prompt("Set the table for two.")
    assert '"action": "set_table"' in prompt
    assert '"target": "place_settings_1_2"' in prompt
    assert 'exact command "Set the table for two." is explicitly supported' in prompt


def test_openvino_reasoner_accepts_decoded_results_and_fenced_json():
    response = SimpleNamespace(
        texts=[
            "```json\n"
            '{"supported": true, "action": "place", "object": "plate", '
            '"target": "place_setting_1"}\n'
            "```"
        ]
    )
    _, factory = factory_for(response)

    result = OpenVINOReasoner(
        "fake-model",
        pipeline_factory=factory,
    ).reason("Set the plate.")

    assert result.intent.object_name == "plate"


def test_openvino_reasoner_rejects_unverified_controller_task():
    _, factory = factory_for(
        '{"supported": true, "action": "place", "object": "cup", '
        '"target": "place_setting_1"}'
    )

    with pytest.raises(OpenVINOReasoningError, match="outside the verified controller"):
        OpenVINOReasoner("fake-model", pipeline_factory=factory).reason(
            "Put the cup down."
        )


def test_openvino_reasoner_maps_two_place_request_to_bimanual_task():
    _, factory = factory_for(
        '{"supported": true, "action": "set_table", "object": "plates", '
        '"target": "place_settings_1_2"}'
    )

    result = OpenVINOReasoner("fake-model", pipeline_factory=factory).reason(
        "Set the table for two."
    )

    assert result.intent.action == "set_table"
    assert result.intent.object_name == "plates"
    assert result.intent.target == "place_settings_1_2"


def test_auto_backend_falls_back_to_deterministic_parser_on_runtime_failure():
    def broken_factory(model_path, device):
        raise RuntimeError("simulated OpenVINO initialization failure")

    result = reason_command(
        "Set the plate.",
        backend="auto",
        model_path="fake-model",
        pipeline_factory=broken_factory,
    )

    assert result.backend == "deterministic"
    assert result.fallback_used is True
    assert "initialization failure" in result.fallback_reason
    assert result.intent.object_name == "plate"


def test_explicit_openvino_backend_requires_model_path():
    with pytest.raises(OpenVINOReasoningError, match="requires --openvino-model"):
        reason_command("Set the plate.", backend="openvino")
