import os
from enum import Enum
from src.paths import PROCESSED_DATASETS_DIR


DATASET_LOADING_SIZE_LIMIT = 200


class QuestionType(str, Enum):
    """Question types for dataset classification."""
    CATEGORICAL_CLOSE_ENDED = "categorical_close_ended"
    CONSTRAINED = "constrained"
    OPEN_ENDED = "open_ended"
    RANKING = "ranking"  # Ordered discrete labels (e.g., 0-5 truthfulness scale)
    
# Main dataset registry
# Key: dataset name
# Value: dict with:
#   - hf_id: HuggingFace dataset ID
#   - train_split, test_split: split names to load
#     * If train_split == test_split: load that split and split it into train/test
#     * If different: load them separately
#   - label_column: column name for labels (for checking label existence)
#   - subtype: HuggingFace config/subset name (optional)
#   - image_columns: list of image column names (optional)
#   - filter_has_image: True=keep with image, False=keep without image (optional)
#   - choices_column: column name containing answer choices (optional)
#   - map_from_labels_to_options: dict for label transformation and filtering (optional)
#     * Keys define valid labels for filtering; values define what to transform to
#     * Identity mapping (e.g., {"A": "A"}) means keep label as-is but still use for filtering
#     * Keys can be int or str; matching checks both forms (e.g., key 0 matches label "0" and vice versa)
#     * Empty dict {} means no filtering and no transformation
#   - response_label_formatting_str: instruction for response format, appended to assembled_text (optional)
MAP_FROM_DATASET_NAME_TO_CONSTANTS = {
    "M3CoT": {
        "source": "hugging_face",
        "hf_id": "LightChen2333/M3CoT",
        "train_split": "train",
        "test_split": "test",
        "image_columns": ["image"],
        "text_columns": ["context", "question", "choices"],  # For assembled_text
        "label_column": "answer",
        "choices_column": "choices",
        "question_type": QuestionType.CONSTRAINED,
        "map_from_labels_to_options": {"A": "A", "B": "B", "C": "C", "D": "D"},
        "response_label_formatting_str": "If given options, please answer from the options; if not, please answer with a number. Also you should provide an explanation for your answer.",
    },
    "MathVision_constrained": {
        "source": "hugging_face",
        "hf_id": "MathLLMs/MathVision",
        "train_split": "test",
        "test_split": "test",  # Same -> will split (only test available)
        "image_columns": ["decoded_image"],
        "text_columns": ["question", "options"],  # For assembled_text
        "label_column": "answer",
        "choices_column": "options",
        "question_type": QuestionType.CONSTRAINED,
        "map_from_labels_to_options": {"A": "A", "B": "B", "C": "C", "D": "D", "E": "E"},
        "response_label_formatting_str": "If given options, please answer from the options; if not, please answer with a number. Also you should provide an explanation for your answer.",
    },
    "ScienceQA_text": {
        "source": "hugging_face",
        "hf_id": "derek-thomas/ScienceQA",
        "train_split": "train",
        "test_split": "test",
        "image_columns": ["image"],
        "text_columns": ["hint", "question", "choices"],  # For assembled_text
        "label_column": "answer",
        "choices_column": "choices",
        "filter_has_image": False,  # Keep rows WITHOUT image
        "question_type": QuestionType.CONSTRAINED,
        "map_from_labels_to_options": {0: "A", 1: "B", 2: "C", 3: "D", 4: "E"},
        "response_label_formatting_str": "If given options, please answer from the options; if not, please answer with a number. Also you should provide an explanation for your answer.",
    },
    "ScienceQA_image": {
        "source": "hugging_face",
        "hf_id": "derek-thomas/ScienceQA",
        "train_split": "train",
        "test_split": "test",
        "image_columns": ["image"],
        "text_columns": ["hint", "question", "choices"],  # For assembled_text
        "label_column": "answer",
        "choices_column": "choices",
        "filter_has_image": True,  # Keep rows WITH image
        "question_type": QuestionType.CONSTRAINED,
        "map_from_labels_to_options": {0: "A", 1: "B", 2: "C", 3: "D", 4: "E", 5: "F"},
        "response_label_formatting_str": "If given options, please answer from the options; if not, please answer with a number. Also you should provide an explanation for your answer.",
    },
    "A-OKVQA": {
        "source": "hugging_face",
        "hf_id": "HuggingFaceM4/A-OKVQA",
        "train_split": "train",
        "test_split": "test",
        "image_columns": ["image"],
        "text_columns": ["question", "choices"],  # For assembled_text
        "label_column": "correct_choice_idx",
        "choices_column": "choices",
        "question_type": QuestionType.CONSTRAINED,
        "map_from_labels_to_options": {0: "A", 1: "B", 2: "C", 3: "D"},
        "response_label_formatting_str": "If given options, please answer from the options; if not, please answer with a number. Also you should provide an explanation for your answer.",
    },
    "AI2D": {
        "source": "hugging_face",
        "hf_id": "lmms-lab/ai2d",
        "train_split": "test",
        "test_split": "test",  # Same -> will split (only test available)
        "image_columns": ["image"],
        "text_columns": ["question", "options"],  # For assembled_text
        "label_column": "answer",
        "choices_column": "options",
        "question_type": QuestionType.CONSTRAINED,
        "map_from_labels_to_options": {0: "A", 1: "B", 2: "C", 3: "D"},
        "response_label_formatting_str": "If given options, please answer from the options; if not, please answer with a number. Also you should provide an explanation for your answer.",
    },
    "HellaSwag": {
        "source": "hugging_face",
        "hf_id": "Rowan/hellaswag",
        "train_split": "train",
        "test_split": "test",
        "image_columns": [],  # Text-only
        "text_columns": ["ctx", "endings"],  # For assembled_text
        "label_column": "label",
        "choices_column": "endings",
        "question_type": QuestionType.CONSTRAINED,
        "map_from_labels_to_options": {0: "A", 1: "B", 2: "C", 3: "D"},
        "response_label_formatting_str": "Extend the paragraph by choosing the correct option. Also you should provide an explanation for your answer.",
    },
    "GQA_categorical": {
        "source": "hugging_face",
        "hf_id": "lmms-lab/GQA",
        "subtype": "train_balanced_instructions",
        "train_split": "train",
        "test_split": "train",  # Same -> will split (val has different subtype)
        "image_columns": [],
        "text_columns": ["question"],  # For assembled_text (short-answer VQA, no choices)
        "label_column": "answer",
        "question_type": QuestionType.CATEGORICAL_CLOSE_ENDED,
        "map_from_labels_to_options": {"yes": "yes", "no": "no"},
        "response_label_formatting_str": "Please respond with yes or no, and provide an explanation for your answer.",
    },
    "GQA_open_ended": {
        "source": "hugging_face",
        "hf_id": "lmms-lab/GQA",
        "subtype": "train_balanced_instructions",
        "train_split": "train",
        "test_split": "train",  # Same -> will split (val has different subtype)
        "image_columns": [],
        "text_columns": ["question"],  # For assembled_text (short-answer VQA, no choices)
        "label_column": "fullAnswer", # Label_column is different from GQA_categorical so that data has overlap with it
        "question_type": QuestionType.OPEN_ENDED,
        "map_from_labels_to_options": {"yes": "yes", "no": "no"},  # For filtering, not transformation
        "response_label_formatting_str": "Please respond with a compact answer and provide an explanation for your answer.",
    },
    "MathVista": {
        "source": "hugging_face",
        "hf_id": "AI4Math/MathVista",
        "train_split": "testmini",
        "test_split": "testmini",  # Same -> will split (no train available)
        "image_columns": ["decoded_image"],
        "text_columns": ["question", "choices", "query"],  # For assembled_text (query has format hint)
        "label_column": "answer",
        "choices_column": "choices",  # Can be None for free_form questions
        "question_type": QuestionType.CONSTRAINED,
        "map_from_labels_to_options": {},  # Mixed format - no transformation
        "response_label_formatting_str": "If given options, please answer from the options; if not, please answer with a number. Also you should provide an explanation for your answer.",
    },
    "BBEH_constrained": {
        "source": "hugging_face",
        "hf_id": "BBEH/bbeh",
        "train_split": "train",
        "test_split": "train",  # Same as train -> will split
        "image_columns": [],  # Text-only
        "text_columns": ["input"],  # For assembled_text
        "label_column": "target",
        "question_type": QuestionType.CONSTRAINED,
        "map_from_labels_to_options": {"proved": "proved", "disproved": "disproved", "unknown": "unknown", "(A)": "(A)", "(B)": "(B)", "(C)": "(C)", "(D)": "(D)", "(E)": "(E)"},
        "response_label_formatting_str": "If given options, please answer from the options; if not, please answer proved, disproved, unknown or a number. Also you should provide an explanation for your answer.",
    },
    "BBEH_open_ended": {
        "source": "hugging_face",
        "hf_id": "BBEH/bbeh",
        "train_split": "train",
        "test_split": "train",  # Same as train -> will split
        "image_columns": [],  # Text-only
        "text_columns": ["input"],  # For assembled_text
        "label_column": "target",
        "question_type": QuestionType.OPEN_ENDED,
        "map_from_labels_to_options": {"proved": "proved", "disproved": "disproved", "unknown": "unknown", "(A)": "(A)", "(B)": "(B)", "(C)": "(C)", "(D)": "(D)", "(E)": "(E)"},
        "response_label_formatting_str": "Please respond with a compact answer and provide an explanation for your answer.",
    },
    # ======================new datasets======================
    "MMVet_constrained": {
        "source": "hugging_face",
        "hf_id": "lmms-lab/MMVet",
        "train_split": "test",
        "test_split": "test",  # Same -> will split (only test available, 218 rows)
        "image_columns": ["image"],
        "text_columns": ["question"],
        "label_column": "answer",
        "question_type": QuestionType.CONSTRAINED,
        "map_from_labels_to_options": {'yes': 'yes', 'no': 'no'},
        "response_label_formatting_str": "Please answer with yes or no or a number. Also you should provide an explanation for your answer.",
    },
    "MMVet_open_ended": {
        "source": "hugging_face",
        "hf_id": "lmms-lab/MMVet",
        "train_split": "test",
        "test_split": "test",  # Same -> will split (only test available, 218 rows)
        "image_columns": ["image"],
        "text_columns": ["question"],
        "label_column": "answer",
        "question_type": QuestionType.OPEN_ENDED,
        "response_label_formatting_str": "Please respond with a compact answer and provide an explanation for your answer.",
    },
    "MMVetv2_constrained": {
        "source": "hugging_face",
        "hf_id": "whyu/mm-vet-v2",
        "train_split": "test",
        "test_split": "test",  # Same -> will split (only test available, 517 rows)
        "image_columns": ["image_0", "image_1", "image_2", "image_3", "image_4", "image_5", "image_6", "image_7", "image_8", "image_9", "image_10", "image_11", "image_12", "image_13", "image_14", "image_15", "image_16", "image_17"],
        "text_columns": ["question"],
        "label_column": "answer",
        "question_type": QuestionType.CONSTRAINED,
        "map_from_labels_to_options": {},
        "response_label_formatting_str": "If given options, please answer from the options; if not, please answer with yes or no or a number. Also you should provide an explanation for your answer.",
    },
    "MMVetv2_open_ended": {
        "source": "hugging_face",
        "hf_id": "whyu/mm-vet-v2",
        "train_split": "test",
        "test_split": "test",  # Same -> will split (only test available, 517 rows)
        "image_columns": ["image_0", "image_1", "image_2", "image_3", "image_4", "image_5", "image_6", "image_7", "image_8", "image_9", "image_10", "image_11", "image_12", "image_13", "image_14", "image_15", "image_16", "image_17"],
        "text_columns": ["question"],
        "label_column": "answer",
        "question_type": QuestionType.OPEN_ENDED,
        "response_label_formatting_str": "Please respond with a compact answer and provide an explanation for your answer.",
    },
    "NLVR2": {
        "source": "hugging_face",
        "hf_id": "lmms-lab/NLVR2",  # Alternative with proper image format
        "train_split": "balanced_dev",
        "test_split": "balanced_test_public",
        "image_columns": ["left_image", "right_image"],
        "text_columns": ["question"],
        "label_column": "answer",
        "question_type": QuestionType.CATEGORICAL_CLOSE_ENDED,
        "map_from_labels_to_options": {"True": "True", "False": "False"},
        "response_label_formatting_str": "Please respond with True or False, and provide an explanation for your answer.",
    },
    "GeoBenchVLM": {
        "source": "hugging_face",
        "hf_id": "aialliance/GEOBench-VLM",
        "train_split": "single",
        "test_split": "single",  # Same -> will split (only 'single' split, 3211 rows)
        "image_columns": ["image"],  # PIL Image, not image_path
        "text_columns": ["prompts", "options"],
        "label_column": "ground_truth_option",
        "choices_column": "options",
        "question_type": QuestionType.CONSTRAINED,
        "map_from_labels_to_options": {"A": "A", "B": "B", "C": "C", "D": "D", "E": "E"},
        "response_label_formatting_str": "Please answer choice index, A means first choice and A, B, C, D, E so on. Also you should provide an explanation for your answer.",
    },
    # BLINK base config (use BLINK_<subtype> for specific subtypes)
    "BLINK": {
        "source": "hugging_face",
        "hf_id": "BLINK-Benchmark/BLINK",
        "subtype": "Spatial_Relation",  # Default subset
        "train_split": "val",
        "test_split": "val",
        "image_columns": ["image_1", "image_2", "image_3", "image_4"],
        "text_columns": ["question", "choices"],
        "label_column": "answer",
        "choices_column": "choices",
        "question_type": QuestionType.CONSTRAINED,
        "map_from_labels_to_options": {"(A)": "(A)", "(B)": "(B)", "(C)": "(C)", "(D)": "(D)"},
        "response_label_formatting_str": "Please answer choice index, (A) means first choice and (A), (B), (C), (D) so on. Also you should provide an explanation for your answer.",
    },
    "BLINK_all": {
        "source": "hugging_face",
        "hf_id": "BLINK-Benchmark/BLINK",
        # No subtype -> loads all 14 subtypes combined
        "train_split": "val",
        "test_split": "test",
        "is_multi_subject": True,
        "image_columns": ["image_1", "image_2", "image_3", "image_4"],
        "text_columns": ["question", "choices"],
        "label_column": "answer",
        "choices_column": "choices",
        "question_type": QuestionType.CONSTRAINED,
        "map_from_labels_to_options": {"(A)": "(A)", "(B)": "(B)", "(C)": "(C)", "(D)": "(D)"},
        "response_label_formatting_str": "Please answer choice index, (A) means first choice and (A), (B), (C), (D) so on. Also you should provide an explanation for your answer.",
   },
    "TextVQA": {
        "source": "hugging_face",
        "hf_id": "lmms-lab/textvqa",  # Alternative to deprecated facebook/textvqa
        "train_split": "train",
        "test_split": "validation",
        "image_columns": ["image"],
        "text_columns": ["question"],
        "label_column": "answers",  # List of 10 answers
        "question_type": QuestionType.OPEN_ENDED,
        "response_label_formatting_str": "Please respond with a compact answer and a detailed explanation for your answer.",
    },
    "DocVQA": {
        "source": "hugging_face",
        "hf_id": "lmms-lab/DocVQA",
        "subtype": "DocVQA",  # Explicit subtype (default)
        "train_split": "validation",
        "test_split": "validation",  # test has no labels
        "image_columns": ["image"],
        "text_columns": ["question"],
        "label_column": "answers",  # List of answers
        "question_type": QuestionType.OPEN_ENDED,
        "response_label_formatting_str": "Please respond with a compact answer and a detailed explanation for your answer.",
    },
    "InfographicVQA": {
        "source": "hugging_face",
        "hf_id": "lmms-lab/DocVQA",
        "subtype": "InfographicVQA",  # 6.09k rows total
        "train_split": "validation",
        "test_split": "validation",  # test has no labels (3.29k), validation (2.8k)
        "image_columns": ["image"],
        "text_columns": ["question"],
        "label_column": "answers",  # List of answers
        "question_type": QuestionType.OPEN_ENDED,
        "response_label_formatting_str": "Please respond with a compact answer and a detailed explanation for your answer.",
    },
    "VQAv2": {
        "source": "hugging_face",
        "hf_id": "lmms-lab/VQAv2",  # Alternative to deprecated HuggingFaceM4/VQAv2
        "train_split": "validation",  # No train split available
        "test_split": "testdev",
        "image_columns": ["image"],
        "text_columns": ["question"],
        "label_column": "answers",  # List of answer annotations
        "question_type": QuestionType.OPEN_ENDED,
        "response_label_formatting_str": "Please respond with a compact answer and a detailed explanation for your answer.",
    },
    # =========================PTP/ProTeGi datasets (text-only classification) =================================
    "Liar": {
        "source": "local",
        "local_path": os.path.join(PROCESSED_DATASETS_DIR, "liar"),
        "train_split": "train",
        "test_split": "test",
        "image_columns": [],
        "text_columns": ["statement", "subject", "speaker", "job_title", "state_info", "party_affiliation", "context"],
        "label_column": "label",
        "question_type": QuestionType.RANKING,
        # Ordinal 6-way scale: 0=pants-fire (most false) to 5=true (most true)
        "map_from_labels_to_options": {},  # Keep numeric labels for ranking
        "response_label_formatting_str": "Rate the truthfulness of this political statement from 0 to 5. 0=pants-fire (completely false), 1=false, 2=barely-true, 3=half-true, 4=mostly-true, 5=true. Respond with a number and explanation.",
    },
    "Ethos_binary": {
        "source": "local",
        "local_path": os.path.join(PROCESSED_DATASETS_DIR, "ethos_binary"),
        "train_split": "train",
        "test_split": "test",
        "image_columns": [],
        "text_columns": ["text"],
        "label_column": "label",
        "question_type": QuestionType.RANKING,
        # Continuous score 0.0-1.0 (aggregated annotator agreement)
        "label_range": (0.0, 1.0),
        "map_from_labels_to_options": {},  # Keep continuous labels
        "response_label_formatting_str": "Rate how likely this text is hate speech from 0.0 to 1.0. 0.0=definitely not hate speech, 1.0=definitely hate speech. Respond with a decimal number and explanation.",
    },
    "ArSarcasm": {
        "source": "local",
        "local_path": os.path.join(PROCESSED_DATASETS_DIR, "arsarcasm"),
        "train_split": "train",
        "test_split": "test",
        "image_columns": [],
        "text_columns": ["tweet"],
        "label_column": "sarcasm",
        "question_type": QuestionType.CATEGORICAL_CLOSE_ENDED,
        "map_from_labels_to_options": {0: 0, 1: 1},
        "response_label_formatting_str": "Answer with 0 (not sarcastic) or 1 (sarcastic). Provide an explanation.",
    },
    # =========================datasets that are irrelevant or diffcult to use and not yet well processed =====================     
    # TabFact needs to specially downloaded from web and processed
    "TabFact": {
        "hf_id": "wenhu/tab_fact",
        "train_split": "train",
        "test_split": "test",
        "image_columns": [],  # Text-only (table + statement)
        "text_columns": ["table", "statement"],
        "label_column": "label",
        "map_from_labels_to_options": {0: "refuted", 1: "entailed"},
        "response_label_formatting_str": "Determine if the statement is refuted or entailed by the table. Provide an explanation.",
    },
    # VSR image needs to specially downloaded from coco2017 and processed
    "VSR": {
        "hf_id": "juletxara/visual-spatial-reasoning",
        "train_split": "train",
        "test_split": "test",
        "image_columns": ["image"],
        "text_columns": ["caption"],
        "label_column": "label",
        "map_from_labels_to_options": {True: "True", False: "False"},
        "response_label_formatting_str": "Please respond with True or False, and provide an explanation for your answer.",
    },
    # Object recognition and counting with little reasoning
    "CLEVR_4": {
        "hf_id": "dali-does/clevr-math",
        "subtype": "general",
        "train_split": "train",
        "test_split": "validation",
        "image_columns": ["image"],
        "text_columns": ["question"],
        "label_column": "label",  # Integer answer
        # Synthetic compositional reasoning
    },
    # Ethos_multilabel has many label columns
    "Ethos_multilabel": {
        "source": "local",
        "local_path": os.path.join(PROCESSED_DATASETS_DIR, "ethos_multilabel"),
        "train_split": "train",
        "test_split": "test",
        "image_columns": [],
        "text_columns": ["text"],
        "label_column": "violence",  # Primary label; also has: directed_vs_generalised, gender, race, national_origin, disability, religion, sexual_orientation
        "question_type": QuestionType.RANKING,
        # Continuous score 0.0-1.0
        "label_range": (0.0, 1.0),
        "response_label_formatting_str": "Rate how likely this hate speech incites violence from 0.0 to 1.0. 0.0=no violence, 1.0=incites violence. Respond with a decimal number and explanation.",
    },
    # TallyQA is about object counting
    "TallyQA": {
        "hf_id": "manoja328/tallyqa",
        "train_split": "train",
        "test_split": "test",
        "image_columns": [],
        "text_columns": ["question"],
        "label_column": "answer",
    },
    # ======================datasets that should not be used======================
    # scienceqa should use text or image version
    "ScienceQA": {
        "hf_id": "derek-thomas/ScienceQA",
        "train_split": "train",
        "test_split": "test",
        "image_columns": ["image"],
        "text_columns": ["hint", "question", "choices"],  # For assembled_text
        "label_column": "answer",
        "choices_column": "choices",
        "map_from_labels_to_options": {0: "A", 1: "B", 2: "C", 3: "D"},
        "response_label_formatting_str": "If given options, please answer from the options; if not, please answer with a number. Also you should provide an explanation for your answer.",
    },
    # MMMU labeled data rows too few (test has answer='?')
    "MMMU": {
        "hf_id": "MMMU/MMMU",
        "train_split": "validation",
        "test_split": "validation",  # Same -> will split (test has no labels)
        "is_multi_subject": True,
        "image_columns": ["image_1", "image_2", "image_3", "image_4", "image_5", "image_6", "image_7"],
        "text_columns": ["question", "options"],  # For assembled_text
        "label_column": "answer",
        "choices_column": "options",
        "map_from_labels_to_options": {"A": "A", "B": "B", "C": "C", "D": "D"},
        "response_label_formatting_str": "If given options, please answer from the options; if not, please answer with a number. Also you should provide an explanation for your answer.",
    },
    "MMMU_all": {
        "hf_id": "MMMU/MMMU",
        "train_split": "validation",
        "test_split": "validation",  # Same -> will split
        "is_multi_subject": True,
        "image_columns": ["image_1", "image_2", "image_3", "image_4", "image_5", "image_6", "image_7"],
        "text_columns": ["question", "options"],  # For assembled_text
        "label_column": "answer",
        "choices_column": "options",
        "map_from_labels_to_options": {"A": "A", "B": "B", "C": "C", "D": "D"},
        "response_label_formatting_str": "If given options, please answer from the options; if not, please answer with a number. Also you should provide an explanation for your answer.",
    },
}

# MMMU subjects
MMMU_SUBJECTS = [
    "Accounting", "Agriculture", "Architecture_and_Engineering", "Art",
    "Art_Theory", "Basic_Medical_Science", "Biology", "Chemistry",
    "Clinical_Medicine", "Computer_Science", "Design", "Diagnostics_and_Laboratory_Medicine",
    "Economics", "Electronics", "Energy_and_Power", "Finance", "Geography",
    "History", "Literature", "Manage", "Marketing", "Materials", "Math",
    "Mechanical_Engineering", "Music", "Pharmacy", "Physics", "Psychology",  
    "Public_Health", "Sociology",
]

# Dynamically add MMMU_<Subject> entries (lowercase key for case-insensitivity)
for subject in MMMU_SUBJECTS:
    MAP_FROM_DATASET_NAME_TO_CONSTANTS[f"mmmu_{subject.lower()}"] = {
        "hf_id": "MMMU/MMMU",
        "train_split": "validation",
        "test_split": "validation",  # Same -> will split (test has no labels)
        "subtype": subject,  # Keep original case for HF API
        "image_columns": ["image_1", "image_2", "image_3", "image_4", "image_5", "image_6", "image_7"],
        "text_columns": ["question", "options"],  # For assembled_text
        "label_column": "answer",
        "choices_column": "options",
        "map_from_labels_to_options": {"A": "A", "B": "B", "C": "C", "D": "D"},
        "response_label_formatting_str": "If given options, please answer from the options; if not, please answer with a number. Also you should provide an explanation for your answer.",
    }

# BLINK subtypes (14 visual perception tasks)
BLINK_SUBTYPES = [
    "Art_Style",
    "Counting",
    "Forensic_Detection",
    "Functional_Correspondence",
    "IQ_Test",
    "Jigsaw",
    "Multi-view_Reasoning",
    "Object_Localization",
    "Relative_Depth",
    "Relative_Reflectance",
    "Semantic_Correspondence",
    "Spatial_Relation",
    "Visual_Correspondence",
    "Visual_Similarity",
]

# Dynamically add BLINK_<Subtype> entries (lowercase key for case-insensitivity)
for subtype in BLINK_SUBTYPES:
    MAP_FROM_DATASET_NAME_TO_CONSTANTS[f"blink_{subtype.lower()}"] = {
        "hf_id": "BLINK-Benchmark/BLINK",
        "train_split": "val",
        "test_split": "test",
        "subtype": subtype,  # Keep original case for HF API
        "image_columns": ["image_1", "image_2", "image_3", "image_4"],
        "text_columns": ["question", "choices"],
        "label_column": "answer",
        "choices_column": "choices",
        "map_from_labels_to_options": {"(A)": "(A)", "(B)": "(B)", "(C)": "(C)", "(D)": "(D)"},
        "response_label_formatting_str": "If given options, please answer from the options; if not, please answer with a number. Also you should provide an explanation for your answer.",
    }
