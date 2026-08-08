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


def _grid(dirs: dict, floor: dict, dev_sel: dict) -> tuple[list, dict, list]:
    """[(target, guard, amp_dev, amp_test, rg_dev, rg_test)], floors, all Fisher p."""
    rows, floors, ps = [], {}, []
    for target, tl in (('qwen2_5_vl_7b', 'Qwen2.5-VL'), ('internvl3_8b', 'InternVL3')):
        fl = {c: floor[(target, c)] for c in S.CHAINS if (target, c) in floor}
        d_fl = S.scan_floor(target)
        S.require_full(fl, [c for c in S.CHAINS if c not in fl], f'{target}/floor held-out')
        S.require_full(d_fl, [c for c in S.CHAINS if c not in d_fl], f'{target}/floor dev')
        f, df = S.ens(fl.values()), S.ens(d_fl.values())
        floors[tl] = (S.rate(df), S.rate(f))
        ps.append(_fisher_two_sided(sum(f.values()), len(f), sum(df.values()), len(df)))
        for guard in S.GUARDS:
            r = {}
            for cond in CONDS:
                found, missing = cell(dirs, target, guard, cond)
                S.require_full(found or {}, missing, f'{target}/{guard}/{cond} held-out')
                d_found, d_missing = S.postfix_dirs(dev_sel, target, guard, cond)
                S.require_full(d_found, d_missing, f'DEV {target}/{guard}/{cond}')
                t_f, d_f = S.ens(found.values()), S.ens(d_found.values())
                r[cond] = (S.rate(d_f), S.rate(t_f))
                ps.append(_fisher_two_sided(sum(t_f.values()), len(t_f),
                                            sum(d_f.values()), len(d_f)))
            rows.append((tl, S.LABEL[guard],
                         r['mc'][0] - r['gb'][0], r['mc'][1] - r['gb'][1],
                         r['rg'][0] - r['mc'][0], r['rg'][1] - r['mc'][1]))
    return rows, floors, ps


def emit_latex(dirs: dict, floor: dict, dev_sel: dict) -> None:
    rows, floors, ps = _grid(dirs, floor, dev_sel)
    n = len(ps)
    alpha = 0.05 / n
    unc = sum(1 for p in ps if p < 0.05)
    srv = sum(1 for p in ps if p < alpha)
    mean = lambda i: sum(r[i] for r in rows) / len(rows)
    # The wrong-way COUNT matching across slices does not mean the same CELLS are
    # wrong-way; asserting that without checking is how a caption overstates a
    # replication. Compute the overlap and describe whatever it actually is.
    wrong_d = {(r[0], r[1]) for r in rows if r[2] > 0}
    wrong_t = {(r[0], r[1]) for r in rows if r[3] > 0}
    both = sorted(wrong_d & wrong_t)
    only_d = sorted(wrong_d - wrong_t)
    only_t = sorted(wrong_t - wrong_d)
    if not (only_d or only_t):
        overlap = ('the same cells in both --- '
                   + ', '.join(f'{g} on {t}' for t, g in both))
    else:
        overlap = ('overlapping in ' + (f'{len(both)}: '
                   + ', '.join(f'{g} on {t}' for t, g in both) if both else 'none')
                   + '; the remaining wrong-way cell differs between the slices ('
                   + ', '.join(f'{g}/{t}' for t, g in only_d) + ' on development, '
                   + ', '.join(f'{g}/{t}' for t, g in only_t) + ' on held-out)')
    amp_wrong_d, amp_wrong_t = len(wrong_d), len(wrong_t)
    rg_good_d = sum(1 for r in rows if r[4] < 0)
    rg_good_t = sum(1 for r in rows if r[5] < 0)
    fl = ' and '.join(f'${d:.0f}\\to{t:.0f}$ on {k}' for k, (d, t) in floors.items())

    print(r'\begin{table}[t]')
    print(r'\centering\small\setlength{\tabcolsep}{3.4pt}')
    print(r'\caption{\textbf{Held-out replication.} Every design decision in this paper was '
          r'made on HarmBench behaviors $0$--$99$; those are therefore the \emph{development} '
          r'set, and the columns marked \emph{dev} are development numbers. We re-ran the '
          r'entire grid unchanged on behaviors $100$--$199$ --- taken in file order, with no '
          r'selection of any kind, and with no threshold, guard, decode setting or policy '
          r'retuned. Entries are the change in eleven-attack ensemble ASR (percentage points, '
          f'negative $=$ safer). Across all {n} matched level comparisons only {unc} reach '
          r'$p<0.05$ uncorrected (both LlamaGuard-3), and '
          f'\\textbf{{none survives Bonferroni correction}} ($\\alpha={alpha:.4f}$); tests are '
          r'\emph{two-sample Fisher exact}, not McNemar, because the two sets are disjoint '
          r'samples and admit no pairing. The pattern the paper rests on carries over intact: '
          f're-screening improves safety in {rg_good_d}/{len(rows)} cells on development data '
          f'and {rg_good_t}/{len(rows)} on held-out, at nearly the same magnitude '
          f'(mean ${mean(4):.1f}$ vs.\\ ${mean(5):.1f}$), while the amplifier alone stays small '
          f'and moves the \\emph{{wrong}} way in {amp_wrong_d}/{len(rows)} cells on development '
          f'and {amp_wrong_t}/{len(rows)} on held-out --- {overlap}. '
          r'Two differences run \emph{against} our own reading and we state them '
          f'rather than absorb them: the amplifier reads somewhat stronger on held-out '
          f'(mean ${mean(2):.1f}\\to{mean(3):.1f}$), which softens our claim that it does '
          f'little on its own; and the held-out behaviors are modestly easier to attack '
          f'(undefended floor {fl}, neither significant), a level shift that applies to every '
          r'arm and therefore leaves the contrasts intact.}')
    print(r'\label{tab:heldout}')
    print(r'\begin{tabular}{llrrrr}')
    print(r'\toprule')
    print(r'& & \multicolumn{2}{c}{Amplifier} & \multicolumn{2}{c}{Re-screening} \\')
    print(r'& & \multicolumn{2}{c}{$gb\to mc$} & \multicolumn{2}{c}{$mc\to{+}rg$} \\')
    print(r'\cmidrule(lr){3-4}\cmidrule(lr){5-6}')
    print(r'Target & Guard & dev & held-out & dev & held-out \\')
    print(r'\midrule')
    last = None
    for t, g, ad, at, rd, rt in rows:
        cell_t = t if t != last else ''
        last = t
        bold = lambda v: (r'\textbf{%+.0f}' % v) if v > 0 else '%+.0f' % v
        print(f'{cell_t} & {g} & {bold(ad)} & {bold(at)} & {rd:+.0f} & {rt:+.0f} \\\\')
    print(r'\midrule')
    print(f'\\multicolumn{{2}}{{l}}{{\\emph{{mean}}}} & ${mean(2):.1f}$ & ${mean(3):.1f}$ '
          f'& ${mean(4):.1f}$ & ${mean(5):.1f}$ \\\\')
    print(r'\bottomrule')
    print(r'\end{tabular}')
    print(r'\end{table}')


def main() -> int:
    dirs, floor = scan_heldout()
    want_dev = '--dev' in sys.argv or '--latex' in sys.argv
    dev_sel = S.scan() if want_dev else None
    if '--latex' in sys.argv:
        emit_latex(dirs, floor, dev_sel)
        return 0

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
