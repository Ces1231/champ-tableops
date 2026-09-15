# CHAMP TableOps

**Voice-Guided Physical AI for Bimanual Table Setting**

CHAMP TableOps is a hackathon prototype for the **AI Infra Summit Hackathon 2026**.

The system is designed around a closed-loop Physical AI workflow:

**Perceive → Reason → Plan → Act → Verify → Correct**

The initial demo target is autonomous table setting in simulation using robotic manipulation, multimodal reasoning, and optional real-time voice interaction.

## Current Hackathon Status

**Milestone 2 is working in automated CI:** an actuated MuJoCo manipulator approaches a plate, aligns with it, closes its gripper, lifts the plate, transfers it to a target place setting, releases it, retreats, and verifies the final placement.

Unlike the original Milestone 1 proof of concept, the Milestone 2 controller does **not** rewrite the plate free-joint position to move it. Cartesian robot motion is generated through MuJoCo position actuators. Once the gripper is aligned and closed, a temporary MuJoCo equality constraint models a stable grasp; the constraint is released at placement.

Current demo loop:

**Perceive → Plan → Approach → Grasp → Lift → Transfer → Place → Release → Verify**

## Objectives

- Observe a simulated tabletop scene.
- Identify plates, cups, utensils, napkins, and other task objects.
- Convert natural-language or spoken instructions into structured tasks.
- Plan a sequence of manipulation actions.
- Coordinate two simulated robot arms.
- Verify that the resulting scene satisfies the requested task.
- Correct failed or incomplete placements.

## Stack

- Python 3.11+
- MuJoCo 3.3+
- Intel OpenVINO / Intel Physical AI tooling as required by the challenge
- Multimodal/VLA model selected from official challenge resources
- Speechmatics for optional speech-to-text
- Pytest for validation
- Docker for reproducible execution

> Final Intel models, SDKs, and starter repositories should be pinned only after the official track brief is confirmed.

## Repository Layout

```text
champ-tableops/
├── .github/workflows/
├── assets/
├── demo/
├── docker/
├── docs/
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
│   ├── verification/
│   └── voice/
└── tests/
```

## Quick Start

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pytest
```

### Linux / WSL / macOS

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pytest
```

## Milestone 2 Demo

From the repository root, launch the visual MuJoCo demo:

```bash
python simulation/demo_pick_place.py
```

The demo executes the command concept:

> **"Set the plate."**

For a fast headless validation run:

```bash
python simulation/demo_pick_place.py --headless --fast
```

Expected final output includes:

```text
[TableOps] VERIFY: measure final placement
[TableOps] SUCCESS
MILESTONE 2: SUCCESS
```

The automated equivalent is covered by:

```bash
pytest tests/test_milestone2_pick_place.py -v
```

## Milestone Roadmap

**Milestone 1 — Complete:** load MuJoCo scene and programmatically validate movement of one table object.

**Milestone 2 — Complete in CI / pending local visual confirmation:** actuated manipulator performs one plate pick-and-place and verifies final placement.

**Milestone 3 — Next:** connect natural-language task input to the manipulation controller, then add additional table objects.

**Milestone 4 — Stretch:** multimodal perception, second manipulator, voice input, and Verify → Correct recovery behavior.

## Target Demo Scenario

Example command:

> "Set the table for two."

Target workflow:

1. Perception detects available objects and their locations.
2. Reasoning interprets the desired final scene.
3. Planning generates ordered manipulation tasks.
4. Manipulation executes pick-and-place actions.
5. Verification checks the resulting scene.
6. Correction retries or repairs failed placements.

## License

MIT License. See [LICENSE](LICENSE).
