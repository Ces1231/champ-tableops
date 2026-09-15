# CHAMP TableOps

**Voice-Guided Physical AI for Bimanual Table Setting**

CHAMP TableOps is a hackathon prototype for the **AI Infra Summit Hackathon 2026**.

The system is designed around a closed-loop Physical AI workflow:

**Perceive → Reason → Plan → Act → Verify → Correct**

The current prototype performs natural-language-guided table manipulation in MuJoCo, verifies the result, and can physically correct an intentionally bad placement before completing the task.

## Current Hackathon Status

### Milestone 1 — Complete

Load a MuJoCo tabletop scene and verify programmatic object movement.

### Milestone 2 — Complete

An actuated MuJoCo manipulator approaches a plate, aligns with it, closes its gripper, lifts it, transfers it to the target, releases it, retreats, and verifies final placement.

The controller does **not** rewrite the plate free-joint position to perform the move. Cartesian motion is generated through MuJoCo actuators. A temporary equality constraint models a stable grasp and is released at placement.

### Milestone 3 — Complete

Natural-language commands such as `Set the plate.` and `Set the table for one.` are converted into a verified task contract and executed by the robotic controller.

### Milestone 4 — Complete

Closed-loop recovery is working. TableOps can intentionally place the plate outside tolerance, detect the error, execute a correction action, re-verify the scene, and finish successfully.

### Milestone 5 — Implementation complete / local OpenVINO model validation next

An Intel OpenVINO GenAI reasoning adapter now maps natural-language commands into the same verified `TaskIntent` contract. The deterministic parser remains available as a fallback so a model/runtime problem does not destroy the robotics demo.

Current end-to-end target:

**Natural language → OpenVINO GenAI → Plan → Act → Verify → Correct → Success**

## Objectives

- Observe a simulated tabletop scene.
- Convert natural-language or spoken instructions into structured tasks.
- Use Intel OpenVINO GenAI for local task reasoning.
- Plan manipulation actions.
- Execute robotic pick-and-place in MuJoCo.
- Verify the resulting scene.
- Correct failed or incomplete placements.
- Extend to additional objects and a second manipulator.

## Stack

- Python 3.11+
- MuJoCo 3.3+
- Intel OpenVINO GenAI
- Qwen2.5-1.5B-Instruct INT4 OpenVINO IR model for the Milestone 5 local reasoning demo
- Pytest
- Docker for reproducible execution
- Optional speech-to-text / voice interface in a later milestone

## Repository Layout

```text
champ-tableops/
├── .github/workflows/
├── assets/
├── demo/
│   └── tableops_cli.py
├── docker/
├── docs/
│   └── openvino_reasoning.md
├── outputs/
├── scripts/
├── simulation/
│   ├── demo_pick_place.py
│   ├── milestone1.py
│   ├── table_scene.xml
│   └── table_scene_v2.xml
├── src/champ_tableops/
│   ├── manipulation/
│   ├── perception/
│   ├── planning/
│   ├── reasoning/
│   │   ├── command_parser.py
│   │   └── openvino_reasoner.py
│   ├── verification/
│   └── voice/
├── requirements.txt
├── requirements-openvino.txt
└── tests/
```

## Quick Start

### Linux / WSL / macOS

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pytest -v
```

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pytest -v
```

## Known-Good Deterministic Demo

Headless:

```bash
python demo/tableops_cli.py --headless --fast "Set the plate."
```

Visual:

```bash
python demo/tableops_cli.py "Set the plate."
```

Closed-loop correction:

```bash
python demo/tableops_cli.py --headless --fast --demo-correction "Set the plate."
```

## Milestone 5 — Intel OpenVINO GenAI

Install the optional stack:

```bash
python -m pip install -r requirements-openvino.txt
```

Download the recommended OpenVINO-optimized model:

```bash
python - <<'PY'
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="OpenVINO/Qwen2.5-1.5B-Instruct-int4-ov",
    local_dir="models/qwen2.5-1.5b-instruct-int4-ov",
)
PY
```

Configure the model:

```bash
export CHAMP_TABLEOPS_OPENVINO_MODEL="$PWD/models/qwen2.5-1.5b-instruct-int4-ov"
export CHAMP_TABLEOPS_OPENVINO_DEVICE=CPU
```

Run explicit Intel reasoning:

```bash
python demo/tableops_cli.py \
  --headless --fast \
  --reasoner openvino \
  "Set the plate."
```

Full OpenVINO + recovery demo:

```bash
python demo/tableops_cli.py \
  --reasoner openvino \
  --demo-correction \
  "Set the plate."
```

See `docs/openvino_reasoning.md` for setup details and fallback behavior.

## Safety Boundary

The AI reasoner does not directly control robot joints. It must emit the currently verified controller contract:

```json
{
  "action": "place",
  "object": "plate",
  "target": "place_setting_1"
}
```

Any model-produced task outside that contract is rejected before manipulation begins.

## Roadmap

**Milestone 1 — Complete:** base MuJoCo scene.

**Milestone 2 — Complete:** actuator-driven plate pick-and-place.

**Milestone 3 — Complete:** natural-language command interface.

**Milestone 4 — Complete:** Verify → Correct closed-loop recovery.

**Milestone 5 — Current:** Intel OpenVINO GenAI reasoning, pending local model validation.

**Milestone 6 — Next:** add a second table object and expand scene/task planning.

**Milestone 7 — Stretch:** second manipulator / bimanual coordination, richer perception, and voice input.

## License

MIT License. See [LICENSE](LICENSE).
