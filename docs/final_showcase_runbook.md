# CHAMP TableOps Final Showcase Runbook

This runbook is for the hackathon live demo and backup validation.

## Primary live-demo command

From the repository root with the virtual environment active:

```bash
python demo/tableops_cli.py --showcase
```

Showcase mode fixes the task to:

```text
Set the table for two.
```

It then requires the Intel OpenVINO GenAI reasoner, runs the two-arm MuJoCo scene, injects a 10 cm error into the right-hand placement, verifies the error, corrects it, re-verifies both place settings, and reports success.

If `CHAMP_TABLEOPS_OPENVINO_MODEL` is not set, showcase mode automatically uses this local path when it exists:

```text
models/qwen2.5-1.5b-instruct-int4-ov
```

## Expected proof points

The live output should visibly include:

```text
[TableOps] SHOWCASE MODE: Intel OpenVINO + bimanual + closed-loop recovery
[TableOps] REASONER: openvino_genai
[TableOps] INTEL: OpenVINO GenAI active on CPU
[TableOps] MODE: BIMANUAL / TWO PLACE SETTINGS
[TableOps] VERIFY: left error ...; right error ~0.10 m
[TableOps] CORRECT: right manipulator repositions plate
[TableOps] VERIFY: corrected left error ...; right error ...
[TableOps] VERIFY: both place settings accepted
MILESTONE 6: SUCCESS
CHAMP TABLEOPS SHOWCASE: SUCCESS
```

## Pre-demo validation

Run this before the presentation:

```bash
pytest -v
```

Then validate the entire showcase path without opening the MuJoCo viewer:

```bash
python demo/tableops_cli.py --showcase --headless --fast
```

Only use the visual run after the headless run succeeds.

## Model configuration

If the model is stored elsewhere:

```bash
export CHAMP_TABLEOPS_OPENVINO_MODEL="/path/to/openvino/model"
export CHAMP_TABLEOPS_OPENVINO_DEVICE=CPU
```

Then run:

```bash
python demo/tableops_cli.py --showcase
```

## Fallback demo

If the OpenVINO runtime or model fails immediately before the live presentation, keep the robotics demonstration available with the deterministic reasoner:

```bash
python demo/tableops_cli.py \
  --reasoner deterministic \
  --demo-correction \
  "Set the table for two."
```

That fallback still demonstrates two-arm manipulation, verification, error detection, correction, and re-verification. It should be described accurately as the deterministic fallback rather than the Intel reasoning path.

## Two-minute live-demo narration

A compact narration is:

1. "CHAMP TableOps converts natural language into a verified physical task using Intel OpenVINO GenAI."
2. "The system coordinates two simulated manipulators to set two place settings."
3. "I intentionally inject a ten-centimeter error into the right-hand placement."
4. "The system detects the miss, generates a correction action, repositions the plate, and verifies both targets again."
5. "The final success state demonstrates Perceive, Reason, Plan, Act, Verify, Correct, and Re-Verify in one closed loop."

## Do not change before the presentation

After the final showcase passes, avoid changes to the manipulation controller, scene geometry, OpenVINO prompt contract, or WSLg shutdown handling unless a reproducible blocker is found. Make presentation and documentation changes on top of the frozen known-good behavior.
