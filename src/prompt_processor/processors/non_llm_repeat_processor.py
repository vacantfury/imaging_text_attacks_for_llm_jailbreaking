"""
Repeat processor - replays the exact processed prompt from a previous experiment.

This processor loads a previous experiment's detailed_results.csv and, for each
input prompt, returns the exact same processed_prompt that was used in that
experiment. This enables controlled "exact repeat" experiments: same processed
prompt → same model → potentially different result (demonstrating non-determinism).

Usage:
    processor = RepeatProcessor(experiment_dir="/path/to/previous/experiment")
    # process() receives the original prompt text and looks up the stored
    # processed_prompt by matching original_prompt text.
"""
import csv
import sys
from pathlib import Path
from typing import Optional, Dict, List

# Some encoded prompts (e.g. quantum mechanics) exceed Python's default 128 KB
# CSV field limit.  Raise it so RepeatProcessor can read any experiment CSV.
csv.field_size_limit(sys.maxsize)

from ..base_processor import BaseProcessor
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RepeatProcessor(BaseProcessor):
    """
    Replay exact processed prompts from a previous experiment.
    
    Loads detailed_results.csv from a given experiment directory and builds
    a lookup table: original_prompt → processed_prompt. When process() is
    called with a prompt, it returns the previously stored processed_prompt
    for that exact prompt text.
    
    This is a rule-based processor (no LLM calls needed).
    """
    
    # No target prefix — the processed prompt already includes whatever
    # prefix was used in the original experiment.
    TARGET_PREFIX = ""
    
    def __init__(self, model=None, experiment_dir: str = "", **kwargs):
        """
        Initialize the repeat processor.
        
        Args:
            model: Optional LLM model (not used by this rule-based processor)
            experiment_dir: Path to the experiment directory containing
                           detailed_results.csv to replay prompts from.
            **kwargs: Additional parameters (for consistency with base class)
        """
        super().__init__(model=model, **kwargs)
        self.experiment_dir = experiment_dir
        self._lookup: Dict[str, str] = {}
        self._id_lookup: Dict[str, str] = {}
        
        if experiment_dir:
            self._load_experiment_data(experiment_dir)
    
    def _load_experiment_data(self, experiment_dir: str):
        """
        Load processed prompts from a previous experiment's CSV.
        
        Builds two lookup tables:
        - By original_prompt text (primary)
        - By id (fallback)
        
        Args:
            experiment_dir: Path to experiment directory
        """
        csv_path = Path(experiment_dir) / "detailed_results.csv"
        
        if not csv_path.exists():
            logger.error(f"CSV not found: {csv_path}")
            return
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                original = row.get('original_prompt', '').strip()
                processed = row.get('processed_prompt', '')
                data_id = row.get('id', '').strip()
                
                if original and processed:
                    self._lookup[original] = processed
                if data_id and processed:
                    self._id_lookup[data_id] = processed
                count += 1
        
        logger.info(
            f"RepeatProcessor loaded {count} prompts from {csv_path} "
            f"({len(self._lookup)} by text, {len(self._id_lookup)} by id)"
        )
    
    def process(self, prompt: str, **kwargs) -> str:
        """
        Return the exact processed prompt from the previous experiment.
        
        Looks up by original_prompt text first, falls back to id if provided
        in kwargs.
        
        Args:
            prompt: The original prompt text to look up
            **kwargs: Optional 'data_id' for fallback lookup
            
        Returns:
            The previously stored processed_prompt, or the raw prompt
            if no match is found.
        """
        # Primary: lookup by original prompt text
        prompt_stripped = prompt.strip()
        if prompt_stripped in self._lookup:
            processed = self._lookup[prompt_stripped]
            return processed + "\n" + processed
        
        # Fallback: lookup by data_id
        data_id = kwargs.get('data_id', '')
        if data_id and data_id in self._id_lookup:
            logger.info(f"RepeatProcessor: matched by id={data_id}")
            processed = self._id_lookup[data_id]
            return processed + "\n" + processed
        
        # No match found
        logger.warning(
            f"RepeatProcessor: no match for prompt "
            f"'{prompt_stripped[:80]}...' — returning raw prompt"
        )
        return prompt
    
    def batch_process(self, prompts: List[str], **kwargs) -> List[str]:
        """
        Process multiple prompts by looking up each one.
        
        Overrides base class to skip rephrase/repeat post-steps since
        we want to return the exact stored processed prompts.
        
        Args:
            prompts: List of original prompts
            **kwargs: Additional parameters
            
        Returns:
            List of previously stored processed prompts
        """
        results = []
        matched = 0
        for prompt in prompts:
            result = self.process(prompt, **kwargs)
            if result != prompt:
                matched += 1
            results.append(result)
        
        logger.info(
            f"RepeatProcessor: matched {matched}/{len(prompts)} prompts"
        )
        return results
