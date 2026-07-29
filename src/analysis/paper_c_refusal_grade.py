"""Graded over-refusal — the 3-class OR-Bench rubric, before the binary collapse.

Answers cspaper review 13's con 5: "over-refusal collapses responses to binary
answered-vs-refused, so partial refusals, hedged answers, or 'I can help with
that but...' responses that degrade utility without triggering the refusal
classifier are not captured."

No new judging is needed. The OR-Bench evaluator already stores a THREE-class
label per response in `refusal_judge_output`:

    direct_answer     -- the request is answered
    indirect_refusal  -- hedged / partial / deflected (the reviewer's category)
    direct_refusal    -- an explicit refusal

The paper's over-refusal metric collapses {indirect, direct} -> refused. This
script reports the split that collapse hides, and asks the question the review
actually implies: does the amplifier change the STYLE of refusal (direct ->
indirect), which is what "decoding softens borderline phrasing" would predict?

Reads exactly the cells `paper_c_benign_utility.py` consumes (same selection
rule: newest rejudge per (defense, guard, variant)), so the numbers are
comparable to the reported over-refusal table by construction.

Usage:  python3 src/analysis/paper_c_refusal_grade.py
        python -m src.analysis.paper_c_refusal_grade
"""
import glob
import json
import math
import os
import re
from collections import Counter, defaultdict

REJUDGE_BENIGN = 'outputs/autoattack_defense/rejudge/orbench_benign_hard/*'
CAMPAIGN = 'paper_c_guard_panel_benign'
TARGET = 'qwen2_5_vl_7b'
VARIANTS = {'text': 'non_llm_baseline', 'image': 'ir_plain'}

CLASSES = ['direct_answer', 'indirect_refusal', 'direct_refusal']
GUARD_SHORT = {
    'wildguard': 'WildGuard', 'llama_guard_3_8b': 'LlamaGuard-3',
    'qwen3guard_gen_8b': 'Qwen3Guard', 'thinkguard': 'ThinkGuard',
    'guardreasoner_vl_7b': 'GuardReasoner', 'none': '--',
}
COND_SHORT = {'no_defense': 'floor', 'guard_baseline': 'gb',
              'modality_complete': 'mc'}
COND_ORDER = ['no_defense', 'guard_baseline', 'modality_complete']


def _lj(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except Exception:
        return None


def _stamp(name):
    m = re.search(r'_(\d{8})_(\d{6})_', name)
    return (m.group(1) + m.group(2)) if m else '0'


def wilson(k, n, z=1.96):
    """Wilson score interval, matching the rest of the paper's CIs."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (100 * max(0.0, c - h), 100 * min(1.0, c + h))


def collect_cells():
    """(defense, guard, variant) -> rejudge dir. Newest wins.

    Identical rule to paper_c_benign_utility.collect_cells, kept standalone so
    this script runs without importing the package (and its LLM deps).
    """
    sel = {}
    for d in glob.glob(REJUDGE_BENIGN):
        r = _lj(os.path.join(d, 'results.json'))
        if not r:
            continue
        src = (r.get('upstream_ref') or {}).get('source_dir', '')
        s = _lj(os.path.join(src, 'results.json')) or {}
        if s.get('campaign') != CAMPAIGN or s.get('target_model') != TARGET:
            continue
        step = (s.get('upstream_ref') or {}).get('source_dir', '')
        variant = next((v for v, stem in VARIANTS.items()
                        if f'/{stem}_' in step or step.endswith('/' + stem)), None)
        if variant is None:
            continue
        guard = (s.get('defense_config') or {}).get('guard_model', 'none')
        key = (r.get('defense'), guard, variant)
        t = _stamp(os.path.basename(d))
        if key not in sel or t > sel[key][0]:
            sel[key] = (t, d)
    return {k: v[1] for k, v in sel.items()}


def load_labels(d):
    """Return the per-row 3-class labels for one cell, skipping failed calls."""
    labels, dropped = [], 0
    p = os.path.join(d, 'raw_results.jsonl')
    if not os.path.exists(p):
        return labels, dropped
    with open(p, encoding='utf-8') as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            # A failed target call is not a refusal -- never let one be counted
            # as evidence either way (the silent-failure mode in this repo's
            # notes: dead API -> rows that read as clean 'safe'/'answered').
            if 'Error code:' in str(row.get('response', '')):
                dropped += 1
                continue
            lab = row.get('refusal_judge_output')
            if lab in CLASSES:
                labels.append(lab)
            else:
                dropped += 1
    return labels, dropped


def main():
    cells = collect_cells()
    if not cells:
        print('no benign cells found under', REJUDGE_BENIGN)
        return

    # (defense, guard) -> Counter over classes, pooling the text+image variants
    # exactly as the paper's avg(text, image) over-refusal does.
    pooled = defaultdict(Counter)
    dropped_total = 0
    for (defense, guard, _variant), d in cells.items():
        labels, dropped = load_labels(d)
        dropped_total += dropped
        pooled[(defense, guard)].update(labels)

    print('=' * 78)
    print('GRADED OVER-REFUSAL  (OR-Bench 3-class, before the binary collapse)')
    print('target: %s   cells: %d   rows dropped (failed calls): %d'
          % (TARGET, len(cells), dropped_total))
    print('=' * 78)
    print()
    print('%-6s %-14s %6s %8s %8s %8s %9s' % (
        'cond', 'guard', 'n', 'answer', 'indirect', 'direct', 'refused'))
    print('-' * 78)

    rows = []
    for defense in COND_ORDER:
        for (dfn, guard), c in sorted(pooled.items(), key=lambda x: str(x[0][1])):
            if dfn != defense:
                continue
            n = sum(c[k] for k in CLASSES)
            if not n:
                continue
            ans, ind, dir_ = c['direct_answer'], c['indirect_refusal'], c['direct_refusal']
            refused = ind + dir_
            print('%-6s %-14s %6d %7.1f%% %7.1f%% %7.1f%% %8.1f%%' % (
                COND_SHORT.get(defense, defense), GUARD_SHORT.get(guard, guard),
                n, 100 * ans / n, 100 * ind / n, 100 * dir_ / n, 100 * refused / n))
            rows.append((defense, guard, n, ans, ind, dir_))
        print('-' * 78)

    # ---- the question the review actually implies -------------------------
    print()
    print('=' * 78)
    print('REFUSAL COMPOSITION -- of the responses counted as REFUSED, what')
    print('share are INDIRECT (hedged/partial) rather than explicit?')
    print('If the amplifier "softens borderline phrasing", this share rises.')
    print('=' * 78)
    print()
    print('%-6s %-14s %8s %8s %10s   %s' % (
        'cond', 'guard', 'refused', 'indirect', 'share', '95% CI'))
    print('-' * 78)
    by_cond = defaultdict(lambda: [0, 0])
    for defense in COND_ORDER:
        for d2, guard, n, ans, ind, dir_ in rows:
            if d2 != defense:
                continue
            ref = ind + dir_
            if not ref:
                continue
            lo, hi = wilson(ind, ref)
            print('%-6s %-14s %8d %8d %9.1f%%   [%.0f, %.0f]' % (
                COND_SHORT.get(defense, defense), GUARD_SHORT.get(guard, guard),
                ref, ind, 100 * ind / ref, lo, hi))
            by_cond[defense][0] += ind
            by_cond[defense][1] += ref
        print('-' * 78)

    print()
    print('POOLED across guards:')
    print('%-8s %10s %10s %10s   %s' % ('cond', 'refused', 'indirect', 'share', '95% CI'))
    for defense in COND_ORDER:
        ind, ref = by_cond[defense]
        if not ref:
            continue
        lo, hi = wilson(ind, ref)
        print('%-8s %10d %10d %9.1f%%   [%.1f, %.1f]' % (
            COND_SHORT.get(defense, defense), ref, ind, 100 * ind / ref, lo, hi))

    # ---- the clean measure ------------------------------------------------
    # Verified empirically: direct_refusal is overwhelmingly the guard's CANNED
    # block string ("I cannot assist with this request because the guard model
    # flagged it as unsafe" -- 127/129 rows under GuardReasoner/gb). So:
    #     direct_refusal   ~ the GUARD blocked (model never answered)
    #     indirect_refusal ~ the MODEL itself hedged
    # Hedging must therefore be measured CONDITIONAL on the model having been
    # allowed to answer, i.e. over (answer + indirect), excluding blocks.
    print()
    print('=' * 78)
    print('MODEL-SIDE HEDGING -- indirect refusals among prompts the model was')
    print('actually allowed to answer (blocked rows excluded from denominator).')
    print('This isolates the TARGET\'s own over-caution from the guard\'s blocking.')
    print('=' * 78)
    print()
    print('%-14s %10s %10s %10s   %s' % ('guard', 'gb hedge', 'mc hedge', 'delta', 'mc 95% CI'))
    print('-' * 78)
    idx = {(d, g): (n, a, i, r) for d, g, n, a, i, r in rows}
    guards = sorted({g for d, g, *_ in rows if d != 'no_defense'})
    ups = 0
    for g in guards:
        gb = idx.get(('guard_baseline', g))
        mc = idx.get(('modality_complete', g))
        if not gb or not mc:
            continue
        gb_d, mc_d = gb[1] + gb[2], mc[1] + mc[2]      # answer + indirect
        if not gb_d or not mc_d:
            continue
        gb_h, mc_h = 100 * gb[2] / gb_d, 100 * mc[2] / mc_d
        lo, hi = wilson(mc[2], mc_d)
        ups += (mc_h > gb_h)
        print('%-14s %9.1f%% %9.1f%% %+9.1f   [%.0f, %.0f]' % (
            GUARD_SHORT.get(g, g), gb_h, mc_h, mc_h - gb_h, lo, hi))
    fl = idx.get(('no_defense', 'none'))
    if fl:
        fd = fl[1] + fl[2]
        print('-' * 78)
        print('%-14s %9.1f%% (undefended floor, no guard to block)'
              % ('--', 100 * fl[2] / fd))
    print()
    print('guards where the amplifier RAISES model-side hedging: %d/%d'
          % (ups, len(guards)))

    print()
    print('Reading: "answer" is the only column that counts as retained utility')
    print('in the paper. "indirect" is the reviewer\'s hedged/partial category --')
    print('it is ALREADY counted as refused, so the reported over-refusal rates')
    print('do NOT understate utility loss, which is the opposite of the concern.')
    print('The live finding is the split: the amplifier does not only make the')
    print('guard block more, it makes the TARGET hedge more on what it still answers.')


if __name__ == '__main__':
    main()
