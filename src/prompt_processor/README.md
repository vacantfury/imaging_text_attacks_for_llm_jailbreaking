# Prompt Processor - Clean Strategy Pattern Design

## Architecture

**Simple and extensible design with just 3 components:**

```
1. PromptProcessor         (ONE unified processor class)
2. BaseProcessingStrategy  (abstract base for strategies)
3. Concrete Strategies     (DirectLLMStrategy, SplitReassembleStrategy, etc.)
```

No separate LLM/NonLLM processors needed! The distinction is in the **strategies**, not the processor.

## Quick Start

### LLM-Based Processing

```python
from src.prompt_processor import PromptProcessor
from src.llm_utils import LLMModel

# Direct prompting
processor = PromptProcessor(
    strategy='direct',
    model=LLMModel.GPT_4,
    input_file="prompts.jsonl",
    output_file="responses.jsonl"
)
processor.process_and_save()

# Few-shot prompting (with example)
processor = PromptProcessor(
    strategy='few_shot',
    model=LLMModel.GPT_4
)
response = processor.process_prompt("Explain recursion")
```

### Rule-Based Processing

```python
from src.prompt_processor import PromptProcessor

# Split and reassemble
processor = PromptProcessor(
    strategy='split_reassemble',
    num_parts=6,
    input_file="harmful.jsonl",
    output_file="obfuscated.jsonl"
)
processor.process_and_save()

# Conditional probability
processor = PromptProcessor(
    strategy='conditional_probability',
    num_parts=5
)
result = processor.process_prompt("How to secure a network")
```

## Built-in Strategies

### LLM Strategies
- **`direct`**: Direct prompting (no modifications)
- **`few_shot`**: With example for few-shot learning

### Rule-Based Strategies
- **`split_reassemble`**: Mathematical summation notation
- **`conditional_probability`**: Probability equation format

## Adding a New Strategy

Just create a new strategy class and register it:

```python
from src.prompt_processor import BaseProcessingStrategy, register_strategy

class MyCustomStrategy(BaseProcessingStrategy):
    """My custom transformation strategy."""
    
    def __init__(self, my_param: int = 10):
        self.my_param = my_param
    
    def process(self, prompt: str, **kwargs) -> str:
        """Transform the prompt."""
        return f"Custom[{self.my_param}]: {prompt}"
    
    # Optional: for efficient batch processing
    def supports_batch_processing(self) -> bool:
        return False  # True if you implement batch_process()

# Register it
register_strategy('my_custom', MyCustomStrategy)

# Use it
processor = PromptProcessor(strategy='my_custom', my_param=20)
```

That's it! No need to modify PromptProcessor or any other files.

## Key Features

### 1. Single Processor Class
- ONE `PromptProcessor` for all use cases
- Handles I/O, batching, parallelization
- Delegates processing to strategies

### 2. Strategy Pattern
- Easy to add new strategies (just inherit and register)
- No enums needed (string-based registry)
- Can mix LLM and non-LLM strategies

### 3. Automatic Optimization
- LLM strategies: Use native batch APIs
- Rule-based strategies: Automatic parallel processing (10+ prompts)
- Small batches: Sequential processing (fast enough)

### 4. Flexible Creation
```python
# By name (with parameters)
processor = PromptProcessor(strategy='direct', model=LLMModel.GPT_4)

# Using factory
from src.prompt_processor import create_strategy
strategy = create_strategy('split_reassemble', num_parts=8)
processor = PromptProcessor(strategy=strategy)

# Custom instance
strategy = MyCustomStrategy(my_param=20)
processor = PromptProcessor(strategy=strategy)
```

## File Structure

```
prompt_processor/
├── __init__.py                # Exports
├── prompt_processor.py        # PromptProcessor class (orchestration & I/O)
├── processing_strategies.py   # All strategies (base + concrete)
├── constants.py              # Shared constants
└── README.md                 # This file
```

**That's it! Just 4 files total.** 🎯

## Benefits

✅ **Simple**: One processor class, strategies are plugins  
✅ **Extensible**: Add strategies without modifying existing code  
✅ **Clean**: No LLM/NonLLM split in processor hierarchy  
✅ **Flexible**: Strategies can be LLM-based, rule-based, or hybrid  
✅ **Efficient**: Automatic optimization (batch, parallel)  
✅ **No boilerplate**: No enums, no factory classes  

## Examples

### Batch Processing
```python
processor = PromptProcessor(strategy='direct', model=LLMModel.GPT_4)

# Process list directly
prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
responses = processor.batch_process(prompts)

# Process from file
processor.process_and_save()
```

### Custom Parameters
```python
# Rule-based with custom num_parts
processor = PromptProcessor(strategy='split_reassemble', num_parts=8)

# LLM with custom temperature
processor = PromptProcessor(
    strategy='direct',
    model=LLMModel.GPT_4,
    temperature=0.3,
    max_tokens=1000
)
```

### List Available Strategies
```python
from src.prompt_processor import list_strategies

print(list_strategies())
# ['direct', 'few_shot', 'split_reassemble', 'conditional_probability']
```

## Migration from Old Design

**Old**:
```python
from src.prompt_processor import LLMProcessor, NonLLMProcessor

llm = LLMProcessor(model=GPT_4, use_example=True)
non_llm = NonLLMProcessor(mode=1, num_parts=6)
```

**New**:
```python
from src.prompt_processor import PromptProcessor

llm = PromptProcessor(strategy='few_shot', model=GPT_4)
non_llm = PromptProcessor(strategy='split_reassemble', num_parts=6)
```

Much cleaner! Same functionality, simpler API. ✨
