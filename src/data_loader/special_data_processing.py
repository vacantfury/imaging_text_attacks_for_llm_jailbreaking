"""
Special data processing for local datasets.
Processes raw datasets from original_datasets/ into standardized parquet format in processed_datasets/.

Output: train.parquet and test.parquet for each dataset (no validation split)
"""

import os
import sys
import pandas as pd
from sklearn.model_selection import train_test_split

# Handle imports for both module and direct execution
try:
    from src.paths import RAW_DATASETS_DIR, PROCESSED_DATASETS_DIR
except ImportError:
    # Direct execution - compute paths manually
    _THIS_DIR = os.path.dirname(os.path.abspath(__file__))
    _PROJECT_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))
    sys.path.insert(0, _PROJECT_ROOT)
    from src.paths import RAW_DATASETS_DIR, PROCESSED_DATASETS_DIR

# Default split ratio and seed
DEFAULT_TEST_RATIO = 0.2
DEFAULT_SEED = 42


def verify_labels(df: pd.DataFrame, label_column: str, dataset_name: str) -> bool:
    """Verify that the dataset has valid labels.
    
    Returns True if labels are valid, False otherwise.
    """
    if label_column not in df.columns:
        print(f"  ERROR: Label column '{label_column}' not found in {dataset_name}")
        return False
    
    # Check for missing/empty labels
    missing = df[label_column].isna().sum()
    empty = (df[label_column] == "").sum() if df[label_column].dtype == object else 0
    total = len(df)
    valid = total - missing - empty
    
    print(f"  Labels: {valid}/{total} valid ({missing} missing, {empty} empty)")
    
    if valid == 0:
        print(f"  ERROR: No valid labels in {dataset_name}")
        return False
    
    # Show label distribution
    label_counts = df[label_column].value_counts()
    print(f"  Distribution: {dict(label_counts)}")
    
    return True


def split_and_save(df: pd.DataFrame, output_dir: str, label_col: str, 
                   test_ratio: float = DEFAULT_TEST_RATIO, seed: int = DEFAULT_SEED):
    """Split dataframe into train/test and save as parquet."""
    train_df, test_df = train_test_split(
        df, test_size=test_ratio, random_state=seed, stratify=df[label_col]
    )
    
    train_df.to_parquet(os.path.join(output_dir, "train.parquet"), index=False)
    test_df.to_parquet(os.path.join(output_dir, "test.parquet"), index=False)
    
    print(f"  Saved train.parquet ({len(train_df)} rows), test.parquet ({len(test_df)} rows)")


def process_liar():
    """Process LIAR dataset from TSV to parquet.
    
    Combines train + valid -> train, keeps test separate.
    """
    print("\nProcessing LIAR dataset...")
    
    input_dir = os.path.join(RAW_DATASETS_DIR, "liar")
    output_dir = os.path.join(PROCESSED_DATASETS_DIR, "liar")
    os.makedirs(output_dir, exist_ok=True)
    
    # Column names based on README
    columns = [
        "id", "label", "statement", "subject", "speaker", "job_title", 
        "state_info", "party_affiliation", 
        "barely_true_count", "false_count", "half_true_count", 
        "mostly_true_count", "pants_fire_count", "context"
    ]
    
    # Label mapping: text labels to integers (0-5 ordinal scale)
    # 0 = most false (pants-fire), 5 = most true (true)
    label_map = {
        "pants-fire": 0,
        "false": 1, 
        "barely-true": 2,
        "half-true": 3,
        "mostly-true": 4,
        "true": 5
    }
    
    # Load all splits
    dfs = {}
    for split in ["train", "valid", "test"]:
        input_file = os.path.join(input_dir, f"{split}.tsv")
        if not os.path.exists(input_file):
            print(f"  Warning: {input_file} not found, skipping")
            continue
        
        df = pd.read_csv(input_file, sep="\t", header=None, names=columns, dtype=str)
        df["label"] = df["label"].map(label_map)
        df = df.fillna("")
        dfs[split] = df
        print(f"  Loaded {split}: {len(df)} rows")
    
    if not dfs:
        print("  ERROR: No data loaded")
        return False
    
    # Combine train + valid -> train
    train_dfs = []
    if "train" in dfs:
        train_dfs.append(dfs["train"])
    if "valid" in dfs:
        train_dfs.append(dfs["valid"])
    
    if train_dfs:
        train_df = pd.concat(train_dfs, ignore_index=True)
        if not verify_labels(train_df, "label", "liar/train"):
            return False
        output_file = os.path.join(output_dir, "train.parquet")
        train_df.to_parquet(output_file, index=False)
        print(f"  Saved train.parquet ({len(train_df)} rows = train + valid)")
    
    # Save test separately
    if "test" in dfs:
        test_df = dfs["test"]
        if not verify_labels(test_df, "label", "liar/test"):
            return False
        output_file = os.path.join(output_dir, "test.parquet")
        test_df.to_parquet(output_file, index=False)
        print(f"  Saved test.parquet ({len(test_df)} rows)")
    
    print("  LIAR processing complete!")
    return True


def process_arsarcasm():
    """Process ArSarcasm dataset from CSV to parquet."""
    print("\nProcessing ArSarcasm dataset...")
    
    input_dir = os.path.join(RAW_DATASETS_DIR, "arsarcasm")
    output_dir = os.path.join(PROCESSED_DATASETS_DIR, "arsarcasm")
    os.makedirs(output_dir, exist_ok=True)
    
    for split in ["train", "test"]:
        input_file = os.path.join(input_dir, f"ArSarcasm_{split}.csv")
        if not os.path.exists(input_file):
            print(f"  Warning: {input_file} not found, skipping")
            continue
        
        df = pd.read_csv(input_file)
        print(f"  Loaded {split}: {len(df)} rows")
        
        # Convert boolean sarcasm to integer (0 or 1)
        df["sarcasm"] = df["sarcasm"].map({True: 1, False: 0, "True": 1, "False": 0})
        df = df.fillna("")
        
        if not verify_labels(df, "sarcasm", f"arsarcasm/{split}"):
            return False
        
        output_file = os.path.join(output_dir, f"{split}.parquet")
        df.to_parquet(output_file, index=False)
        print(f"  Saved {split}.parquet ({len(df)} rows)")
    
    print("  ArSarcasm processing complete!")
    return True


def process_ethos_binary():
    """Process ETHOS binary dataset from CSV to parquet.
    
    Single file -> split into train/test.
    Keeps original continuous scores (0.0 to 1.0) for ranking evaluation.
    """
    print("\nProcessing ETHOS binary dataset...")
    
    input_dir = os.path.join(RAW_DATASETS_DIR, "ethos_binary")
    output_dir = os.path.join(PROCESSED_DATASETS_DIR, "ethos_binary")
    os.makedirs(output_dir, exist_ok=True)
    
    input_file = os.path.join(input_dir, "Ethos_Dataset_Binary.csv")
    if not os.path.exists(input_file):
        print(f"  Warning: {input_file} not found, skipping")
        return False
    
    df = pd.read_csv(input_file, sep=";")
    print(f"  Loaded: {len(df)} rows")
    
    # Rename columns to match data_loader_constants
    # Keep label as continuous float (0.0 to 1.0) for ranking/regression
    df = df.rename(columns={"comment": "text", "isHate": "label"})
    df = df.fillna("")
    
    if not verify_labels(df, "label", "ethos_binary"):
        return False
    
    # For stratified split, create temporary binary column
    df["_label_bin"] = (df["label"] >= 0.5).astype(int)
    split_and_save(df, output_dir, "_label_bin")
    
    # Remove temp column from saved files (reload and resave)
    for split in ["train", "test"]:
        path = os.path.join(output_dir, f"{split}.parquet")
        split_df = pd.read_parquet(path)
        split_df = split_df.drop(columns=["_label_bin"])
        split_df.to_parquet(path, index=False)
    
    print("  ETHOS binary processing complete!")
    return True


def process_ethos_multilabel():
    """Process ETHOS multilabel dataset from CSV to parquet.
    
    Single file -> split into train/test.
    Keeps original continuous scores (0.0 to 1.0) for ranking evaluation.
    """
    print("\nProcessing ETHOS multilabel dataset...")
    
    input_dir = os.path.join(RAW_DATASETS_DIR, "ethos_multi_label")
    output_dir = os.path.join(PROCESSED_DATASETS_DIR, "ethos_multilabel")
    os.makedirs(output_dir, exist_ok=True)
    
    input_file = os.path.join(input_dir, "Ethos_Dataset_Multi_Label.csv")
    if not os.path.exists(input_file):
        binary_file = os.path.join(input_dir, "Ethos_Dataset_Binary.csv")
        if os.path.exists(binary_file):
            print(f"  Warning: Found binary dataset in multilabel folder.")
            print(f"  Please download Ethos_Dataset_Multi_Label.csv from:")
            print(f"  https://github.com/intelligence-csd-auth-gr/Ethos-Hate-Speech-Dataset")
        else:
            print(f"  Warning: {input_file} not found, skipping")
        return False
    
    df = pd.read_csv(input_file, sep=";")
    print(f"  Loaded: {len(df)} rows")
    
    # Rename comment to text
    # Keep all label columns as continuous floats (0.0 to 1.0) for ranking/regression
    df = df.rename(columns={"comment": "text"})
    df = df.fillna("")
    
    # Verify primary label (violence)
    if not verify_labels(df, "violence", "ethos_multilabel"):
        return False
    
    # For stratified split, create temporary binary column
    df["_label_bin"] = (df["violence"] >= 0.5).astype(int)
    split_and_save(df, output_dir, "_label_bin")
    
    # Remove temp column from saved files
    for split in ["train", "test"]:
        path = os.path.join(output_dir, f"{split}.parquet")
        split_df = pd.read_parquet(path)
        split_df = split_df.drop(columns=["_label_bin"])
        split_df.to_parquet(path, index=False)
    
    print("  ETHOS multilabel processing complete!")
    return True


def decode_nlvr2_images(example, images_col: str = "images"):
    """Decode NLVR2 images from raw bytes to PIL Images.
    
    NLVR2 stores images as nested lists of dicts with 'bytes' key:
    [[{'bytes': b'...', 'path': None}, {'bytes': b'...', 'path': None}]]
    
    This function decodes them to a flat list of PIL Images.
    
    Args:
        example: A single dataset example (dict)
        images_col: Name of the images column
        
    Returns:
        Dict with decoded images
    """
    from PIL import Image
    from io import BytesIO
    
    raw_images = example.get(images_col, [])
    decoded = []
    
    # Handle nested list structure: [[{bytes, path}, {bytes, path}]]
    for item in raw_images:
        if isinstance(item, list):
            # Nested list - iterate through inner list
            for inner_item in item:
                if isinstance(inner_item, dict) and 'bytes' in inner_item:
                    try:
                        img_bytes = inner_item['bytes']
                        img = Image.open(BytesIO(img_bytes))
                        decoded.append(img)
                    except Exception:
                        pass  # Skip invalid images
        elif isinstance(item, dict) and 'bytes' in item:
            # Direct dict with bytes
            try:
                img_bytes = item['bytes']
                img = Image.open(BytesIO(img_bytes))
                decoded.append(img)
            except Exception:
                pass
        elif hasattr(item, 'mode'):
            # Already a PIL Image
            decoded.append(item)
    
    return {images_col: decoded}


def process_all():
    """Process all local datasets."""
    print("=" * 60)
    print("Processing all local datasets")
    print(f"Input:  {RAW_DATASETS_DIR}")
    print(f"Output: {PROCESSED_DATASETS_DIR}")
    print("=" * 60)
    
    results = {}
    results["liar"] = process_liar()
    results["arsarcasm"] = process_arsarcasm()
    results["ethos_binary"] = process_ethos_binary()
    results["ethos_multilabel"] = process_ethos_multilabel()
    
    print("\n" + "=" * 60)
    print("Processing Summary:")
    for name, success in results.items():
        status = "OK" if success else "FAILED"
        print(f"  {name}: {status}")
    print("=" * 60)
    
    return all(results.values())


if __name__ == "__main__":
    process_all()
