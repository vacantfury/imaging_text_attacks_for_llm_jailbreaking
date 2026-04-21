# Project Structure: Encoding × Modality Jailbreaking Study

## Design Principles

1. **Preserve existing structure** — Adapt `src/` modules from PTP/jailbreak projects, don't rebuild
2. **Minimal changes** — Only rename/add/delete what's necessary for this project
3. **Hydra configs** — Experimental conditions defined by config

---

## Directory Layout

```
project_root/
│
├── conf/                          # Hydra configs (adapt for this project)
│   ├── config.yaml
│   ├── model/
│   │   ├── gpt4o.yaml
│   │   ├── gemini25.yaml
│   │   ├── claude_sonnet4.yaml
│   │   └── llava_next.yaml
│   └── encoding/
│       ├── plain_english.yaml
│       ├── classical_chinese.yaml
│       └── math_encoding.yaml
│
├── data/                          # Source data only (git tracked)
│   ├── harmful_prompts.jsonl      # 150 harmful prompts
│   └── benign_prompts.jsonl       # 50 benign controls
│
├── src/
│   ├── paths.py                   # Adapt paths for this project
│   ├── llm_utils/                 # KEEP — low-level API calls (OpenAI, Claude, Google)
│   ├── text_encoding/             # RENAMED — encodes prompts (plain/CC/math)
│   ├── imaging/                   # NEW — renders text → image
│   ├── experiment/                # ADAPT
│   │   ├── experiment.py          #   orchestrator: manages task list across conditions
│   │   └── task.py                #   executor: sends prompts to model, collects responses,
│   │                              #     calls evaluation/ for judging (mode dispatch)
│   ├── evaluation/                # ADAPT — ASR judging (GPT-4o judge + Llama Guard)
│   ├── data_loader/               # ADAPT — loads harmful/benign JSONL
│   └── utils/                     # KEEP — logger, multiprocessing, etc.
│
├── scripts/                       # Utility scripts & commands (keep style)
├── outputs/                       # Raw outputs (gitignored)
├── results/                       # Curated results (tracked)
├── text_docs/                     # Planning docs
├── main.py                        # Entry point: python main.py
├── pyproject.toml
├── TODO.md
└── .gitignore
```

---

## Changes from Current State

| Module | Action | What changes |
|--------|--------|-------------|
| `src/llm_utils/` | **KEEP** | Nothing |
| `src/prompt_processor/` | **RENAME → `text_encoding/`** | Rename files/classes (see migration table below), add `ClassicalChineseEncoder`, delete unused PTP processors |
| `src/imaging/` | **NEW** | `image_renderer.py` — Pillow text→base64 image |
| `src/experiment/` | **ADAPT** | Modify for 3×2 matrix conditions (existing: experiment.py, task.py; delete config.py — old version) |
| `src/evaluation/` | **ADAPT** | Add ASR judge (GPT-4o + Llama Guard protocol) |
| `src/data_loader/` | **ADAPT** | Load harmful/benign JSONL datasets |
| `src/utils/` | **KEEP** | Logger, multiprocessing utilities |
| `src/prompt_optimization/` | **DELETE** | PTP-specific |

---

## Task Modes

The existing `task.py` uses a **mode-based dispatch** pattern (`run_task(config)` → checks `config.mode` → runs appropriate code path). We adapt this with three modes:

```
mode: "text_encode" → Encode all prompts with specified encoding → outputs/
mode: "imaging"     → Render encoded prompts as images → data/images/
mode: "evaluate"  → Query model + judge responses → outputs/
```

### Execution

```bash
python main.py              # reads conf/experiment/default.yaml
python main.py -e encode_cc # reads conf/experiment/encode_cc.yaml
```

Always reads an experiment YAML with a `tasks:` list (a single task is just a list of one).

**conf/experiment/encode_cc.yaml:**
```yaml
tasks:
  - mode: text_encode
    encoding: classical_chinese
```

**conf/experiment/eval_gpt4o.yaml:**
```yaml
tasks:
  - mode: evaluate
    model: gpt4o
    encoding: classical_chinese
    modality: text
    source_dir: outputs/encode_classical_chinese_v1/
  - mode: evaluate
    model: gpt4o
    encoding: classical_chinese
    modality: image
    source_dir: outputs/image_classical_chinese_v1/
```

**conf/experiment/full.yaml** — all 24 conditions in one file.

### Why separate modes

- **text_encode** runs once per encoding type, reusable across all models
- **image** runs once per encoding type, same images sent to all models (controlled experiment)
- **evaluate** is the expensive API step — can be rerun independently
- **`source_dir`** lets you choose which version of encoded/image data to use (different settings produce different outputs)

---

## Data Schema (`data_loader/schemas.py`)

Pydantic models define the contract between stages. Both task.py (writer) and data_loader (reader) import from the same schemas — single source of truth.

```python
class RawPrompt(BaseModel):
    id: str
    category: str
    source: str           # "advbench" | "harmbench" | "jailbreakbench"
    prompt: str

class EncodedPrompt(BaseModel):
    id: str
    encoding: str         # "plain_english" | "classical_chinese" | "math_encoding"
    original: str
    encoded: str

class ImagePrompt(BaseModel):
    id: str
    encoding: str
    image_path: str       # relative path to PNG within output dir

class ModelResponse(BaseModel):
    id: str
    model: str
    encoding: str
    modality: str         # "text" | "image"
    response: str
    timestamp: str

class Judgment(BaseModel):
    id: str
    model: str
    encoding: str
    modality: str
    gpt4o_judge: bool
    llamaguard_judge: bool
    asr: bool             # final ASR decision
```

Write: `prompt.model_dump_json()` → JSONL line
Read: `EncodedPrompt.model_validate_json(line)` → validated object

---

## Migration: `prompt_processor/` → `text_encoding/`

### File Renaming

| Old (prompt_processor/) | New (text_encoding/) | Class Rename |
|---|---|---|
| `base_processor.py` | `base_encoder.py` | `BaseProcessor` → `BaseEncoder` |
| `processor_type.py` | `encoder_type.py` | `ProcessorType` → `EncoderType` |
| `processor_factory.py` | `encoder_factory.py` | `ProcessorFactory` → `EncoderFactory` |
| `processor_config.py` | `encoder_config.py` | `ProcessorConfig` → `EncoderConfig` |
| `processors/` | `encoders/` | — |
| `processors/non_llm_baseline_processor.py` | `encoders/plain_encoder.py` | → `PlainEncoder` |
| `processors/llm_set_theory_processor.py` | `encoders/math_encoder.py` | → `MathEncoder` |
| `processors/llm_formal_logic_processor.py` | `encoders/formal_logic_encoder.py` | → `FormalLogicEncoder` |
| `processors/constants.py` | `encoders/constants.py` | — |
| — (NEW) | `encoders/classical_chinese_encoder.py` | `ClassicalChineseEncoder` |

### Method Renaming

| Old | New |
|---|---|
| `process(prompt)` | `encode(prompt)` |
| `batch_process(prompts)` | `batch_encode(prompts)` |

### Files to Delete (not in our encoding matrix)

- `processors/llm_rephrase_processor.py`
- `processors/llm_markov_chain_processor.py`
- `processors/llm_quantum_mechanics_processor.py`
- `processors/non_llm_addition_equation_split_reassemble_processor.py`
- `processors/non_llm_conditional_probability_processor.py`
- `processors/non_llm_symbol_injection_processor.py`
- `processors/non_llm_repeat_processor.py`
