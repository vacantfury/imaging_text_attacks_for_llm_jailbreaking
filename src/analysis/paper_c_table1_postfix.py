"""Paper C (AS-3) — rebuild Table 1 (`tab:reguard`) on POST-FIX cells, markers included.

The ASR half of `tab:reguard` is 30 ensemble cells (5 guards x 3 conditions x 2 targets).
Stages 2-4 of the method-fidelity re-run replaced the two affected attacks (`code_attack`,
`ir_figstep`); the other nine are unchanged. A post-fix cell is therefore 9 published chains
+ 2 rebuilt ones.

⚠️ THE POINT OF THIS SCRIPT IS THE MARKERS, NOT THE NUMBERS. The table's daggers are "exact
McNemar on the paired contrast INTO that column" -- mc carries gb->mc, +rg carries mc->+rg.
Both endpoints of every contrast move when the cells move, so adopting post-fix values is NOT
a find-and-replace: a marker can appear or vanish, and each one is a claim. This prints
published vs post-fix markers side by side so any change is visible before the paper is touched.

  dagger  p < 0.05
  ddagger p < 0.05 AND survives Bonferroni (alpha = 0.05/20)

Selection moved to `paper_c_select` (2026-08-07) so that all Paper-C analyses share ONE
selector; this file's output is unchanged by that extraction. See that module's header for
why campaign pinning must be paired with a coverage assertion.
"""
from src.analysis.paper_c_select import (
    GUARDS, LABEL, ens, marker, mcnemar, postfix_dirs, rate, scan,
)

# What the paper printed BEFORE the fidelity re-run: (gb, mc, rg, marker_mc, marker_rg).
# Rebuilding this column and checking it reproduces is the only test that catches a
# mis-selection which would otherwise look like a mere coverage count.
PUBLISHED = {
    ('qwen2_5_vl_7b', 'wildguard'): (75, 72, 43, '', 'ddagger'),
    ('qwen2_5_vl_7b', 'qwen3guard_gen_8b'): (76, 65, 43, '', 'ddagger'),
    ('qwen2_5_vl_7b', 'guardreasoner_vl_7b'): (84, 71, 58, 'ddagger', 'dagger'),
    ('qwen2_5_vl_7b', 'llama_guard_3_8b'): (71, 79, 48, '', 'ddagger'),
    ('qwen2_5_vl_7b', 'thinkguard'): (78, 77, 54, '', 'ddagger'),
    ('internvl3_8b', 'wildguard'): (81, 63, 48, 'ddagger', 'ddagger'),
    ('internvl3_8b', 'qwen3guard_gen_8b'): (81, 69, 56, 'dagger', 'dagger'),
    ('internvl3_8b', 'guardreasoner_vl_7b'): (90, 67, 65, 'ddagger', ''),
    ('internvl3_8b', 'llama_guard_3_8b'): (79, 83, 61, '', 'ddagger'),
    ('internvl3_8b', 'thinkguard'): (82, 77, 59, '', 'ddagger'),
}


def main() -> None:
    sel = scan()
    print(f'cells indexed: {len(sel)}\n')
    changes = []
    sig = {'': ' ', 'dagger': '†', 'ddagger': '‡'}
    for target in ('qwen2_5_vl_7b', 'internvl3_8b'):
        print('=' * 100)
        print(f'{target}   —   published  ->  POST-FIX   (marker changes flagged)')
        print('=' * 100)
        print(f'{"guard":16}{"gb":>12}{"mc":>18}{"+rg":>18}   coverage')
        for guard in GUARDS:
            arm, cov, bad = {}, [], []
            for postfix in (False, True):
                u = {}
                for cond in ('gb', 'mc', 'rg'):
                    found, missing = postfix_dirs(sel, target, guard, cond, postfix=postfix)
                    u[cond] = ens(found.values())
                    if postfix:
                        cov.append(len(found))
                        if missing:
                            bad.append(f'{cond}:{",".join(missing)}')
                arm[postfix] = {
                    'r': {c: rate(u[c]) for c in u},
                    'mc': marker(mcnemar(u['gb'], u['mc'])),
                    'rg': marker(mcnemar(u['mc'], u['rg'])),
                }
            pub, fix = arm[False], arm[True]
            p_gb, p_mc, p_rg, p_m_mc, p_m_rg = PUBLISHED[(target, guard)]
            repro = all(x == x and round(x) == y for x, y in
                        [(pub['r']['gb'], p_gb), (pub['r']['mc'], p_mc), (pub['r']['rg'], p_rg)])
            ok = '✅' if repro else '❌REPRO'
            flag = ''
            if fix['mc'] != pub['mc']:
                flag += f'  ⚠ mc {sig[pub["mc"]]}->{sig[fix["mc"]]}'
                changes.append((target, guard, 'mc', pub['mc'], fix['mc']))
            if fix['rg'] != pub['rg']:
                flag += f'  ⚠ +rg {sig[pub["rg"]]}->{sig[fix["rg"]]}'
                changes.append((target, guard, '+rg', pub['rg'], fix['rg']))
            print(f'{LABEL[guard]:16}{pub["r"]["gb"]:5.0f}->{fix["r"]["gb"]:4.0f} '
                  f'{pub["r"]["mc"]:9.0f}{sig[pub["mc"]]}->{fix["r"]["mc"]:4.0f}{sig[fix["mc"]]} '
                  f'{pub["r"]["rg"]:9.0f}{sig[pub["rg"]]}->{fix["r"]["rg"]:4.0f}{sig[fix["rg"]]}   '
                  f'{"/".join(map(str, cov))} {ok}{flag}')
            if bad:
                print(f'{"":16}⚠ MISSING {"; ".join(bad)}')
        print()
    print('=' * 100)
    if changes:
        print(f'🔴 {len(changes)} MARKER CHANGE(S) — each one is a claim that moves:')
        for t, g, c, old, new in changes:
            print(f'   {t:15}{LABEL[g]:16}{c:5}  {old or "n.s."} -> {new or "n.s."}')
    else:
        print('✅ NO MARKER CHANGES — every significance verdict in Table 1 survives the re-run.')
    print('\ncoverage must read 11/11/11 per guard. † p<0.05 · ‡ also survives Bonferroni (0.05/20).')


if __name__ == '__main__':
    main()
