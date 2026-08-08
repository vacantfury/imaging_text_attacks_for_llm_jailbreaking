"""Held-out TEST-SET grid for AS-3, and its comparison against the development set.

The held-out run (campaign `paper_c_heldout`, HarmBench behaviors 100-199) answers the
one objection both cspaper reviews block on: every design decision in the paper was made
while looking at the same 100 behaviors the paper reports. Behaviors 0-99 are therefore
the DEVELOPMENT set and everything the paper prints today is a development number; this
module rebuilds the same grid on data no decision has ever seen.

TWO THINGS THIS MODULE GETS RIGHT THAT ARE EASY TO GET WRONG
------------------------------------------------------------
1. THE TEST IS UNPAIRED. Every other contrast in this paper is McNemar on the SAME
   behaviors under two conditions, which is correct there and wrong here: development
   and held-out are DISJOINT samples of 100 behaviors each. There is no pairing to
   exploit, so the comparison is a two-sample test of independent proportions (Fisher
   exact, two-sided). Using McNemar across the two slices would silently invent a
   pairing between behavior i of one set and behavior i of the other.

2. COVERAGE IS ASSERTED, NOT ASSUMED. Same rule as `paper_c_select.require_full`: an
   ensemble over a subset of the eleven attacks is not this paper's metric. A guard
   whose chunk has not finished is reported as PENDING with its coverage count, never
   as a number computed over the chains that happen to exist.

Run:  .venv/bin/python -m src.analysis.paper_c_heldout [--dev]

`--dev` additionally rebuilds the development arm through the shared selector, so the
two columns print side by side. It needs the development output tree, which lives
locally; on a cluster box run without it and combine afterwards.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from math import comb

from src.analysis import paper_c_select as S

CAMPAIGN = 'paper_c_heldout'
HELDOUT_RANGE = [100, 199]
CONDS = ('gb', 'mc', 'rg')


def scan_heldout(judge: str = S.JUDGE) -> tuple[dict, dict]:
    """({(target, guard, cond, chain): dir}, {(target, chain): dir}) for the floor.

    Selection is by CAMPAIGN plus an explicit prompt_range check. The range check is not
    redundant belt-and-braces: it is what makes a development cell structurally unable to
    enter this arm even if a campaign label were ever reused by mistake.
    """
    sel, floor = {}, {}
    for root in S.ROOTS:
        for d in glob.glob(root + '/*'):
            r = S.lj(d + '/results.json')
            if not r or r.get('judge_model') != judge:
                continue
            if r.get('asr') is None and r.get('refusal_rate') is None:
                continue
            src = (r.get('upstream_ref') or {}).get('source_dir', '')
            up = S.lj(S.resolve(src) + '/results.json') if src else None
            meta = up if (up and up.get('mode') == 'defense+evaluate') else r
            if meta.get('campaign') != CAMPAIGN:
                continue
            if list(r.get('prompt_range') or []) != HELDOUT_RANGE:
                continue
            target = r.get('target_model') or meta.get('target_model')
            chain = S.chain_of(os.path.basename(d), src)
            if not (target and chain):
                continue
            dc = meta.get('defense_config') or r.get('defense_config') or {}
            defense = meta.get('defense') or r.get('defense')
            t = S.ts(os.path.basename(d))
            if defense == 'no_defense':
                k = (target, chain)
                if k not in floor or t > floor[k][0]:
                    floor[k] = (t, d)
                continue
            cond = S.cond_of(defense, dc)
            guard = dc.get('guard_model')
            if not (cond and guard in S.GUARDS):
                continue
            k = (target, guard, cond, chain)
            if k not in sel or t > sel[k][0]:
                sel[k] = (t, d)
    return ({k: v[1] for k, v in sel.items()}, {k: v[1] for k, v in floor.items()})


def _fisher_two_sided(a: int, n1: int, b: int, n2: int) -> float:
    """Exact two-sided Fisher test on the 2x2 [[a, n1-a], [b, n2-b]].

    Written out rather than pulled from scipy because this repo has no scipy dependency
    and the tables are tiny (n=100 per arm). Two-sided by the standard point-probability
    criterion: sum every table at least as extreme as the observed one.
    """
    tot, succ = n1 + n2, a + b

    def p(x: int) -> float:
        return (comb(n1, x) * comb(n2, succ - x)) / comb(tot, succ)

    lo, hi = max(0, succ - n2), min(n1, succ)
    obs = p(a)
    return min(1.0, sum(p(x) for x in range(lo, hi + 1) if p(x) <= obs * (1 + 1e-9)))


def cell(dirs: dict, target: str, guard: str, cond: str) -> tuple[dict | None, list]:
    found, missing = {}, []
    for c in S.CHAINS:
        k = (target, guard, cond, c)
        (found.__setitem__(c, dirs[k]) if k in dirs else missing.append(c))
    return (found if not missing else None), missing


def main() -> int:
    dirs, floor = scan_heldout()
    want_dev = '--dev' in sys.argv
    dev_sel = S.scan() if want_dev else None

    print(f'held-out arm: campaign={CAMPAIGN} range={HELDOUT_RANGE} judge={S.JUDGE}')
    print(f'cells found: {len(dirs)} defended + {len(floor)} floor\n')

    hdr = f'{"target":11}{"guard":15}{"cond":5}{"held-out":>10}{"n":>4}'
    if want_dev:
        hdr += f'{"dev":>7}{"delta":>8}{"p (Fisher)":>12}'
    print(hdr)
    print('-' * len(hdr))

    for target, tl in (('qwen2_5_vl_7b', 'Qwen2.5-VL'), ('internvl3_8b', 'InternVL3')):
        fl = {c: floor[(target, c)] for c in S.CHAINS if (target, c) in floor}
        if len(fl) == len(S.CHAINS):
            f = S.ens(fl.values())
            line = f'{tl:11}{"(floor)":15}{"--":5}{S.rate(f):9.0f}%{len(f):4}'
            if want_dev:
                d_fl = S.scan_floor(target)
                if len(d_fl) == len(S.CHAINS):
                    df = S.ens(d_fl.values())
                    a, b = sum(f.values()), sum(df.values())
                    line += (f'{S.rate(df):6.0f}%{S.rate(f) - S.rate(df):+8.0f}'
                             f'{_fisher_two_sided(a, len(f), b, len(df)):12.3f}')
            print(line)
        elif fl:
            print(f'{tl:11}{"(floor)":15}{"--":5}{"PENDING":>10}{len(fl):>4}/11')

        for guard in S.GUARDS:
            for cond in CONDS:
                found, missing = cell(dirs, target, guard, cond)
                if found is None:
                    if len(missing) < len(S.CHAINS):
                        print(f'{tl:11}{S.LABEL[guard]:15}{cond:5}{"PENDING":>10}'
                              f'{len(S.CHAINS) - len(missing):>4}/11')
                    continue
                f = S.ens(found.values())
                line = f'{tl:11}{S.LABEL[guard]:15}{cond:5}{S.rate(f):9.0f}%{len(f):4}'
                if want_dev:
                    d_found, d_missing = S.postfix_dirs(dev_sel, target, guard, cond)
                    S.require_full(d_found, d_missing, f'DEV {target}/{guard}/{cond}')
                    df = S.ens(d_found.values())
                    a, b = sum(f.values()), sum(df.values())
                    line += (f'{S.rate(df):6.0f}%{S.rate(f) - S.rate(df):+8.0f}'
                             f'{_fisher_two_sided(a, len(f), b, len(df)):12.3f}')
                print(line)
    return 0


if __name__ == '__main__':
    sys.exit(main())
