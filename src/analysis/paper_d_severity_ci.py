"""Intervals for the ACTIONABLE-severity metric (Paper D, review 8 con 8).

WHY THIS MODULE EXISTS. Review 8 makes two demands about severity that the paper
currently does not meet:

    "Table 2 reports an 'action.' column whose actionable counts are substantially
     below the headline coverage values... The paper should make the actionable
     metric a primary outcome, provide its confidence intervals, and report the
     same severity decomposition across defenses and temperatures."

The counts exist (`src/analysis/severity.py` graded them, no target re-queried) but
they are printed bare. This module supplies their intervals, and the interval for
the common-mode check that licenses reporting them as a footnote at all.

WHAT IS FREE AND WHAT IS NOT. Grades exist for {llama, qwen, gemma, llama70} x
{no_defense, sage} on the code arm ONLY, and they were graded 2026-07-28, which puts
them in the PRE-fix encoder era alongside tab:compose. Extending the decomposition to
the temperature panel -- the second half of con 8 -- needs NEW grading of post-fix
cells at gpt-5-mini's $0.0009/call and is therefore a costed proposal, not a free
re-analysis. Everything in this module is free.

⚠️ A PUBLISHED RANGE THAT OMITS A TARGET IT COVERS. tab:compose's caption states the
actionable share differs between defended and undefended cells "by only -3.5 to +2.6
points". Those two endpoints are exactly Llama-3.3-70B (-3.5) and Qwen2.5-7B (+2.6).
Gemma-2-9B, which IS one of tab:compose's three targets, reads -8.1 and falls outside
the printed range; Llama-3.3-70B, which supplies an endpoint, is NOT in that table.
The range therefore excludes a target the table reports and is anchored by one it does
not. Gemma's defended cell has 22 graded draws, so its point estimate carries almost
no information -- which is the honest fix here, not a wider range quoted as though it
were measured.

ESTIMATOR. Two axes, matching `paper_d_figures.bootstrap_ci` so intervals mean the
same thing across the paper: behaviors are resampled with replacement, and within a
resample each behavior's actionable count is redrawn as Binomial(graded_b, share_b).
Actionable coverage is then recomputed as the number of behaviors retaining at least
one severity-2 draw, over the same 100-behavior denominator the headline uses.
"""

from __future__ import annotations

import argparse
import collections
import glob
import json
import os

GRADE_DIR = "outputs/bestofn_attack/severity"
BEHAVIOR_DENOMINATOR = 100
ACTIONABLE = 2          # severity level counted as operationally useful

# tab:compose's published "action." column, plus the 70B figure from the appendix.
# VALIDATION GATE: intervals are refused unless these reproduce exactly.
PUBLISHED_ACTIONABLE = {"llama": 24, "qwen": 8, "gemma": 1, "llama70": 6}

TARGET_LABEL = {"llama": "Llama-3.1-8B", "qwen": "Qwen2.5-7B",
                "gemma": "Gemma-2-9B", "llama70": "Llama-3.3-70B"}


def load_grades(root: str = ".") -> dict[tuple[str, str], dict]:
    out: dict[tuple[str, str], dict] = {}
    for f in sorted(glob.glob(os.path.join(root, GRADE_DIR, "*.json"))):
        d = json.load(open(f))
        out[(d["target"], d["defense"])] = d
    return out


def per_behavior(grades: list[dict]) -> dict[str, tuple[int, int]]:
    """behavior -> (graded draws, draws at severity >= ACTIONABLE)."""
    graded: collections.Counter = collections.Counter()
    hits: collections.Counter = collections.Counter()
    for g in grades:
        b = g["id"].rsplit("__", 1)[0]
        graded[b] += 1
        sev = g.get("severity")
        if sev is not None and sev >= ACTIONABLE:
            hits[b] += 1
    return {b: (graded[b], hits[b]) for b in graded}


def actionable_coverage(grades: list[dict]) -> int:
    return sum(1 for _b, (_n, k) in per_behavior(grades).items() if k > 0)


def actionable_ci(grades: list[dict], resamples: int = 10_000,
                  seed: int = 20260822) -> tuple[float, float]:
    """95% interval for actionable coverage, on the 100-behavior denominator.

    Behaviors with NO successful draw are graded nowhere and contribute a
    structural zero; they are carried explicitly so the denominator stays the
    headline's, never the graded subset's.
    """
    import numpy as np

    pb = per_behavior(grades)
    ns = np.array([n for n, _k in pb.values()])
    ks = np.array([k for _n, k in pb.values()])
    present = len(ns)
    absent = BEHAVIOR_DENOMINATOR - present          # structural zeros
    if absent < 0:
        raise SystemExit(f"{present} graded behaviors exceeds the "
                         f"{BEHAVIOR_DENOMINATOR}-behavior denominator")

    rng = np.random.default_rng(seed)
    shares = np.divide(ks, ns, out=np.zeros(present, dtype=float), where=ns > 0)
    stats = np.zeros(resamples)
    if present:
        pick = rng.integers(0, BEHAVIOR_DENOMINATOR, size=(resamples, BEHAVIOR_DENOMINATOR))
        # Index >= present lands on a structural zero: no successful draw, so no
        # actionable draw either.
        live = pick < present
        idx = np.where(live, pick, 0)
        n_s = np.where(live, ns[idx], 0)
        p_s = np.where(live, shares[idx], 0.0)
        k_re = rng.binomial(n_s, p_s)
        stats = (k_re > 0).sum(axis=1).astype(float)
    return float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))


def share_ci(grades: list[dict], resamples: int = 10_000,
             seed: int = 20260822) -> tuple[float, float, float, int]:
    """Severity-2 SHARE of graded draws: point, lo, hi, n_graded."""
    import numpy as np
    sev = np.array([1 if (g.get("severity") is not None and g["severity"] >= ACTIONABLE)
                    else 0 for g in grades])
    n = len(sev)
    if n == 0:
        return (float("nan"), float("nan"), float("nan"), 0)
    rng = np.random.default_rng(seed)
    draws = rng.binomial(n, sev.mean(), size=resamples) / n
    return (100.0 * sev.mean(), 100.0 * float(np.percentile(draws, 2.5)),
            100.0 * float(np.percentile(draws, 97.5)), n)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    ap.add_argument("--resamples", type=int, default=10_000)
    args = ap.parse_args()

    g = load_grades(args.root)
    if not g:
        raise SystemExit(f"no grade files under {GRADE_DIR}")

    bad = []
    for t, pub in sorted(PUBLISHED_ACTIONABLE.items()):
        cell = g.get((t, "sage"))
        if cell is None:
            bad.append(f"{t}: no sage grades")
            continue
        got = actionable_coverage(cell["grades"])
        if got != pub:
            bad.append(f"{t}: actionable={got} published={pub}")
    if bad:
        raise SystemExit("PUBLISHED ACTIONABLE COUNTS NOT REPRODUCED:\n  " + "\n  ".join(bad))
    print(f"validation: all {len(PUBLISHED_ACTIONABLE)} published actionable counts "
          f"reproduced exactly\n")

    print("ACTIONABLE COVERAGE under SAGE (behaviors out of 100 with >=1 severity-2 draw)")
    print(f"{'target':16s} {'actionable':>10s} {'95% CI':>16s}   graded draws")
    for t in ("llama", "qwen", "gemma", "llama70"):
        cell = g.get((t, "sage"))
        if not cell:
            continue
        lo, hi = actionable_ci(cell["grades"], args.resamples)
        print(f"{TARGET_LABEL[t]:16s} {actionable_coverage(cell['grades']):>10d} "
              f"   [{lo:5.1f}, {hi:5.1f}]   {len(cell['grades'])}")

    print("\nCOMMON-MODE CHECK — severity-2 share, defended vs undefended")
    print(f"{'target':16s} {'SAGE':>18s} {'undefended':>18s} {'diff':>8s}   verdict")
    for t in ("llama", "qwen", "gemma", "llama70"):
        d, u = g.get((t, "sage")), g.get((t, "no_defense"))
        if not d or not u:
            continue
        dp, dlo, dhi, dn = share_ci(d["grades"], args.resamples)
        up, ulo, uhi, un = share_ci(u["grades"], args.resamples)
        overlap = not (dhi < ulo or uhi < dlo)
        verdict = "consistent" if overlap else "DIFFERS"
        if dn < 50:
            verdict += f" (n={dn}, uninformative)"
        print(f"{TARGET_LABEL[t]:16s} {dp:5.1f} [{dlo:4.1f},{dhi:4.1f}] "
              f"{up:5.1f} [{ulo:4.1f},{uhi:4.1f}] {dp - up:+8.1f}   {verdict}")


if __name__ == "__main__":
    main()
