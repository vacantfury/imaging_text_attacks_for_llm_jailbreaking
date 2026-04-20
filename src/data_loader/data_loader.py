"""
Unified DataLoader for PTP experiments.
Loads train and test datasets from HuggingFace or local parquet files.
"""
import math
import os
from datasets import load_dataset, concatenate_datasets, Dataset
from typing import Any
import logging

from omegaconf import OmegaConf

from .constants import (
    MAP_FROM_DATASET_NAME_TO_CONSTANTS, 
    MMMU_SUBJECTS,
    QuestionType,
    DATASET_LOADING_SIZE_LIMIT,
)
from ..utils.logger import get_logger
from ..utils.number import is_str_a_number

# Silence verbose HTTP logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("datasets").setLevel(logging.WARNING)

logger = get_logger(__name__)


class DataLoader:
    
    # Build case-insensitive lookup (lowercase key -> original key)
    _name_lookup = {k.lower(): k for k in MAP_FROM_DATASET_NAME_TO_CONSTANTS.keys()}
    
    def __init__(self, config):
        """Initialize DataLoader with a DictConfig or dict.
        
        Args:
            config: Hydra DictConfig or plain dict with data loader settings.
                    Required key: 'name' (dataset name).
                    See conf/data_loader/default.yaml for all supported keys.
        """
        # Accept dict or DictConfig — normalize to DictConfig for attribute access
        if isinstance(config, dict):
            config = OmegaConf.create(config)
        
        self.config = config
        self.train_dataset = None
        self.test_dataset = None
        
        # Case-insensitive name matching
        name_lower = self.config.name.lower()
        if name_lower not in self._name_lookup:
            raise ValueError(f"Unknown dataset: {self.config.name}. Available: {list(MAP_FROM_DATASET_NAME_TO_CONSTANTS.keys())}")
        
        self._canonical_name = self._name_lookup[name_lower]
        self._info = MAP_FROM_DATASET_NAME_TO_CONSTANTS[self._canonical_name]
    
    def _get(self, key: str, default=None):
        """Get value from dataset info with optional default."""
        return self._info.get(key, default)
    
    def _filter_by_image_presence(self, dataset):
        """Filter dataset by image presence based on filter_has_image setting."""
        filter_has_image = self._get("filter_has_image")
        if dataset is None or filter_has_image is None:
            return dataset
        
        image_cols = self._get("image_columns", ["image"])
        keep_with_image = filter_has_image
        
        def has_image(example):
            for col in image_cols:
                if col in example and example[col] is not None:
                    return True
            return False
        
        if keep_with_image:
            # Keep rows WITH image
            filtered = dataset.filter(has_image)
            logger.info(f"Filtered to rows WITH image: {len(dataset)} -> {len(filtered)}")
        else:
            # Keep rows WITHOUT image
            filtered = dataset.filter(lambda x: not has_image(x))
            logger.info(f"Filtered to rows WITHOUT image: {len(dataset)} -> {len(filtered)}")
        
        return filtered
    
    def _check_label_existence_ratio(self, dataset) -> float:
        """Check the ratio of valid (non-empty, non-None, non-'?') labels in a dataset."""
        if dataset is None or len(dataset) == 0:
            return 0.0
        
        label_col = self._get("label_column", self.config.label_column)
        if label_col not in dataset.column_names:
            logger.warning(f"Label column '{label_col}' not found in dataset columns: {dataset.column_names}")
            return 0.0
        
        valid_count = 0
        for item in dataset:
            label_value = item.get(label_col)
            # Check if label is valid (not None, not empty string, not '?')
            if label_value is not None and label_value != '' and label_value != '?':
                valid_count += 1
        
        ratio = valid_count / len(dataset)
        return ratio
    
    def _is_label_a_number(self, label) -> bool:
        """Check if a label is a number (int, float, or numeric string)."""
        if isinstance(label, (int, float)):
            return True
        if isinstance(label, str):
            return is_str_a_number(label)
        return False
    
    def _normalize_label(self, label):
        """Normalize label for comparison. Convert to lowercase string so int/str are equivalent.
        
        Examples: 3 -> "3", "A" -> "a", "Yes" -> "yes"
        """
        return str(label).lower()
    
    def _label_in_valid_set(self, label, valid_set_normalized) -> bool:
        """Check if label is in valid_set. Treats int and str as equivalent (3 == "3")."""
        normalized = self._normalize_label(label)
        return normalized in valid_set_normalized
    
    def _has_choices(self, example, choices_col: str) -> bool:
        """Check if example has valid choices (not None, not empty string, not empty list)."""
        if choices_col not in example:
            return False
        choices = example.get(choices_col)
        if choices is None:
            return False
        if isinstance(choices, str) and choices.strip() == "":
            return False
        if isinstance(choices, list) and len(choices) == 0:
            return False
        return True
    
    def _filter_by_question_type(self, dataset):
        """Filter dataset based on question_type.
        
        Question types:
        - categorical_close_ended: Keep labels matching map keys only.
          If no map defined, keep all rows.
        - constrained: Priority: choices_column > map_from_labels_to_options keys.
          If choices_column defined: keep rows with choices OR numeric label.
          If no choices_column: keep rows matching map keys OR numeric label.
          Numeric labels are always included.
        - open_ended: Reverse of constrained logic.
          Exclude rows that constrained would keep.
        
        If question_type is not defined, no filtering is applied.
        """
        question_type = self._get("question_type")
        if dataset is None or question_type is None:
            return dataset
        
        label_col = self._get("label_column", self.config.label_column)
        choices_col = self._get("choices_column")
        
        if label_col not in dataset.column_names:
            return dataset
        
        original_len = len(dataset)
        
        if question_type == QuestionType.CATEGORICAL_CLOSE_ENDED:
            # Keep labels matching map keys
            label_map = self._get("map_from_labels_to_options")
            if not label_map:  # Empty dict or None means no filtering
                return dataset
            
            # Build flexible set that handles both int and str forms
            filter_set = set()
            for key in label_map.keys():
                filter_set.add(self._normalize_label(key))
                if isinstance(key, int):
                    filter_set.add(str(key))
                elif isinstance(key, str):
                    try:
                        filter_set.add(str(int(key)))
                    except ValueError:
                        pass
            
            def keep_categorical(example):
                label = example.get(label_col)
                return self._label_in_valid_set(label, filter_set)
            
            filtered = dataset.filter(keep_categorical)
            
        elif question_type == QuestionType.CONSTRAINED:
            # Priority: choices_column > map_from_labels_to_options keys
            # In all cases, numeric labels are always included
            if choices_col and choices_col in dataset.column_names:
                # Has choices_column field - filter by choices OR numeric label
                def keep_constrained(example):
                    if self._has_choices(example, choices_col):
                        return True
                    return self._is_label_a_number(example.get(label_col))
                filtered = dataset.filter(keep_constrained)
            else:
                # No choices_column - filter by map keys OR numeric label
                label_map = self._get("map_from_labels_to_options")
                if not label_map:
                    # No map defined - keep only numeric labels
                    def keep_constrained(example):
                        return self._is_label_a_number(example.get(label_col))
                    filtered = dataset.filter(keep_constrained)
                else:
                    # Build flexible set from map keys
                    filter_set = set()
                    for key in label_map.keys():
                        filter_set.add(self._normalize_label(key))
                        if isinstance(key, int):
                            filter_set.add(str(key))
                        elif isinstance(key, str):
                            try:
                                filter_set.add(str(int(key)))
                            except ValueError:
                                pass
                    
                    def keep_constrained(example):
                        label = example.get(label_col)
                        # Map key match OR numeric label
                        if self._label_in_valid_set(label, filter_set):
                            return True
                        return self._is_label_a_number(label)
                    filtered = dataset.filter(keep_constrained)
            
        elif question_type == QuestionType.OPEN_ENDED:
            # Reverse of CONSTRAINED: exclude rows that CONSTRAINED would keep
            # Priority: choices_column > map_from_labels_to_options keys
            if choices_col and choices_col in dataset.column_names:
                # Has choices_column field - exclude rows with choices OR numeric label
                def keep_open_ended(example):
                    if self._has_choices(example, choices_col):
                        return False
                    if self._is_label_a_number(example.get(label_col)):
                        return False
                    return True
                filtered = dataset.filter(keep_open_ended)
            else:
                # No choices_column - exclude rows matching map keys OR numeric label
                label_map = self._get("map_from_labels_to_options")
                if not label_map:
                    # No map defined - exclude only numeric labels
                    def keep_open_ended(example):
                        return not self._is_label_a_number(example.get(label_col))
                    filtered = dataset.filter(keep_open_ended)
                else:
                    # Build flexible set from map keys
                    filter_set = set()
                    for key in label_map.keys():
                        filter_set.add(self._normalize_label(key))
                        if isinstance(key, int):
                            filter_set.add(str(key))
                        elif isinstance(key, str):
                            try:
                                filter_set.add(str(int(key)))
                            except ValueError:
                                pass
                    
                    def keep_open_ended(example):
                        label = example.get(label_col)
                        # Exclude if map key match OR numeric label
                        if self._label_in_valid_set(label, filter_set):
                            return False
                        if self._is_label_a_number(label):
                            return False
                        return True
                    filtered = dataset.filter(keep_open_ended)
            
        else:
            logger.warning(f"Unknown question_type: {question_type}, no filtering applied")
            return dataset
        
        if len(filtered) < original_len:
            logger.info(f"Filtered by question_type={question_type}: {original_len} -> {len(filtered)}")
        
        return filtered
    
    def _transform_labels(self, dataset):
        """Transform labels using map_from_labels_to_options.
        
        Converts original labels to standardized options (e.g., 0 -> 'A', 1 -> 'B').
        Checks both int and str forms when matching keys (e.g., key 0 matches label '0').
        Labels not in the mapping are left unchanged.
        """
        if dataset is None:
            return dataset
        
        label_map = self._get("map_from_labels_to_options")
        if not label_map:  # Empty dict or None means no transformation
            return dataset
        
        label_col = self._get("label_column", self.config.label_column)
        if label_col not in dataset.column_names:
            return dataset
        
        # Build lookup that handles both int and str forms
        # e.g., {0: 'A', '0': 'A', 1: 'B', '1': 'B'}
        flexible_map = {}
        for key, value in label_map.items():
            flexible_map[key] = value
            # Also add str version of int keys and int version of str keys
            if isinstance(key, int):
                flexible_map[str(key)] = value
            elif isinstance(key, str):
                try:
                    flexible_map[int(key)] = value
                except ValueError:
                    pass  # Not a numeric string, skip
        
        def transform_row(example):
            label = example.get(label_col)
            if label in flexible_map:
                return {label_col: str(flexible_map[label])}
            return {label_col: str(label)}  # Always return str to avoid mixed types
        
        original_labels = set(str(x) for x in dataset[label_col][:100])
        dataset = dataset.map(transform_row)
        new_labels = set(str(x) for x in dataset[label_col][:100])
        
        if original_labels != new_labels:
            logger.info(f"Transformed labels: {original_labels} -> {new_labels}")
        
        return dataset
    
    def _transform_text_labels_to_option_letters(self, dataset):
        """Fallback: convert text labels to option letters by matching against choices.
        
        For datasets like MathVista where labels are answer text (e.g., 'mice')
        and choices are ['sun', 'grasshoppers', 'grass', 'mice'], this converts
        the label to 'D' (the matching choice letter).
        
        Only converts if:
        1. choices_column exists and has values
        2. The label text exactly matches one of the choices (case-insensitive)
        3. The label is NOT already an option letter (A/B/C/D/E)
        
        This runs AFTER _transform_labels, so static maps take priority.
        """
        if dataset is None:
            return dataset
        
        choices_col = self._get("choices_column")
        if not choices_col:
            return dataset
        
        label_col = self._get("label_column", self.config.label_column)
        # Use standardized label column name if it was renamed
        if label_col not in dataset.column_names:
            label_col = self.config.label_column
        if label_col not in dataset.column_names or choices_col not in dataset.column_names:
            return dataset
        
        converted_count = 0
        total = len(dataset)
        
        def transform_row(example):
            label = example.get(label_col)
            choices = example.get(choices_col)
            
            if label is None or not choices or not isinstance(choices, list):
                return {label_col: label}
            
            label_str = str(label).strip()
            
            # Skip if already an option letter (A-E) or number
            if len(label_str) == 1 and label_str.upper() in 'ABCDE':
                return {label_col: label}
            
            # Try to match label text against choices
            for i, choice in enumerate(choices):
                if str(choice).strip().lower() == label_str.lower():
                    letter = chr(ord('A') + i)
                    return {label_col: letter}
            
            # No match found — keep original
            return {label_col: label}
        
        # Quick check: if all labels are already option letters or numbers, skip
        sample_labels = [str(x).strip() for x in dataset[label_col][:100]]
        needs_transform = any(
            len(s) != 1 or s.upper() not in 'ABCDE0123456789'
            for s in sample_labels if s
        )
        if not needs_transform:
            return dataset
        
        dataset = dataset.map(transform_row)
        new_labels = set(str(x) for x in dataset[label_col][:100])
        
        logger.info(f"Text-to-letter fallback: {set(sample_labels)} -> {new_labels}")
        
        return dataset
    
    def _add_data_ids(self, dataset, start_id: int = 0):
        """Add sequential data_id column to dataset. IDs are stored as strings."""
        if dataset is None:
            return None, start_id
        
        # Add sequential IDs as strings
        ids = [str(i) for i in range(start_id, start_id + len(dataset))]
        dataset = dataset.add_column(self.config.data_id_column, ids)
        next_id = start_id + len(dataset)
        return dataset, next_id
    
    @staticmethod
    def _format_value(value) -> str:
        """Format a value for text assembly. Handles lists, None, etc."""
        if value is None:
            return ""
        if isinstance(value, list):
            # Format list as numbered options: "A. option1\nB. option2\n..."
            if len(value) == 0:
                return ""
            formatted = []
            for i, item in enumerate(value):
                letter = chr(ord('A') + i)  # A, B, C, D, ...
                formatted.append(f"{letter}. {item}")
            return "\n".join(formatted)
        return str(value)
    
    def _assemble_text(self, dataset):
        """Assemble text from specified columns into assembled_text column.
        
        Format: "column_name1: value1\ncolumn_name2: value2\n..."
        Appends response_label_formatting_str at the end if defined.
        """
        text_cols = self._get("text_columns", [])
        if dataset is None or len(text_cols) == 0:
            return dataset
        
        format_value = self._format_value  # Capture reference for closure
        response_format_str = self._get("response_label_formatting_str", "")
        assembled_text_col = self.config.assembled_text_column  # Capture for closure
        
        def assemble_row(example):
            parts = []
            for col in text_cols:
                if col in example:
                    value = format_value(example[col])
                    if value:  # Only include non-empty values
                        parts.append(f"{col}: {value}")
            
            assembled = "\n".join(parts)
            
            # Append response formatting instruction if defined
            if response_format_str:
                assembled = f"{assembled}\n\n{response_format_str}"
            
            return {assembled_text_col: assembled}
        
        dataset = dataset.map(assemble_row)
        return dataset
    
    def _assemble_images(self, dataset):
        """Assemble images from image_columns into a single 'images' column as a list.
        
        Collects all non-None images from the specified image columns into a list.
        """
        img_cols = self._get("image_columns", ["image"])
        if dataset is None or len(img_cols) == 0:
            return dataset
        
        images_col = self.config.images_column  # Capture for closure
        
        def assemble_row(example):
            images = []
            for col in img_cols:
                if col in example and example[col] is not None:
                    images.append(example[col])
            return {images_col: images}
        
        dataset = dataset.map(assemble_row)
        return dataset
    
    def _standardize_label_column(self, dataset):
        """Standardize the label column name.
        
        Renames the dataset-specific label column (e.g., 'target', 'correct_choice_idx')
        to the standardized config.label_column (default: 'label').
        """
        if dataset is None:
            return dataset
        
        source_col = self._get("label_column", self.config.label_column)
        target_col = self.config.label_column
        
        # Only rename if source and target are different and source exists
        if source_col != target_col and source_col in dataset.column_names:
            dataset = dataset.rename_column(source_col, target_col)
            logger.info(f"Standardized label column: '{source_col}' -> '{target_col}'")
        
        return dataset
    
    def _load_local_split(self, split: str):
        """Load a specific split from local parquet files.
        
        Expects parquet files at: local_path / {split}.parquet
        local_path should be the full path to the dataset directory.
        """
        local_path = self._get("local_path")
        if not local_path:
            raise ValueError(f"local_path not defined for local dataset {self._canonical_name}")
        
        # local_path is the full path to the dataset directory
        parquet_file = os.path.join(local_path, f"{split}.parquet")
        
        if not os.path.exists(parquet_file):
            raise FileNotFoundError(
                f"Local dataset file not found: {parquet_file}\n"
                f"Please run `python -m src.data_loader.special_data_processing` to process the dataset."
            )
        
        # Load from parquet
        dataset = Dataset.from_parquet(parquet_file)
        logger.info(f"Loaded local parquet: {parquet_file} ({len(dataset)} rows)")
        
        return dataset
    
    def _load_split(self, split: str, limit: int = DATASET_LOADING_SIZE_LIMIT):
        """Load a specific split from HuggingFace or local files.
        
        Args:
            split: Dataset split name (e.g., 'train', 'test').
            limit: Max examples to stream. Callers should pass a larger value
                   when post-filtering (e.g., question_type) will reduce the count.
        """
        source = self._get("source", "hugging_face")
        
        if source == "local":
            dataset = self._load_local_split(split)
        else:
            # HuggingFace loading - use streaming to limit download size
            hf_id = self._info["hf_id"]
            subject = self._get("subject")
            subtype = self._get("subtype")
            
            if self._get("is_multi_subject", False):
                all_datasets = []
                per_subject_limit = max(10, limit // len(MMMU_SUBJECTS))
                for subj in MMMU_SUBJECTS:
                    ds = load_dataset(hf_id, subj, split=split, streaming=True)
                    ds = Dataset.from_list(list(ds.take(per_subject_limit)))
                    all_datasets.append(ds)
                dataset = concatenate_datasets(all_datasets)
            elif subject:
                ds = load_dataset(hf_id, subject, split=split, streaming=True)
                dataset = Dataset.from_list(list(ds.take(limit)))
            elif subtype:
                ds = load_dataset(hf_id, subtype, split=split, streaming=True)
                dataset = Dataset.from_list(list(ds.take(limit)))
            else:
                ds = load_dataset(hf_id, split=split, streaming=True)
                dataset = Dataset.from_list(list(ds.take(limit)))
            
            logger.info(f"Loaded {split} (streaming): {len(dataset)} examples")
        
        # Apply image presence filter if configured
        dataset = self._filter_by_image_presence(dataset)
        return dataset
    
    def _load_local(self):
        """Load local dataset - just load train and test parquet files directly."""
        logger.info(f"Loading {self.config.name} (local: {self._get('local_path')})...")
        
        self.train_dataset = self._load_local_split("train")
        self.test_dataset = self._load_local_split("test")
        
        logger.info(f"Loaded train: {len(self.train_dataset)} examples")
        logger.info(f"Loaded test: {len(self.test_dataset)} examples")
        
        # Apply dataset size limits
        seed = self.config.seed
        if self.train_dataset and len(self.train_dataset) > self.config.training_dataset_size_limit:
            self.train_dataset = self.train_dataset.shuffle(seed=seed).select(range(self.config.training_dataset_size_limit))
            logger.info(f"Limited train to {self.config.training_dataset_size_limit} examples")
        if self.test_dataset and len(self.test_dataset) > self.config.test_dataset_size_limit:
            self.test_dataset = self.test_dataset.shuffle(seed=seed).select(range(self.config.test_dataset_size_limit))
            logger.info(f"Limited test to {self.config.test_dataset_size_limit} examples")
        
        # Add sequential data IDs
        self.train_dataset, next_id = self._add_data_ids(self.train_dataset, start_id=0)
        self.test_dataset, _ = self._add_data_ids(self.test_dataset, start_id=next_id)
        logger.info(f"Added {self.config.data_id_column} column")
        
        # Assemble text from specified columns
        text_cols = self._get("text_columns", [])
        if text_cols:
            self.train_dataset = self._assemble_text(self.train_dataset)
            self.test_dataset = self._assemble_text(self.test_dataset)
            logger.info(f"Assembled {self.config.assembled_text_column} from columns: {text_cols}")
        
        # Transform labels using map_from_labels_to_options (before standardizing column name)
        self.train_dataset = self._transform_labels(self.train_dataset)
        self.test_dataset = self._transform_labels(self.test_dataset)
        
        # Fallback: convert text labels to option letters by matching choices
        self.train_dataset = self._transform_text_labels_to_option_letters(self.train_dataset)
        self.test_dataset = self._transform_text_labels_to_option_letters(self.test_dataset)
        
        # Standardize label column name (after transformations)
        self.train_dataset = self._standardize_label_column(self.train_dataset)
        self.test_dataset = self._standardize_label_column(self.test_dataset)
    
    def _load_huggingface(self):
        """Load HuggingFace dataset with filtering and processing."""
        logger.info(f"Loading {self.config.name} (HF: {self._info['hf_id']}, subject: {self._get('subject')})...")
        
        train_split = self._get("train_split", "train")
        test_split = self._get("test_split", "test")
        seed = self.config.seed
        test_ratio = self.config.test_dataset_ratio
        label_ratio_limit = self.config.label_existent_ratio_limit
        
        if train_split == test_split:
            # Same split -> load once, filter by question_type, then split into train/test
            # Need enough examples so that AFTER the split, both train and test meet their limits
            # test_limit / test_ratio gives the total needed to get test_limit in test split

            train_limit = self.config.training_dataset_size_limit
            test_limit = self.config.test_dataset_size_limit
            min_total = max(
                math.ceil(test_limit / test_ratio),
                math.ceil(train_limit / (1 - test_ratio)),
            )
            
            # Apply filter multiplier when any filtering will reduce the count
            question_type = self._get("question_type")
            has_image_filter = self._get("filter_has_image") is not None
            needs_multiplier = question_type or has_image_filter
            multiplier = getattr(self.config, "filter_loading_multiplier", 10) if needs_multiplier else 1
            load_limit = min_total * multiplier
            
            dataset = self._load_split(train_split, limit=load_limit)
            logger.info(f"Loaded {train_split}: {len(dataset)} examples")
            
            # Filter BEFORE split to ensure fair distribution of filtered examples
            dataset = self._filter_by_question_type(dataset)
            if len(dataset) == 0:
                raise ValueError(f"No examples remain after filtering by question_type for {self.config.name}")
            
            split_result = dataset.train_test_split(test_size=test_ratio, seed=seed)
            self.train_dataset = split_result["train"]
            self.test_dataset = split_result["test"]
            logger.info(f"Split into train ({len(self.train_dataset)}) and test ({len(self.test_dataset)})")
        else:
            # Different splits -> load separately, using config limits for streaming
            # Apply multiplier when filtering (question_type or image) will reduce the count
            question_type = self._get("question_type")
            has_image_filter = self._get("filter_has_image") is not None
            needs_multiplier = question_type or has_image_filter
            multiplier = getattr(self.config, "filter_loading_multiplier", 10) if needs_multiplier else 1
            
            train_load_limit = self.config.training_dataset_size_limit * multiplier
            test_load_limit = self.config.test_dataset_size_limit * multiplier
            
            self.train_dataset = self._load_split(train_split, limit=train_load_limit)
            logger.info(f"Loaded train ({train_split}): {len(self.train_dataset)} examples")
            
            self.test_dataset = self._load_split(test_split, limit=test_load_limit)
            logger.info(f"Loaded test ({test_split}): {len(self.test_dataset)} examples")
            
            # Filter after loading for separate splits
            self.train_dataset = self._filter_by_question_type(self.train_dataset)
            self.test_dataset = self._filter_by_question_type(self.test_dataset)
        
        # Check label existence ratio in test dataset
        # If labels are missing/insufficient, resplit from train only (discard unlabeled test)
        if self.test_dataset is not None and self.train_dataset is not None:
            label_ratio = self._check_label_existence_ratio(self.test_dataset)
            logger.info(f"Test label existence ratio: {label_ratio:.2%} (limit: {label_ratio_limit:.0%})")
            
            if label_ratio < label_ratio_limit:
                logger.warning(f"Test labels below threshold ({label_ratio:.2%} < {label_ratio_limit:.0%}), resplitting from train only")
                # Only use train data for resplit (discard unlabeled test data)
                split_result = self.train_dataset.train_test_split(test_size=test_ratio, seed=seed)
                self.train_dataset = split_result["train"]
                self.test_dataset = split_result["test"]
                logger.info(f"Resplit train into train ({len(self.train_dataset)}) and test ({len(self.test_dataset)})")
        
        # Apply dataset size limits (after filtering)
        if self.train_dataset and len(self.train_dataset) > self.config.training_dataset_size_limit:
            self.train_dataset = self.train_dataset.shuffle(seed=seed).select(range(self.config.training_dataset_size_limit))
            logger.info(f"Limited train to {self.config.training_dataset_size_limit} examples")
        if self.test_dataset and len(self.test_dataset) > self.config.test_dataset_size_limit:
            self.test_dataset = self.test_dataset.shuffle(seed=seed).select(range(self.config.test_dataset_size_limit))
            logger.info(f"Limited test to {self.config.test_dataset_size_limit} examples")
        
        # Add sequential data IDs to both train and test (train: 0 to N-1, test: N to N+M-1)
        self.train_dataset, next_id = self._add_data_ids(self.train_dataset, start_id=0)
        self.test_dataset, _ = self._add_data_ids(self.test_dataset, start_id=next_id)
        logger.info(f"Added {self.config.data_id_column} column (train: 0-{next_id-1}, test: {next_id}-{next_id + len(self.test_dataset) - 1})")
        
        # Assemble text from specified columns (with response format instruction if defined)
        text_cols = self._get("text_columns", [])
        if text_cols:
            self.train_dataset = self._assemble_text(self.train_dataset)
            self.test_dataset = self._assemble_text(self.test_dataset)
            response_fmt = self._get("response_label_formatting_str")
            if response_fmt:
                logger.info(f"Assembled {self.config.assembled_text_column} from columns: {text_cols} (+ response format instruction)")
            else:
                logger.info(f"Assembled {self.config.assembled_text_column} from columns: {text_cols}")
        
        # Assemble images from image_columns into a list
        img_cols = self._get("image_columns", ["image"])
        if img_cols:
            self.train_dataset = self._assemble_images(self.train_dataset)
            self.test_dataset = self._assemble_images(self.test_dataset)
            logger.info(f"Assembled {self.config.images_column} from columns: {img_cols}")
        
        # Transform labels using map_from_labels_to_options (before standardizing column name)
        self.train_dataset = self._transform_labels(self.train_dataset)
        self.test_dataset = self._transform_labels(self.test_dataset)
        
        # Fallback: convert text labels to option letters by matching choices
        self.train_dataset = self._transform_text_labels_to_option_letters(self.train_dataset)
        self.test_dataset = self._transform_text_labels_to_option_letters(self.test_dataset)
        
        # Standardize label column name (after transformations)
        self.train_dataset = self._standardize_label_column(self.train_dataset)
        self.test_dataset = self._standardize_label_column(self.test_dataset)
    
    def load(self):
        """Load train and test datasets."""
        source = self._get("source", "hugging_face")
        
        try:
            if source == "local":
                self._load_local()
            else:
                self._load_huggingface()
            
        except Exception as e:
            logger.error(f"Failed to load {self.config.name}: {e}")
            raise
    
    def inspect(self) -> dict[str, Any]:
        """Inspect the dataset schema and show sample examples."""
        if self.test_dataset is None:
            self.load()
        
        # Use test for inspection, fall back to train
        ds = self.test_dataset if self.test_dataset else self.train_dataset
        if ds is None:
            raise ValueError(f"No dataset loaded for {self.config.name}")
        
        num_examples = self.config.num_inspect_examples
        source = self._get("source", "hugging_face")
        
        return {
            "name": self.config.name,
            "source": source,
            "hf_id": self._get("hf_id"),  # None for local datasets
            "local_path": self._get("local_path"),  # None for HF datasets
            "subject": self._get("subject"),
            "question_type": self._get("question_type"),
            "label_column": self._get("label_column"),
            "train_size": len(self.train_dataset) if self.train_dataset else 0,
            "test_size": len(self.test_dataset) if self.test_dataset else 0,
            "columns": list(ds.column_names),
            "features": {k: str(v) for k, v in ds.features.items()},
            "samples": [ds[i] for i in range(min(num_examples, len(ds)))],
        }
    
    def print_inspect(self):
        """Print inspection results in a readable format."""
        info = self.inspect()
        num_examples = self.config.num_inspect_examples
        
        print("\n" + "=" * 60)
        print(f"DATASET: {info['name']}")
        print("=" * 60)
        if info['source'] == "local":
            print(f"Source: local")
            print(f"Local Path: {info['local_path']}")
        else:
            print(f"Source: HuggingFace")
            print(f"HF ID: {info['hf_id']}")
            if info['subject']:
                print(f"Subject: {info['subject']}")
        print(f"Question Type: {info['question_type']}")
        print(f"Label Column: {info['label_column']}")
        print(f"Train Size: {info['train_size']}")
        print(f"Test Size: {info['test_size']}")
        print(f"\nColumns ({len(info['columns'])}):")
        for col in info['columns']:
            print(f"  - {col}: {info['features'].get(col, 'unknown')}")
        
        print(f"\nSample Examples ({num_examples}):")
        for i, sample in enumerate(info['samples']):
            print(f"\n--- Example {i+1} ---")
            for key, value in sample.items():
                # Truncate long values
                val_str = str(value)
                if len(val_str) > 200:
                    val_str = val_str[:200] + "..."
                print(f"  {key}: {val_str}")
        print("\n")


def get_available_datasets() -> list[str]:
    return list(MAP_FROM_DATASET_NAME_TO_CONSTANTS.keys())


def get_mmmu_subjects() -> list[str]:
    return MMMU_SUBJECTS
