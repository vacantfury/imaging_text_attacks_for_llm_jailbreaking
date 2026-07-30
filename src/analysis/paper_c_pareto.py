"""Pareto dominance + pre-specified operating budgets for Paper C (review 17 con 2).

cspaper review 17, con 2: *"The paper labels 43% to 65% ensemble ASR 'unsafe' and 81% to 92%
over-refusal 'impractical' ... but no target risk level, cost model, or application-specific
operating criterion is defined ... It is therefore difficult to assess the claim that 'no
configuration achieves both low attack-success and low over-refusal,' because 'low' is not
formally specified. The paper should report Pareto dominance directly, avoid implying a
universal deployment threshold, and present several pre-specified operating budgets with
confidence intervals."*

The objection is fair and it is fixable without defining "low": Pareto dominance is
threshold-FREE, and a ladder of budgets replaces one privileged threshold with a curve the
reader can enter at their own risk tolerance.

Deliberate design choice: this script does NOT recompute any published number. Every point is
the value already reported in the paper (Table 1 / the baseline runs), entered here with its
provenance, because three separate hand-rederivations of the undefended floor disagreed with
the checksummed `paper_c_ensemble.py` before this rule was adopted. Wilson intervals are exact
functions of (k, n=100), so the CIs need no data access either.

    python -m src.analysis.paper_c_pareto
"""
from __future__ import annotations

import math

N = 100  # every cell is n=100 behaviors

# (label, ensemble ASR %, benign over-refusal %, provenance)
#   ASR / over-ref for mc and +rg: Table 1 (tab:reguard).
#   floor + ECSO + SemanticSmooth: Table 1 block headers.
#   gb over-refusal is NOT in Table 1; it is measured from the same benign panel by
#   paper_c_overrefusal_decomp.py (avg of text+image, gpt-5-mini rejudged, each cell
#   reconciled against its stored rate) and is labelled as such.
POINTS = {
    'qwen2_5_vl_7b': [
        ('undefended',        89, 26, 'T1 header'),
        ('ECSO',              90, 27, 'T1 header'),
        ('SemanticSmooth',    80, 25, 'baseline run 235412'),
        ('WildGuard gb',      75, 49, 'T1 + decomp'),
        ('WildGuard mc',      72, 64, 'T1'),
        ('WildGuard +rg',     43, 84, 'T1'),
        ('Qwen3Guard gb',     76, 47, 'T1 + decomp'),
        ('Qwen3Guard mc',     65, 59, 'T1'),
        ('Qwen3Guard +rg',    43, 81, 'T1'),
        ('GuardReasoner gb',  84, 67, 'T1 + decomp'),
        ('GuardReasoner mc',  71, 60, 'T1'),
        ('GuardReasoner +rg', 58, 87, 'T1'),
        ('LlamaGuard-3 gb',   71, 28, 'T1 + decomp'),
        ('LlamaGuard-3 mc',   79, 28, 'T1'),
        ('LlamaGuard-3 +rg',  48, 33, 'T1'),
        ('ThinkGuard gb',     78, 47, 'T1 + decomp'),
        ('ThinkGuard mc',     77, 45, 'T1'),
        ('ThinkGuard +rg',    54, 66, 'T1'),
    ],
    'internvl3_8b': [
        ('undefended',        91, 53, 'T1 header'),
        ('ECSO',              91, 47, 'T1 header'),
        ('WildGuard gb',      81, 70, 'T1 + decomp'),
        ('WildGuard mc',      63, 84, 'T1'),
        ('WildGuard +rg',     48, 90, 'T1'),
        ('Qwen3Guard gb',     81, 69, 'T1 + decomp'),
        ('Qwen3Guard mc',     69, 80, 'T1'),
        ('Qwen3Guard +rg',    56, 86, 'T1'),
        ('GuardReasoner gb',  90, 81, 'T1 + decomp'),
        ('GuardReasoner mc',  67, 82, 'T1'),
        ('GuardReasoner +rg', 65, 92, 'T1'),
        ('LlamaGuard-3 gb',   79, 54, 'T1 + decomp'),
        ('LlamaGuard-3 mc',   83, 55, 'T1'),
        ('LlamaGuard-3 +rg',  61, 57, 'T1'),
        ('ThinkGuard gb',     82, 67, 'T1 + decomp'),
        ('ThinkGuard mc',     77, 72, 'T1'),
        ('ThinkGuard +rg',    59, 79, 'T1'),
    ],
}

BUDGETS = [30, 35, 40, 50, 60, 70, 80, 95]


def wilson(k: int, n: int = N, z: float = 1.96) -> tuple:
    """Exact Wilson score interval, in percent."""
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (100 * max(0.0, c - h), 100 * min(1.0, c + h))


def pareto(points: list) -> list:
    """Points not dominated on BOTH axes (lower ASR and lower over-refusal are better).

    Dominance is strict-in-one, weak-in-both: q dominates p if q is <= p on both axes and
    strictly < on at least one. Threshold-free, which is the point: it answers con 2 without
    ever defining "low".
    """
    out = []
    for p in points:
        dominated = any(q is not p and q[1] <= p[1] and q[2] <= p[2]
                        and (q[1] < p[1] or q[2] < p[2]) for q in points)
        if not dominated:
            out.append(p)
    return sorted(out, key=lambda x: x[2])


def report() -> None:
    for target, pts in POINTS.items():
        print('\n' + '=' * 78)
        print('%s   --- %d measured configurations' % (target, len(pts)))
        print('=' * 78)
        pf = pareto(pts)
        names = {p[0] for p in pf}
        print('PARETO-OPTIMAL SET (threshold-free; %d of %d configurations)' % (len(pf), len(pts)))
        for label, asr, over, src in pf:
            lo, hi = wilson(asr)
            print('  %-20s ASR %3d [%4.1f-%4.1f]   over-ref %3d   (%s)'
                  % (label, asr, lo, hi, over, src))
        dom = [p for p in pts if p[0] not in names]
        print('  dominated (%d): %s' % (len(dom), ', '.join(p[0] for p in dom)))

        print('\nBEST ACHIEVABLE ENSEMBLE ASR UNDER A PRE-SPECIFIED OVER-REFUSAL BUDGET')
        print('  (no privileged threshold: read the row matching your own risk tolerance)')
        print('  %-8s %-22s %-18s %s' % ('budget', 'best config', 'ensemble ASR [95% CI]', 'note'))
        prev = None
        for b in BUDGETS:
            elig = [p for p in pts if p[2] <= b]
            if not elig:
                print('  <=%-6d %-22s %-18s %s' % (b, '(none)', '--', 'no configuration fits'))
                continue
            # Tie-break on over-refusal: two configs can share an ASR (Qwen3Guard and
            # WildGuard both reach 43 on Qwen), and naming the higher-over-refusal one
            # would advertise a DOMINATED config as the budget's best choice.
            best = min(elig, key=lambda x: (x[1], x[2]))
            lo, hi = wilson(best[1])
            note = ''
            if prev is not None and best[1] == prev:
                note = 'no gain over the tighter budget'
            prev = best[1]
            print('  <=%-6d %-22s %3d [%4.1f-%4.1f]   %s'
                  % (b, best[0], best[1], lo, hi, note))

        floor = next(p for p in pts if p[0] == 'undefended')
        print('\n  undefended reference: ASR %d, over-refusal %d' % (floor[1], floor[2]))
        best_any = min(pts, key=lambda x: x[1])
        lo, hi = wilson(best_any[1])
        print('  lowest ASR at ANY utility cost: %s, %d [%4.1f-%4.1f] at over-refusal %d'
              % (best_any[0], best_any[1], lo, hi, best_any[2]))


if __name__ == '__main__':
    report()
