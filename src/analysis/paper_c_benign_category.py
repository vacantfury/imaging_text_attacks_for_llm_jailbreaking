"""Paper C (AS-3) — per-CATEGORY benign over-refusal.  ($0, stored data.)

cspaper review 3 con 9 asks for per-category OR-Bench results. Producing them surfaced a coverage
fact about our own benign axis that is not currently disclosed anywhere in the paper:

    OR-Bench-Hard carries TEN categories (illegal 527, privacy 199, unethical 125, harmful 106,
    hate 54, sexual 66, violence 66, self-harm 63, deception 72, harassment 41). Our benign slice is
    behaviors 0-99 taken in FILE ORDER, and the file is sorted by category -- so every over-refusal
    number in this paper is measured on exactly TWO categories: deception (72) and harassment (28).

That is a real limitation of the utility axis, not a presentation gap. This script reports the split
so the size of the problem is measured rather than asserted: if the two categories refuse at
similar rates the composition matters little for the reported levels; if they diverge, the levels
are a property of the sample's category mix.

A stratified file already exists (`data/orbench_benign_hard_stratified_300.jsonl`) and would fix
coverage, but re-running the benign grid on it is an experiment with a real cost, not a $0 analysis.

    python -m src.analysis.paper_c_benign_category
"""
from __future__ import annotations

import json
from math import comb

from src.analysis import paper_c_end_to_end as E

PROMPTS = 'data/orbench_benign_hard_prompts.jsonl'
CONDS = [('gb', 'guard alone'), ('mc', 'amplifier'), ('rg', 'amplifier +reguard')]


def categories() -> dict[str, str]:
    out = {}
    for ln in open(PROMPTS, encoding='utf-8'):
        if ln.strip():
            r = json.loads(ln)
            out[str(r['id'])] = r['category']
    return out


def fisher_2x2(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact on [[a,b],[c,d]] -- independent samples, not paired."""
    n = a + b + c + d
    obs = comb(a + b, a) * comb(c + d, c)
    tot = 0.0
    hit = 0.0
    for x in range(0, min(a + b, a + c) + 1):
        y, z = a + b - x, a + c - x
        w = d - (a - x)
        if y < 0 or z < 0 or w < 0:
            continue
        p = comb(a + b, x) * comb(c + d, z)
        tot += p
        if p <= obs:
            hit += p
    return min(1.0, hit / tot) if tot else 1.0


def main() -> None:
    cat = categories()
    bsel = E.scan_benign()
    print(f'benign cells indexed: {len(bsel)}   campaign pinned: {E.BENIGN_CAMPAIGN}\n')
    print('⚠️  COVERAGE: benign slice = behaviors 0-99 in FILE ORDER; the file is category-sorted,')
    print('    so only 2 of OR-Bench-Hard\'s 10 categories appear.\n')
    print(f'{"target":15}{"guard":16}{"condition":22}'
          f'{"deception":>11}{"harassment":>12}{"gap":>7}{"p":>9}')

    gaps = []
    for target in ('qwen2_5_vl_7b', 'internvl3_8b'):
        for g in E.LAB:
            for cond, label in CONDS:
                P = E.pooled_benign(bsel, target, g, cond)
                if P is None:
                    continue
                bucket: dict[str, list[bool]] = {'deception': [], 'harassment': []}
                for (_ch, i), v in P.items():
                    c = cat.get(str(i))
                    if c in bucket:
                        bucket[c].append(bool(v))
                if not all(bucket.values()):
                    continue
                dec, har = bucket['deception'], bucket['harassment']
                rd = 100.0 * sum(dec) / len(dec)
                rh = 100.0 * sum(har) / len(har)
                p = fisher_2x2(sum(dec), len(dec) - sum(dec), sum(har), len(har) - sum(har))
                gaps.append(rh - rd)
                print(f'{target:15}{E.LAB[g]:16}{label:22}{rd:10.1f}%{rh:11.1f}%'
                      f'{rh-rd:+7.1f}{p:9.3f}')

    if gaps:
        gaps.sort()
        n_big = sum(1 for x in gaps if abs(x) >= 10)
        print(f'\n{len(gaps)} condition-cells with both categories present')
        print(f'  harassment - deception gap: {gaps[0]:+.1f} to {gaps[-1]:+.1f} points, '
              f'median {gaps[len(gaps)//2]:+.1f}')
        print(f'  |gap| >= 10 points in {n_big}/{len(gaps)} cells')
        print('\nReading: a LARGE, consistent gap means the reported over-refusal levels are partly')
        print('a property of which categories the slice happens to contain -- which our slice did')
        print('not choose deliberately. A small gap bounds that concern.')

    # ---- the question that actually decides whether this damages the paper ----
    # Levels being category-dependent is survivable if the CONTRASTS the claims rest on
    # reproduce inside each category separately. Check sign agreement per transition.
    print('\n' + '=' * 78)
    print('CONTRAST DIRECTION WITHIN EACH CATEGORY (the claims rest on contrasts, not levels)')
    print('=' * 78)
    print(f'{"target":15}{"guard":16}{"transition":14}'
          f'{"deception":>11}{"harassment":>12}   agree?')
    agree = total = 0
    for target in ('qwen2_5_vl_7b', 'internvl3_8b'):
        for g in E.LAB:
            for c0, c1, label in (('gb', 'mc', 'gb->mc'), ('mc', 'rg', 'mc->+rg')):
                A = E.pooled_benign(bsel, target, g, c0)
                B = E.pooled_benign(bsel, target, g, c1)
                if A is None or B is None:
                    continue
                out = {}
                for name, P in (('a', A), ('b', B)):
                    bk: dict[str, list[bool]] = {'deception': [], 'harassment': []}
                    for (_ch, i), v in P.items():
                        c = cat.get(str(i))
                        if c in bk:
                            bk[c].append(bool(v))
                    out[name] = {k: 100.0 * sum(v) / len(v) for k, v in bk.items() if v}
                if len(out['a']) < 2 or len(out['b']) < 2:
                    continue
                dd = out['b']['deception'] - out['a']['deception']
                dh = out['b']['harassment'] - out['a']['harassment']
                ok = (dd >= 0) == (dh >= 0)
                agree += ok
                total += 1
                print(f'{target:15}{E.LAB[g]:16}{label:14}{dd:+10.1f}{dh:+12.1f}'
                      f'   {"yes" if ok else "NO"}')
    if total:
        print(f'\ndirection agrees in {agree}/{total} contrasts '
              f'({100.0*agree/total:.0f}%) across the two categories')


if __name__ == '__main__':
    main()
