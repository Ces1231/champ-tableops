# Milestone 5 — Intel OpenVINO GenAI Reasoning

Milestone 5 puts an Intel OpenVINO GenAI LLM in front of the known-good CHAMP TableOps manipulation controller.

The AI model does **not** control MuJoCo joints directly. It converts natural-language input into the same verified `TaskIntent` contract used by Milestone 3:

```text
Natural language
      ↓
OpenVINO GenAI reasoner
      ↓
{"action":"place","object":"plate","target":"place_setting_1"}
      ↓
Verified CHAMP manipulation controller
      ↓
VERIFY → CORRECT → SUCCESS
```

This separation keeps the robotics demo deterministic and safe while still demonstrating Intel-backed local AI reasoning.

## 1. Install the optional Intel stack

From the repository root with `.venv` active:

```bash
python -m pip install -r requirements-openvino.txt
```

The OpenVINO project documents `openvino-genai` as the PyPI package for GenAI inference.

## 2. Download a small OpenVINO-optimized model

The recommended hackathon model is the Intel/OpenVINO INT4 conversion of Qwen2.5-1.5B-Instruct. It is roughly 1 GB and is already in OpenVINO IR format.

```bash
python - <<'PY'
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="OpenVINO/Qwen2.5-1.5B-Instruct-int4-ov",
    local_dir="models/qwen2.5-1.5b-instruct-int4-ov",
)
PY
```

`models/` is gitignored, so the model will not be committed accidentally.

## 3. Configure TableOps

```bash
export CHAMP_TABLEOPS_OPENVINO_MODEL="$PWD/models/qwen2.5-1.5b-instruct-int4-ov"
export CHAMP_TABLEOPS_OPENVINO_DEVICE=CPU
```

Optional:

```bash
export CHAMP_TABLEOPS_REASONER=openvino
```

The CLI also accepts the same values explicitly through `--reasoner`, `--openvino-model`, and `--openvino-device`.

## 4. Validate OpenVINO reasoning headlessly

```bash
python demo/tableops_cli.py \
  --headless --fast \
  --reasoner openvino \
  "Set the plate."
```

Expected reasoning lines include:

```text
[TableOps] REASONER: openvino_genai
[TableOps] INTEL: OpenVINO GenAI active on CPU
[TableOps] INTENT: place
[TableOps] OBJECT: plate
[TableOps] TARGET: place_setting_1
```

The existing MuJoCo controller should then execute the manipulation and end with:

```text
MILESTONE 5: SUCCESS
```

## 5. Full closed-loop Intel demo

This combines OpenVINO reasoning with the Milestone 4 recovery loop:

```bash
python demo/tableops_cli.py \
  --reasoner openvino \
  --demo-correction \
  "Set the plate."
```

The expected story is:

```text
OpenVINO reason → PLAN → ACT → VERIFY failure → CORRECT → VERIFY → SUCCESS
```

## Reliable fallback mode

The default backend is `auto`.

If `CHAMP_TABLEOPS_OPENVINO_MODEL` is configured, TableOps attempts OpenVINO GenAI first. If OpenVINO cannot initialize or generate a valid task, TableOps falls back to the deterministic Milestone 3 parser and reports that fallback in the terminal.

For the judged Intel demo, use `--reasoner openvino` so a missing or broken Intel runtime fails visibly instead of silently falling back.

## Safety boundary

The LLM can only emit the controller contract currently verified by automated tests:

- action: `place`
- object: `plate`
- target: `place_setting_1`

Any other model-produced task is rejected before robot execution. Two-place/bimanual table setting remains a later milestone.
