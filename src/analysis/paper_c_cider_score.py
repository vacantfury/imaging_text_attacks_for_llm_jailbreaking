"""Score stored prompt_transform images with CIDER's detector — no target, no judge.

CIDER's decision depends only on the (text, image) pair, so its delta distribution
can be measured directly off the stored attack/benign artifacts. Doing that FIRST
means tau is calibrated before any target call, so the graded run costs one pass
instead of two (a calibration pass at tau=null would otherwise burn target+judge
budget to reproduce the undefended floor).

Runs on a GPU node; falls back to CPU (slow but correct).

Usage (on the cluster, inside the repo):
    python src/analysis/paper_c_cider_score.py \
        --dirs outputs/autoattack_defense/prompt_transform/orbench_benign_hard/*/ir_plain \
               outputs/autoattack_defense/prompt_transform/harmbench/*/ir_figstep \
        --dncnn ~/models/cider_dncnn_checkpoint.pth.tar
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from pathlib import Path

from src.defense.cider import Cider
from src.experiment.schemas import Prompt
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_prompts(step_dir: Path) -> list[Prompt]:
    path = step_dir / "prompts.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"no prompts.jsonl in {step_dir}")
    prompts = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                prompts.append(Prompt(**json.loads(line)))
    return prompts


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="+", required=True,
                    help="prompt_transform STEP dirs (the ones holding prompts.jsonl)")
    ap.add_argument("--dncnn", required=True)
    # CIDER embeds with the target MLLM's own encoders, not CLIP's contrastive
    # space — corrected 2026-08-05, see src/defense/cider.py. Runs made before
    # that date used CLIP and are invalid.
    ap.add_argument("--encoder", default="llava-hf/llava-1.5-7b-hf")
    ap.add_argument("--trace-dir", default="outputs/autoattack_defense/cider_deltas")
    ap.add_argument("--limit", type=int, default=100,
                    help="prompts per dir; matches the grid's prompt_range [0,99]")
    args = ap.parse_args()

    step_dirs: list[str] = []
    for pat in args.dirs:
        step_dirs.extend(sorted(glob.glob(pat)))
    if not step_dirs:
        raise SystemExit(f"no dirs matched: {args.dirs}")

    det = Cider(encoder_model=args.encoder, dncnn_checkpoint=args.dncnn,
                threshold=None, trace_dir=args.trace_dir)
    os.makedirs(args.trace_dir, exist_ok=True)

    for sd in step_dirs:
        step = Path(sd)
        prompts = load_prompts(step)[:args.limit]
        items = []
        for p in prompts:
            if not p.image_encoded:
                continue
            rel = p.image_encoded[0] if isinstance(p.image_encoded, list) else p.image_encoded
            img_path = step / rel
            if not img_path.exists():
                logger.warning(f"{step.name}: missing image {img_path}")
                continue
            from PIL import Image
            items.append((p.id, p.encoded or "", Image.open(img_path)))
        if not items:
            logger.info(f"{step.name}: no images (text-only step) — CIDER inapplicable, skipped")
            continue
        deltas = det._deltas(items)
        out = Path(args.trace_dir) / f"{step.name}.jsonl"
        with open(out, "w") as fh:
            for pid, d in deltas.items():
                fh.write(json.dumps({"id": str(pid), "delta": float(d)}) + "\n")
        vals = list(deltas.values())
        print(f"{step.name:26} n={len(vals):4d}  "
              f"mean={sum(vals)/len(vals):+.4f}  min={min(vals):+.4f}  -> {out}")


if __name__ == "__main__":
    main()
