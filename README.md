# CHAMP TableOps

**Voice-Guided Physical AI for Bimanual Table Setting**

CHAMP TableOps is a hackathon prototype for the **AI Infra Summit Hackathon 2026**.

The system implements a closed-loop Physical AI workflow:

**Perceive → Reason → Plan → Act → Verify → Correct → Re-Verify**

The current prototype combines natural-language reasoning, Intel OpenVINO GenAI, two coordinated MuJoCo manipulators, placement verification, and physical correction behavior.

## Current Hackathon Status

### Milestone 1 — Complete

Load a MuJoCo tabletop scene and verify programmatic object movement.

### Milestone 2 — Complete

An actuated MuJoCo manipulator approaches a plate, grasps it, transfers it to a target, releases it, retreats, and verifies the result. Robot motion is generated through MuJoCo actuators; the controller does not rewrite the plate free-joint position to perform the move.

### Milestone 3 — Complete

Natural-language commands such as `Set the plate.` and `Set the table for one.` are converted into a verified task contract and executed by the robotic controller.

### Milestone 4 — Complete

Closed-loop recovery is working. TableOps can detect an intentionally bad placement, execute a correction action, re-verify the scene, and finish successfully.

### Milestone 5 — Complete

Intel OpenVINO GenAI locally maps natural-language commands into the verified `TaskIntent` contract. The deterministic parser remains available as a fallback.

### Milestone 6 — Complete

A two-place MuJoCo scene contains two plates, two target place settings, and two independently actuated manipulators. The bimanual controller coordinates both arms through approach, grasp, lift, transfer, placement, release, retreat, and verification. The recovery path can intentionally disturb the right-hand placement by 10 cm and use the right manipulator to repair it before release.

Current end-to-end path:

**Natural language → Intel OpenVINO GenAI → Bimanual plan → Two-arm actuation → Verify → Correct → Re-Verify → Success**

## Final Showcase

The polished hackathon path is now a single command:

```bash
python demo/tableops_cli.py --showcase
```

`--showcase` fixes the live task to:

```text
Set the table for two.
```

It then requires the Intel OpenVINO GenAI reasoner, runs the two-arm MuJoCo scene, deliberately injects a 10 cm right-hand placement error, detects the miss, physically corrects it, verifies both place settings again, and reports the final showcase result.

For a headless preflight:

```bash
python demo/tableops_cli.py --showcase --headless --fast
```

Expected final lines include:

```text
[TableOps] VERIFY: both place settings accepted
[TableOps] SUCCESS
MILESTONE 6: SUCCESS
CHAMP TABLEOPS SHOWCASE: SUCCESS
```

See `docs/final_showcase_runbook.md` for the live-demo checklist, proof points, fallback command, and short narration.

## Stack

- Python 3.11+
- MuJoCo 3.3+
- Intel OpenVINO GenAI
- Qwen2.5-1.5B-Instruct INT4 OpenVINO IR model
- Pytest
- Docker for reproducible execution

## Repository Layout

```text
champ-tableops/
├── demo/
│   └── tableops_cli.py
├── docs/
│   ├── final_showcase_runbook.md
│   └── openvino_reasoning.md
├── simulation/
│   ├── demo_pick_place.py
│   ├── milestone1.py
│   ├── table_scene.xml
│   ├── table_scene_v2.xml
│   └── table_scene_bimanual.xml
├── src/champ_tableops/
│   ├── manipulation/
│   │   ├── mujoco_pick_place.py
│   │   └── mujoco_bimanual.py
│   ├── planning/
│   ├── reasoning/
│   │   ├── command_parser.py
│   │   └── openvino_reasoner.py
│   └── verification/
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

## Intel OpenVINO GenAI Setup

Install the optional stack:

```bash
python -m pip install -r requirements-openvino.txt
```

Configure the downloaded OpenVINO model:

```bash
export CHAMP_TABLEOPS_OPENVINO_MODEL="$PWD/models/qwen2.5-1.5b-instruct-int4-ov"
export CHAMP_TABLEOPS_OPENVINO_DEVICE=CPU
```

If `CHAMP_TABLEOPS_OPENVINO_MODEL` is not set, showcase mode will automatically use `models/qwen2.5-1.5b-instruct-int4-ov` when that directory exists.

## Individual Demo Modes

Single-arm deterministic demo:

```bash
python demo/tableops_cli.py --headless --fast "Set the plate."
```

Single-arm Verify → Correct demo:

```bash
python demo/tableops_cli.py --headless --fast --demo-correction "Set the plate."
```

Bimanual deterministic demo:

```bash
python demo/tableops_cli.py \
  --headless --fast \
  --reasoner deterministic \
  "Set the table for two."
```

Bimanual deterministic correction demo:

```bash
python demo/tableops_cli.py \
  --headless --fast \
  --reasoner deterministic \
  --demo-correction \
  "Set the table for two."
```

## Safety Boundary

The AI reasoner does not directly control robot joints. It must emit one of the verified task contracts.

Single place setting:

```json
{"action": "place", "object": "plate", "target": "place_setting_1"}
```

Bimanual two-place setting:

```json
{"action": "set_table", "object": "plates", "target": "place_settings_1_2"}
```

Any other model-produced task is rejected before manipulation begins.

## Roadmap

**Milestone 1 — Complete:** base MuJoCo scene.

**Milestone 2 — Complete:** actuator-driven plate pick-and-place.

**Milestone 3 — Complete:** natural-language command interface.

**Milestone 4 — Complete:** Verify → Correct closed-loop recovery.

**Milestone 5 — Complete:** Intel OpenVINO GenAI reasoning.

**Milestone 6 — Complete:** coordinated two-manipulator / two-place table setting.

**Final Showcase — Current:** presentation hardening, rehearsal, recording, and submission packaging.

**Stretch:** additional table objects, richer perception, and voice input only if the frozen showcase remains stable.

## License

MIT License. See [LICENSE](LICENSE).
