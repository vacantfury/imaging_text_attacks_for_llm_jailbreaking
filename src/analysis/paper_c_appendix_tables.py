"""Full 5-guard per-attack + ensemble tables for the Paper-C technical appendix (POST-FIX).

Qwen2.5-VL: per-attack undefended floor, per-attack gb/mc for all FIVE guards, and the
ensemble (best-of-11) gb/mc per guard.

⚠️ WHY THIS FILE NO LONGER HAS ITS OWN SELECTOR (rewritten 2026-08-07).
The previous version globbed ONLY `outputs/autoattack_defense/rejudge/harmbench/*gpt-5-mini*`
and pinned campaign `paper_c_guard_panel`. The method-fidelity audit (`b266892`) rebuilt
`code_attack` and `ir_figstep` under campaign `paper_c_fidelity_rerun` and QUARANTINED the
originals, so those two chains vanished from the index -- and the script printed `nan` for
them while the ENSEMBLE silently reduced over the surviving NINE attacks. That is worse than
a dash: it produced ensemble numbers (WG 58/45 etc.) that look like results and are computed
over a different attack suite than the paper's headline metric. Two of the eleven -- and the
two with the highest floor -- were missing.

So selection is now DELEGATED to `paper_c_table1_postfix`, which is the hardened one: four
scan roots (live + quarantine, both judge trees), `resolve()` for a quarantined cell whose
recorded `source_dir` still points at its pre-move path, per-target campaign pins, and the
rejudge-vs-direct upstream disambiguation. One selector, one set of numbers -- the appendix
and Table 1 cannot drift apart through their builders again.

Coverage is ASSERTED, not hoped for: every printed ensemble is 11/11 or the script says so
loudly. A partial ensemble is not a result.

    python -m src.analysis.paper_c_appendix_tables
"""
from __future__ import annotations

import glob
import os

from src.analysis.paper_c_table1_postfix import (
    CHAINS, FIXED, GUARDS, LABEL, JUDGE, RERUN, ROOTS, CAMPS,
    lj, ts, resolve, chain_of, flags, ens, scan, cell,
)

TARGET = 'qwen2_5_vl_7b'
FLOOR_CAMP = 'paper_c_guard_panel_floor'
# Column order of `tab:app-perattack` as the appendix prints it. This deliberately
# differs from `GUARDS` (Table 1's row order): pasting generated rows under a header
# in a different order silently transposes five columns, which no build error catches.
COLS = ['wildguard', 'llama_guard_3_8b', 'qwen3guard_gen_8b', 'thinkguard',
        'guardreasoner_vl_7b']
SHORT = {'wildguard': 'WG', 'llama_guard_3_8b': 'LG3', 'qwen3guard_gen_8b': 'Q3G',
         'thinkguard': 'TG', 'guardreasoner_vl_7b': 'GR'}
PRETTY = {'llm_set_theory': 'set theory', 'llm_formal_logic': 'formal logic',
          'llm_classical_language': 'classical lang.', 'non_llm_cipher': 'cipher',
          'code_attack': 'CodeAttack', 'ir_figstep': 'FigStep',
          'ir_fc_flowchart': 'flowchart', 'ir_low_contrast': 'low-contrast',
          'ir_occluded': 'occluded', 'ir_mm_typo': 'mm-typo',
          'ir_distraction_grid': 'distraction'}
# Print order matches the appendix table: the two ensemble-residual drivers last.
ORDER = ['llm_set_theory', 'llm_formal_logic', 'llm_classical_language', 'non_llm_cipher',
         'ir_figstep', 'ir_fc_flowchart', 'ir_low_contrast', 'ir_occluded', 'ir_mm_typo',
         'code_attack', 'ir_distraction_grid']


def scan_floor() -> dict:
    """{chain: dir} for the undefended floor — the one condition that has no guard.

    `paper_c_table1_postfix.scan()` requires `guard in GUARDS`, so the floor cells are
    invisible to it by construction; this is the same scan restricted to `no_defense`.
    The FIXED chains take their floor from the fidelity rerun for the same reason every
    other condition does — a post-fix cell is 9 published chains + 2 rebuilt ones, and the
    floor is not exempt.
    """
    best: dict[str, tuple[str, str]] = {}
    for root in ROOTS:
        for d in glob.glob(root + '/*'):
            r = lj(d + '/results.json')
            if not r or r.get('asr') is None or r.get('judge_model') != JUDGE:
                continue
            src = (r.get('upstream_ref') or {}).get('source_dir', '')
            up = lj(resolve(src) + '/results.json') if src else None
            meta = up if (up and up.get('mode') == 'defense+evaluate') else r
            if (meta.get('defense') or r.get('defense')) != 'no_defense':
                continue
            if (r.get('target_model') or meta.get('target_model')) != TARGET:
                continue
            camp = meta.get('campaign')
            chain = chain_of(os.path.basename(d), src)
            if not chain:
                continue
            want = RERUN if chain in FIXED else FLOOR_CAMP
            if camp != want:
                continue
            t = ts(os.path.basename(d))
            if chain not in best or t > best[chain][0]:
                best[chain] = (t, d)
    return {c: v[1] for c, v in best.items()}


def per_chain(sel: dict, guard: str, cond: str) -> dict:
    """{chain: dir} for one (guard, cond), post-fix — `cell()`'s logic, kept per-chain."""
    out = {}
    for c in CHAINS:
        if c in FIXED:
            k = (RERUN, TARGET, guard, cond, c)
            if k in sel:
                out[c] = sel[k][1]
            continue
        hit = None
        for camp in CAMPS[TARGET][cond]:
            k = (camp, TARGET, guard, cond, c)
            if k in sel and (hit is None or sel[k][0] > hit[0]):
                hit = sel[k]
        if hit:
            out[c] = hit[1]
    return out


def rate(d: str | None) -> float | None:
    if not d:
        return None
    m = flags(d)
    return 100.0 * sum(m.values()) / len(m) if m else None


def main() -> None:
    sel = scan()
    floor = scan_floor()
    grid = {(g, cond): per_chain(sel, g, cond) for g in GUARDS for cond in ('gb', 'mc')}

    missing = []
    if len(floor) != len(CHAINS):
        missing.append(('floor', sorted(set(CHAINS) - set(floor))))
    for (g, cond), dirs in grid.items():
        if len(dirs) != len(CHAINS):
            missing.append((f'{SHORT[g]} {cond}', sorted(set(CHAINS) - set(dirs))))
    if missing:
        print('🔴 INCOMPLETE COVERAGE — these cells are NOT 11/11; every number below that')
        print('   depends on them is computed over a SHORTER attack suite than the paper claims:')
        for who, chains in missing:
            print(f'   {who:10} missing {chains}')
        print()

    print('=== ENSEMBLE (best-of-11) ASR, Qwen2.5-VL, gpt-5-mini, POST-FIX ===')
    print(f'{"guard":16}{"gb":>6}{"mc":>6}   coverage')
    for g in GUARDS:
        vals = []
        cov = []
        for cond in ('gb', 'mc'):
            dirs = grid[(g, cond)]
            cov.append(len(dirs))
            u = ens(list(dirs.values()))
            vals.append(100.0 * sum(u.values()) / len(u) if u else float('nan'))
        ok = '✅' if cov == [len(CHAINS)] * 2 else '🔴'
        print(f'{LABEL[g]:16}{vals[0]:5.0f} {vals[1]:5.0f}   {cov[0]}/{cov[1]} {ok}')

    print()
    print('=== PER-ATTACK ASR (gb/mc per guard), Qwen2.5-VL, POST-FIX ===')
    print(f'{"attack":16}{"floor":>6}  ' + '  '.join(f'{SHORT[g]:>9}' for g in GUARDS))
    for c in ORDER:
        fl = rate(floor.get(c))
        cells = []
        for g in GUARDS:
            gb, mc = rate(grid[(g, 'gb')].get(c)), rate(grid[(g, 'mc')].get(c))
            cells.append(f'{"--" if gb is None else format(gb, ".0f")}/'
                         f'{"--" if mc is None else format(mc, ".0f")}')
        star = '  <-- residual driver' if c in ('code_attack', 'ir_distraction_grid') else ''
        print(f'{PRETTY[c]:16}{"--" if fl is None else format(fl, "5.0f")}  '
              + '  '.join(f'{x:>9}' for x in cells) + star)

    print()
    print('LaTeX rows for tab:app-perattack — columns in COLS order:')
    print('Attack & floor & ' + ' & '.join(f'{SHORT[g]} (gb/mc)' for g in COLS) + r' \\')
    for c in ORDER:
        fl = rate(floor.get(c))
        cells = []
        for g in COLS:
            gb, mc = rate(grid[(g, 'gb')].get(c)), rate(grid[(g, 'mc')].get(c))
            cells.append(f'{gb:.0f}/{mc:.0f}' if gb is not None and mc is not None else '--/--')
        bold = c in ('code_attack', 'ir_distraction_grid')
        name = f'\\textbf{{{PRETTY[c]}}}' if bold else PRETTY[c]
        flt = f'\\textbf{{{fl:.0f}}}' if bold and fl is not None else (
            f'{fl:.0f}' if fl is not None else '--')
        body = ' & '.join(f'\\textbf{{{x}}}' if bold else x for x in cells)
        print(f'{name:22} & {flt} & {body} \\\\')


if __name__ == '__main__':
    main()
