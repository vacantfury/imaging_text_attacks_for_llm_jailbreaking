"""CIDER threshold calibration + attack-vs-benign delta comparison (review 18 con 7).

CIDER's tau is not a chosen number: `other_repos/CIDER/code/defender.py` sets it as a
percentile of the delta distribution measured on CLEAN images at a conservative
ratio, so tau IS a benign false-positive budget:

    tau = numpy.percentile(clean_deltas, (1 - fpr_ratio) * 100)

This reads the `cider_deltas.jsonl` traces written by a calibration pass
(`threshold: null`), emits tau for a sweep of benign FPR budgets, and then reports
what each tau would block on the attack side. That second half is the actual
result: if the attack delta distribution sits on top of the benign one, no tau
separates them and CIDER cannot reach representation-shifting renders --- the
pre-registered prediction in conf/defense/cider.yaml.

Usage:
    python src/analysis/paper_c_cider_threshold.py \
        --benign 'outputs/autoattack_defense/cider_deltas/*__non_llm_baseline.jsonl' \
                 'outputs/autoattack_defense/cider_deltas/*__ir_plain.jsonl' \
        --attack 'outputs/autoattack_defense/cider_deltas/*__ir_[!p]*.jsonl'

Note the benign image channel is `ir_plain` and the benign text channel is
`non_llm_baseline`; the attack globs must EXCLUDE those two or the calibration set
leaks into the attack set.

TRACE FILENAMES ARE `<chain_dir>__<step>.jsonl` (changed 2026-08-05). They used to
be `<step>.jsonl`, which collided whenever two chains ended in the same renderer —
Paper B's arms all end in `ir_constant`, so its benign and attack channels would
have overwritten each other and tau would have been calibrated against whichever
ran last. Globs therefore need the `*__` prefix; the label printed per row is the
full chain+step, so the report still separates channels rather than pooling them.
"""
from __future__ import annotations

import argparse
import glob
import json
import os

import numpy as np

FPR_SWEEP = [0.99, 0.95, 0.90, 0.80, 0.50]


def load(patterns: list[str]) -> dict[str, list[float]]:
    """{source label -> deltas}. Label is the attack/channel dir, so the report
    separates per-attack behaviour instead of pooling it away."""
    out: dict[str, list[float]] = {}
    for pat in patterns:
        for path in sorted(glob.glob(pat)):
            label = os.path.basename(path)[:-len(".jsonl")]
            vals = out.setdefault(label, [])
            with open(path) as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        vals.append(float(json.loads(line)["delta"]))
    return out


def describe(name: str, vals: np.ndarray) -> None:
    print(f"  {name:34} n={len(vals):4d}  mean={vals.mean():+.4f}  "
          f"sd={vals.std():.4f}  p5={np.percentile(vals,5):+.4f}  "
          f"p50={np.percentile(vals,50):+.4f}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign", nargs="+", required=True)
    ap.add_argument("--attack", nargs="+", required=True)
    args = ap.parse_args()

    benign = load(args.benign)
    attack = load(args.attack)
    if not benign:
        raise SystemExit("no benign delta traces found — run the calibration pass "
                         "(threshold: null) over the benign channels first")
    if not attack:
        raise SystemExit("no attack delta traces found")

    b_all = np.array([v for vals in benign.values() for v in vals])
    a_all = np.array([v for vals in attack.values() for v in vals])

    print("=== delta distributions (delta = cos(text,denoised) - cos(text,original)) ===")
    print("BENIGN (calibration set):")
    for k in sorted(benign):
        describe(k, np.array(benign[k]))
    describe("ALL BENIGN", b_all)
    print("ATTACK:")
    for k in sorted(attack):
        describe(k, np.array(attack[k]))
    describe("ALL ATTACK", a_all)

    print("\n=== tau by benign FPR budget, and what it blocks ===")
    print(f"  {'fpr_ratio':>10} {'tau':>10} {'benign blocked':>15} {'attack blocked':>15}")
    for ratio in FPR_SWEEP:
        tau = float(np.percentile(b_all, (1 - ratio) * 100))
        b_block = 100.0 * float((b_all < tau).mean())
        a_block = 100.0 * float((a_all < tau).mean())
        print(f"  {ratio:>10.2f} {tau:>+10.4f} {b_block:>14.1f}% {a_block:>14.1f}%")

    # Separability: if the attack distribution is not shifted DOWN relative to
    # benign, no tau can gate one without the other. Reported as the AUC of the
    # one-sided test (probability a random attack delta is below a random benign
    # one); 0.5 = indistinguishable, 1.0 = perfectly separable.
    wins = (a_all[:, None] < b_all[None, :]).mean() if a_all.size * b_all.size < 4e7 else float("nan")
    print(f"\nseparability AUC (P[attack delta < benign delta]) = {wins:.3f}"
          "   0.50 = indistinguishable, 1.00 = perfectly separable")
    print("\nA value near 0.50 confirms the pre-registered prediction: CIDER's "
          "denoise-shift signal does not distinguish clean synthetic renders from "
          "benign images, because neither carries adversarial perturbation.")


if __name__ == "__main__":
    main()
