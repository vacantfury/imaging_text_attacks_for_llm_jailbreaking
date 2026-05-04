# Text Encoding

Prompt transformation encoders for jailbreaking experiments.

## Architecture

```
text_encoding/
├── base_encoder.py         # BaseEncoder abstract class
├── encoder_type.py         # EncoderType enum
├── encoder_factory.py      # Registry + create_encoder() factory
├── encoder_config.py       # (unused) typed config dataclass
├── prompt_loader.py        # YAML prompt template loader
└── encoders/               # Concrete implementations
    ├── llm_set_theory_encoder.py
    ├── llm_formal_logic_encoder.py
    ├── llm_quantum_mechanics_encoder.py
    ├── llm_classical_language_encoder.py
    ├── non_llm_baseline_encoder.py
    ├── non_llm_addition_equation_split_reassemble_encoder.py
    ├── non_llm_conditional_probability_encoder.py
    └── non_llm_symbol_injection_encoder.py
```

## Quick Start

```python
from src.text_encoding import create_encoder, EncoderType
from src.llm_utils import LLMModel

# LLM-based encoding (MathPrompt approach)
encoder = create_encoder(
    EncoderType.LLM_SET_THEORY,
    model=LLMModel.GPT_4O
)
encoded_texts = encoder.batch_process(prompts)

# Rule-based encoding
encoder = create_encoder(
    EncoderType.NON_LLM_ADDITION_EQUATION_SPLIT_REASSEMBLE,
    num_parts=6
)
encoded_texts = encoder.batch_process(prompts)
```

## Adding a New Encoder

1. Create a file in `encoders/` (prefix with `llm_` or `non_llm_`)
2. Inherit from `BaseEncoder` and implement `process()`
3. Optionally override `_batch_process_core()` for custom batching
4. Register in `encoder_factory.py`

```python
from src.text_encoding.base_encoder import BaseEncoder

class MyEncoder(BaseEncoder):
    def process(self, prompt: str, **kwargs) -> str:
        return transform(prompt)
```

## Encoder Types

### LLM-based (use an LLM to rewrite prompts)
- `llm_set_theory` — encode as set theory notation
- `llm_formal_logic` — encode as formal logic
- `llm_quantum_mechanics` — encode as quantum mechanics notation
- `llm_classical_language` — rephrase into classical/archaic language

### Rule-based (deterministic transformations)
- `non_llm_baseline` — identity/passthrough
- `non_llm_addition_equation_split_reassemble` — split into math equations
- `non_llm_conditional_probability` — probability notation
- `non_llm_symbol_injection` — inject symbols into text
