"""Paper C (AS-3) — FAMILY C: the utility axis, corrected like the safety axis.  ($0, stored data.)

cspaper review 3 con 4: "The safety-utility trade-off is central to the paper, so the utility-side
changes should receive paired uncertainty estimates and an appropriately defined multiple-comparison
treatment comparable to the ASR side." That is a real gap. The paper declares family A (the 20
within-run ENSEMBLE contrasts, exact McNemar, Bonferroni 0.05/20) and family B (32 dev-vs-held-out
level comparisons), and then reports every over-refusal movement uncorrected -- while the headline
claim is two-dimensional by construction.

This builds the exact mirror of family A on the benign axis:

    5 guards x 2 targets x 2 transitions (gb->mc, mc->+rg) = 20 contrasts
    paired principal = the SAME prompt under both arms, both benign channels pooled
                       (100 text + 100 image = 200 paired prompts per cell)
    test  = exact paired McNemar on refusal flags      alpha = 0.05 / 20
    size  = bootstrap CI on the paired difference (10^4 draws, both arms resampled together)

⚠️ BENIGN CAMPAIGN IS PINNED, and not to r1. r1's benign guard cells were judged by gpt-5-nano; the
paper's decided judge is gpt-5-mini, and the only complete gpt-5-mini benign guard grid is
`paper_c_replicate_r2`. Mixing judges across the two axes of one claim would be worse than crossing
campaigns, so the pin is inherited from paper_c_end_to_end and named in the output.

    python -m src.analysis.paper_c_utility_family
"""
from __future__ import annotations

import random

from src.analysis import paper_c_end_to_end as E

BONF = 0.05 / 20
TRANSITIONS = [('gb', 'mc', 'gb->mc  (amplifier)'), ('mc', 'rg', 'mc->+rg (re-screening)')]
BOOT = 10_000


def boot_ci(a: dict, b: dict, seed: int = 0) -> tuple[float, float]:
    """Percentile CI on the paired difference, resampling PROMPTS (both arms together)."""
    keys = sorted(set(a) & set(b))
    rng = random.Random(seed)
    n = len(keys)
    diffs = []
    for _ in range(BOOT):
        s = [keys[rng.randrange(n)] for _ in range(n)]
        diffs.append(100.0 * (sum(b[k] for k in s) - sum(a[k] for k in s)) / n)
    diffs.sort()
    return diffs[int(0.025 * BOOT)], diffs[int(0.975 * BOOT)]


def main() -> None:
    bsel = E.scan_benign()
    print(f'benign cells indexed: {len(bsel)}   campaign pinned: {E.BENIGN_CAMPAIGN} '
          f'(judge {E.JUDGE})\n')
    print('FAMILY C — over-refusal contrasts, paired on the same 200 benign prompts')
    print(f'{"target":15}{"guard":15}{"transition":24}{"from":>7}{"to":>7}{"d":>7}'
          f'{"95% CI":>18}{"p":>10}  sig')

    rows, n_raw, n_bonf, n_ci = [], 0, 0, 0
    for target in ('qwen2_5_vl_7b', 'internvl3_8b'):
        for g in E.LAB:
            for c0, c1, label in TRANSITIONS:
                A = E.pooled_benign(bsel, target, g, c0)
                B = E.pooled_benign(bsel, target, g, c1)
                if A is None or B is None:
                    print(f'{target:15}{E.LAB[g]:15}{label:24}  MISSING CELL')
                    continue
                keys = sorted(set(A) & set(B))
                fa = 100.0 * sum(A[k] for k in keys) / len(keys)
                fb = 100.0 * sum(B[k] for k in keys) / len(keys)
                p = E.mcnemar(A, B)
                lo, hi = boot_ci(A, B)
                n_raw += p < 0.05
                n_bonf += p < BONF
                n_ci += not (lo <= 0 <= hi)
                sig = '‡' if p < BONF else ('†' if p < 0.05 else '')
                rows.append((target, g, label, fa, fb, fb - fa, lo, hi, p))
                print(f'{target:15}{E.LAB[g]:15}{label:24}{fa:7.1f}{fb:7.1f}{fb-fa:+7.1f}'
                      f'{f"[{lo:+.1f},{hi:+.1f}]":>18}{p:10.2g}  {sig}')

    print(f'\nn = {len(rows)} contrasts   paired n = 200 prompts each')
    print(f'  p < 0.05 uncorrected : {n_raw}/{len(rows)}')
    print(f'  p < {BONF:.4g} (Bonferroni): {n_bonf}/{len(rows)}')
    print(f'  bootstrap CI excludes 0: {n_ci}/{len(rows)}')
    up = [r for r in rows if r[5] > 0]
    print(f'  direction: {len(up)}/{len(rows)} contrasts RAISE over-refusal')
    for _, _, label, *_ in TRANSITIONS and []:
        pass
    for c0, c1, label in TRANSITIONS:
        sub = [r for r in rows if r[2] == label]
        if sub:
            ds = sorted(r[5] for r in sub)
            print(f'  {label}: delta {ds[0]:+.1f} to {ds[-1]:+.1f}, '
                  f'{sum(1 for r in sub if r[8] < BONF)}/{len(sub)} survive Bonferroni')


if __name__ == '__main__':
    main()
