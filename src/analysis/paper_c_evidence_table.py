"""Per-guard-target contrast table for AS-3 — review-1 (2026-08-07) Q2.

The reviewer's ask, verbatim: *"a compact table showing, for every guard-target pair,
matched effect size, confidence interval, exact paired counts, corrected p-value, and
whether the comparison is from the same run"*.

Every column already existed somewhere: `paper_c_stats.py` prints the paired counts and
the exact McNemar p, `paper_c_bootstrap_table.py` bootstraps the rates. What was missing
is (a) the effect size and its CI stated on the PAIRED DIFFERENCE rather than on each
arm separately, (b) the Bonferroni-corrected p next to the raw one, and (c) the same-run
flag — which the paper discloses in prose for some contrasts and not for others, and
which is exactly the disclosure the reviewer says should not be left to prose.

The same-run flag is DERIVED, not asserted: two arms are same-run iff, for all eleven
attacks, both cells carry the same campaign. It is therefore correct by construction
even if selection changes. Note that on both targets the two fidelity-rebuilt chains
(`code_attack`, `ir_figstep`) come from `paper_c_fidelity_rerun` in EVERY arm, so they
never break the flag: the mixture is uniform across the arms of a contrast.

Run:  .venv/bin/python -m src.analysis.paper_c_evidence_table [--latex]
"""
from __future__ import annotations

import random
import sys

from src.analysis import paper_c_select as S

TARGETS = [('qwen2_5_vl_7b', 'Qwen2.5-VL'), ('internvl3_8b', 'InternVL3')]
CONTRASTS = [('gb', 'mc', r'$gb\to mc$', 'amplifier'),
             ('mc', 'rg', r'$mc\to{+}rg$', 'reguard')]
N_BOOT = 10000
SEED = 20260807
# The paper corrects over its twenty headline contrasts (five guards x two targets x two
# transitions); alpha = 0.05/20 is stated in the appendix and reused here unchanged.
N_TESTS = 20


def _campaign_map(sel: dict) -> dict:
    """dir -> campaign, inverted from the selector's own key space."""
    return {d: k[0] for k, (_t, d) in sel.items()}


def _paired_delta_ci(fa: dict, fb: dict, n_boot: int = N_BOOT, seed: int = SEED):
    """Percentile 95% CI on rate(B) - rate(A), resampling BEHAVIORS with replacement.

    Bootstrapping the behavior (not the attack, not the cell) is the right unit: the
    ensemble flag is defined per behavior and the two arms are paired on it, so the
    resample must carry both arms' flags for a behavior together.
    """
    ids = sorted(set(fa) & set(fb))
    n = len(ids)
    if n == 0:
        return float('nan'), float('nan')
    pairs = [(1 if fa[i] else 0, 1 if fb[i] else 0) for i in ids]
    rng = random.Random(seed)
    deltas = []
    for _ in range(n_boot):
        sa = sb = 0
        for _ in range(n):
            a, b = pairs[rng.randrange(n)]
            sa += a
            sb += b
        deltas.append(100 * (sb - sa) / n)
    deltas.sort()
    return deltas[int(0.025 * n_boot)], deltas[min(n_boot - 1, int(0.975 * n_boot))]


def rows() -> list[dict]:
    sel = S.scan()
    camp_of = _campaign_map(sel)
    out = []
    for target, tlabel in TARGETS:
        for guard in S.GUARDS:
            dirs, flags = {}, {}
            for cond in ('gb', 'mc', 'rg'):
                found, missing = S.postfix_dirs(sel, target, guard, cond)
                S.require_full(found, missing, f'{target}/{guard}/{cond}')
                dirs[cond] = found
                flags[cond] = S.ens(found.values())
            for a, b, label, kind in CONTRASTS:
                fa, fb = flags[a], flags[b]
                ra, rb = S.rate(fa), S.rate(fb)
                bb = sum(1 for i in fa if fa[i] and not fb.get(i))
                cc = sum(1 for i in fb if fb[i] and not fa.get(i))
                p = S.mcnemar(fa, fb)
                lo, hi = _paired_delta_ci(fa, fb)
                same = all(camp_of.get(dirs[a][c]) == camp_of.get(dirs[b][c])
                           for c in S.CHAINS)
                out.append(dict(target=tlabel, guard=S.LABEL[guard], kind=kind,
                                contrast=label, a=ra, b=rb, delta=rb - ra,
                                lo=lo, hi=hi, bcount=bb, ccount=cc, p=p,
                                p_corr=min(1.0, p * N_TESTS), same_run=same))
    return out


def _fmt_p(p: float) -> str:
    return '$<$0.001' if p < 0.001 else f'{p:.3f}'


def emit_text(rs: list[dict]) -> None:
    print(f'{"target":11}{"guard":15}{"contrast":12}{"A":>5}{"B":>5}{"delta":>8}'
          f'{"95% CI":>16}{"b":>5}{"c":>5}{"p":>10}{"p x20":>10}  same-run')
    for r in rs:
        print(f'{r["target"]:11}{r["guard"]:15}{r["kind"]:12}{r["a"]:>5.0f}{r["b"]:>5.0f}'
              f'{r["delta"]:>+8.0f}{f"[{r['lo']:+.0f}, {r['hi']:+.0f}]":>16}'
              f'{r["bcount"]:>5}{r["ccount"]:>5}{r["p"]:>10.4f}{r["p_corr"]:>10.4f}'
              f'  {"yes" if r["same_run"] else "NO"}')
    surv = [r for r in rs if r['p_corr'] < 0.05 and r['delta'] < 0]
    print(f'\nBonferroni survivors (alpha=0.05/{N_TESTS}), improvements only: {len(surv)}')
    for kind in ('amplifier', 'reguard'):
        k = [r for r in surv if r['kind'] == kind]
        print(f'  {kind:10} {len(k)}')


def emit_latex(rs: list[dict]) -> None:
    print(r'\begin{table*}[t]')
    print(r'\centering\small')
    print(r'\begin{tabular}{llrrrrrrrrc}')
    print(r'\toprule')
    print(r'Target & Guard & \multicolumn{2}{c}{Ensemble ASR (\%)} & $\Delta$ & '
          r'95\% CI on $\Delta$ & $b$ & $c$ & $p$ & $20p$ & same run \\')
    print(r'\cmidrule(lr){3-4}')
    print(r' & & from & to & (pp) & (paired bootstrap) & & & (exact) & (Bonf.) & \\')
    print(r'\midrule')
    last_t = last_k = None
    for r in rs:
        if r['kind'] != last_k:
            if last_k is not None:
                print(r'\midrule')
            head = ('Amplifier: guard alone $\\to$ recover+decode ($gb\\to mc$)'
                    if r['kind'] == 'amplifier'
                    else 'Re-screening: recover+decode $\\to$ ${+}$reguard ($mc\\to{+}rg$)')
            print(r'\multicolumn{11}{l}{\emph{' + head + r'}} \\')
            last_k, last_t = r['kind'], None
        tcell = r['target'] if r['target'] != last_t else ''
        last_t = r['target']
        star = r'\ddagger' if (r['p_corr'] < 0.05 and r['delta'] < 0) else (
            r'\dagger' if (r['p'] < 0.05 and r['delta'] < 0) else '')
        print(f"{tcell} & {r['guard']} & {r['a']:.0f} & {r['b']:.0f} & "
              f"${r['delta']:+.0f}$$^{{{star}}}$ & "
              f"$[{r['lo']:+.0f}, {r['hi']:+.0f}]$ & {r['bcount']} & {r['ccount']} & "
              f"{_fmt_p(r['p'])} & {_fmt_p(r['p_corr'])} & "
              f"{'yes' if r['same_run'] else r'\\textbf{no}'} \\\\")
    print(r'\bottomrule')
    print(r'\end{tabular}')
    print(r'\caption{\textbf{Every headline contrast, matched and corrected.} '
          r'One row per guard--target pair per transition. $\Delta$ is the paired change '
          r'in eleven-attack ensemble ASR (negative = safer); the interval is a percentile '
          r'bootstrap over the $100$ behaviors, resampling both arms together. $b$ and $c$ '
          r'are the exact discordant counts (behaviors broken under the first arm only, and '
          r'under the second only); $p$ is exact two-sided McNemar on those counts and $20p$ '
          r'is the Bonferroni-corrected value over the $20$ contrasts in this table. '
          r'$\dagger$ marks an uncorrected improvement, $\ddagger$ one surviving correction. '
          r'\emph{same run} states whether both arms come from a single experimental run for '
          r'all eleven attacks --- a cross-run contrast is weaker evidence than a within-run one, '
          r'so we mark it per row rather than describe it in prose. The pattern the table is '
          r'here to make checkable: the surviving improvements are re-screening contrasts.}')
    print(r'\label{tab:app-contrasts}')
    print(r'\end{table*}')



def emit_mcnemar() -> None:
    """`tab:app-mcnemar` — paired counts incl. the pipeline-level floor contrast.

    Rebuilt POST-FIX 2026-08-07: the published body was pre-fidelity-fix (WildGuard/Qwen
    gb->mc printed b=14 c=11 p=0.69 where the post-fix cells give b=13 c=4 p=0.049).
    """
    sel = S.scan()
    print(r'\toprule')
    print(r'Guard & Contrast & $b$ & $c$ & $p$ \\')
    print(r'\midrule')
    for target, tlabel in TARGETS:
        print(r'\multicolumn{5}{l}{\emph{' + tlabel + r'}} \\')
        fl = S.scan_floor(target)
        S.require_full(fl, [c for c in S.CHAINS if c not in fl], f'{target}/floor')
        floor = S.ens(fl.values())
        for guard in S.GUARDS:
            f = {}
            for cond in ('gb', 'mc', 'rg'):
                found, missing = S.postfix_dirs(sel, target, guard, cond)
                S.require_full(found, missing, f'{target}/{guard}/{cond}')
                f[cond] = S.ens(found.values())
            print(r'\multirow{3}{*}{' + S.LABEL[guard] + '}')
            for name, a, b in ((r'floor$\rightarrow$+rg', floor, f['rg']),
                               (r'gb$\rightarrow$mc', f['gb'], f['mc']),
                               (r'mc$\rightarrow$+rg', f['mc'], f['rg'])):
                bb = sum(1 for i in a if a[i] and not b.get(i))
                cc = sum(1 for i in b if b[i] and not a.get(i))
                p = S.mcnemar(a, b)
                if p < 0.001:
                    m, e = f'{p:.1e}'.split('e')
                    ptx = f'${m}{{\\times}}10^{{{int(e)}}}$'
                else:
                    ptx = f'${p:.3f}$'
                print(f' & {name:26} & {bb} & {cc} & {ptx} ' + r'\\')
    print(r'\bottomrule')


if __name__ == '__main__':
    # Group by transition, not by guard: the table's whole point is that the two
    # transitions behave differently, so each must be a contiguous block.
    rs = sorted(rows(), key=lambda r: (r['kind'] != 'amplifier', r['target'] != 'Qwen2.5-VL'))
    if '--mcnemar' in sys.argv:
        emit_mcnemar()
    else:
        (emit_latex if '--latex' in sys.argv else emit_text)(rs)

