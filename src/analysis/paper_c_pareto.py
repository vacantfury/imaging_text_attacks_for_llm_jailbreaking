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

⚠️ THE COST OF THAT CHOICE, and the guard that pays it (2026-08-07). An entered table is a
SECOND HOME for every number in it, so when `b266892` rebuilt the two fixed encoders and the
oracle audit moved the baselines to the deployable arm, this file kept printing the pre-fix
frontier -- silently, because a hardcoded table cannot fail. The appendix's budget ladder then
published a dominated ECSO row at an ASR that no longer existed. The entered table stays (its
reason is sound), but `verify()` now rebuilds every ASR from the shared selector and the
baseline script and RAISES on any mismatch, so the second home can no longer drift from the
first. Over-refusal is not cross-checked here -- it has no second computation to check against
-- so it carries `paper_c_overrefusal_decomp` as its named provenance instead.

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
POINTS_2CAT = {
    'qwen2_5_vl_7b': [
        ('undefended',        89, 26, 'T1 header'),
        ('ECSO',              86, 27, 'T1 header, deployable arm'),
        ('SemanticSmooth',    81, 24, 'T1 header, deployable arm'),
        ('WildGuard gb',      77, 49, 'T1 + decomp'),
        ('WildGuard mc',      68, 64, 'T1'),
        ('WildGuard +rg',     43, 84, 'T1'),
        ('Qwen3Guard gb',     75, 47, 'T1 + decomp'),
        ('Qwen3Guard mc',     68, 59, 'T1'),
        ('Qwen3Guard +rg',    50, 81, 'T1'),
        ('GuardReasoner gb',  84, 67, 'T1 + decomp'),
        ('GuardReasoner mc',  71, 60, 'T1'),
        ('GuardReasoner +rg', 63, 87, 'T1'),
        ('LlamaGuard-3 gb',   66, 28, 'T1 + decomp'),
        ('LlamaGuard-3 mc',   78, 28, 'T1'),
        ('LlamaGuard-3 +rg',  49, 33, 'T1'),
        ('ThinkGuard gb',     79, 47, 'T1 + decomp'),
        ('ThinkGuard mc',     81, 45, 'T1'),
        ('ThinkGuard +rg',    58, 66, 'T1'),
    ],
    'internvl3_8b': [
        ('undefended',        94, 53, 'T1 header'),
        ('ECSO',              95, 50, 'T1 header, deployable arm'),
        # SemanticSmooth WAS missing from this target's set, which is why the appendix
        # said "17 configurations on InternVL3". The second-target run exists and is in
        # Table 1's header; omitting it understated the frontier by one point.
        ('SemanticSmooth',    83, 50, 'T1 header, deployable arm'),
        ('WildGuard gb',      86, 70, 'T1 + decomp'),
        ('WildGuard mc',      70, 84, 'T1'),
        ('WildGuard +rg',     49, 90, 'T1'),
        ('Qwen3Guard gb',     83, 69, 'T1 + decomp'),
        ('Qwen3Guard mc',     76, 80, 'T1'),
        ('Qwen3Guard +rg',    55, 86, 'T1'),
        ('GuardReasoner gb',  88, 81, 'T1 + decomp'),
        ('GuardReasoner mc',  76, 82, 'T1'),
        ('GuardReasoner +rg', 69, 92, 'T1'),
        ('LlamaGuard-3 gb',   82, 54, 'T1 + decomp'),
        ('LlamaGuard-3 mc',   81, 55, 'T1'),
        ('LlamaGuard-3 +rg',  61, 57, 'T1'),
        ('ThinkGuard gb',     83, 67, 'T1 + decomp'),
        ('ThinkGuard mc',     81, 72, 'T1'),
        ('ThinkGuard +rg',    62, 79, 'T1'),
    ],
}

# Entered label -> (guard key, condition) for the cross-check. The three header rows
# are checked against `paper_c_floor_baselines` instead, since they are not guard cells.
GUARD_KEY = {'WildGuard': 'wildguard', 'Qwen3Guard': 'qwen3guard_gen_8b',
             'GuardReasoner': 'guardreasoner_vl_7b', 'LlamaGuard-3': 'llama_guard_3_8b',
             'ThinkGuard': 'thinkguard'}
COND_KEY = {'gb': 'gb', 'mc': 'mc', '+rg': 'rg'}

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


GUARD_LABELS = ['WildGuard', 'Qwen3Guard', 'GuardReasoner', 'LlamaGuard-3', 'ThinkGuard']
CONDS = [('gb', 'gb'), ('mc', 'mc'), ('+rg', 'rg')]


def points_balanced() -> tuple:
    """The frontier on the CATEGORY-BALANCED benign axis (n=300 x 2 channels = 600 paired).

    Founded 2026-08-21 answering cspaper review 5 con 5 / Q1. The two-category slice
    (`POINTS_2CAT`) is behaviors 0-99 of OR-Bench-Hard in file order, which the released
    file sorts by category, so it is 72 deception + 28 harassment and nothing else -- the
    paper's own appendix calls it unrepresentative. Reporting the frontier on it while the
    balanced measurement sat in the appendix was the review's sharpest correct hit.

    ASR is unchanged: the safety axis does not depend on which benign prompts we draw.
    Over-refusal is DERIVED here rather than entered, so unlike the ASR half it has no
    second home that can go stale.

    Returns (points_by_target, excluded) -- `excluded` is loud on purpose: ECSO and
    SemanticSmooth were never re-run on the balanced draw, so they cannot appear on this
    axis. They sit at 81-95% ensemble ASR, far above any configuration that could contend
    for the low-ASR corner, so their absence cannot change the corner verdict; it does mean
    the balanced Pareto set is over guard configurations and the undefended floor only.

    !!! NOT THE PAPER'S AXIS AS OF 2026-08-21 -- INSTRUMENT DEFECT !!!
    The balanced draw's IMAGE channel was rendered with `keep_text=True` (the default) while
    every other benign render in this paper passes `keep_text: false`, so its text-only
    guards could read the request instead of being blind to it: 74% blocked against 0% on
    the two-category draw. Half of every pooled number here therefore prices RE-RENDERING,
    not restoring a view. Full account: the header of
    `src/analysis/paper_c_benign_stratified.py`. The paper reverted to `POINTS_2CAT` --
    category-unrepresentative but instrument-matched to the attack axis -- and this function
    is kept for the diagnostic and for the re-run, which needs only stage 1 repeated with the
    flag set. It raises unless the caller opts in.
    """
    from src.analysis.paper_c_benign_stratified import balanced_overrefusal, scan, \
        instrument_gate
    if not instrument_gate(scan()):
        raise SystemExit(
            'points_balanced(): the balanced benign image channel is contaminated '
            '(keep_text=True).\nRe-run benign_stratified_s1.yaml (corrected) + the s2 '
            'chunks, or use POINTS_2CAT.')
    B = balanced_overrefusal()
    out, excluded = {}, []
    for target, pts in POINTS_2CAT.items():
        rows, asr = [], {lab: a for lab, a, _o, _s in pts}
        floor = B.get((target, 'FLOOR', 'floor'))
        if floor is not None and 'undefended' in asr:
            rows.append(('undefended', asr['undefended'], round(floor, 1), 'balanced floor'))
        for gl in GUARD_LABELS:
            for lab, cond in CONDS:
                key = f'{gl} {lab}'
                over = B.get((target, GUARD_KEY[gl], cond))
                if key in asr and over is not None:
                    rows.append((key, asr[key], round(over, 1), 'T1 ASR + balanced benign'))
        for lab, a, _o, _s in pts:
            if lab not in {r[0] for r in rows}:
                excluded.append(f'{target}/{lab} (ASR {a}) — not run on the balanced draw')
        out[target] = rows
    return out, excluded


def verify() -> None:
    """Rebuild every entered ASR from the data and RAISE on mismatch.

    This is the guard the docstring promises. Guard cells come from the shared selector
    (`paper_c_select`), the three header rows from `paper_c_floor_baselines`'s deployable
    arm -- the same two functions the paper's own tables are built from, so a divergence
    here means the entered table has gone stale, not that the data moved.
    """
    from src.analysis import paper_c_select as S
    from src.analysis import paper_c_floor_baselines as F

    shared, bad = S.scan(), []
    fsel = F.scan()
    base = {'undefended': 'no_defense', 'ECSO': 'ecso', 'SemanticSmooth': 'semantic_smooth'}

    for target, pts in POINTS_2CAT.items():
        rebuilt = {}
        for guard_lab, guard in GUARD_KEY.items():
            for lab, cond in COND_KEY.items():
                found, missing = S.postfix_dirs(shared, target, guard, cond)
                if missing:
                    bad.append('%s %s %s: only %d/11 chains (%s)'
                               % (target, guard_lab, lab, 11 - len(missing), missing))
                    continue
                rebuilt['%s %s' % (guard_lab, lab)] = round(S.rate(S.ens(found.values())))
        for lab, defense in base.items():
            if defense == 'no_defense':
                dirs, missing = F.collect(fsel, F.PUBLISHED[(defense, target)], defense,
                                          target, '-', swap=(F.RERUN, '-'))
            else:
                dirs, missing, _ = F.collect_deployable(
                    fsel, F.PUBLISHED[(defense, target)], F.ORACLE[defense], defense,
                    target, (F.RERUN, 'original'), (F.RERUN, 'encoded'))
            if missing:
                bad.append('%s %s: only %d/11 chains (%s)'
                           % (target, lab, 11 - len(missing), missing))
                continue
            rebuilt[lab] = round(F.rate(F.ensemble(dirs)))
        for label, asr, _over, src in pts:
            if label in rebuilt and rebuilt[label] != asr:
                bad.append('%s %-18s entered %d, data says %d   [%s]'
                           % (target, label, asr, rebuilt[label], src))
    if bad:
        raise SystemExit('🔴 POINTS is STALE — the entered frontier no longer matches the '
                         'data:\n  ' + '\n  '.join(bad))
    print('✅ every entered ASR reproduces from the data (guard cells via paper_c_select, '
          'headers via paper_c_floor_baselines deployable arm)')


def report() -> None:
    verify()
    for target, pts in POINTS_2CAT.items():
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
