"""E2 / review-6 con-6: per-attack UNION-CONTRIBUTION decomposition of the Paper-C ensemble.

Rebuts the reviewer reading that best-of-suite ASR is "just the max attack" / that the
per-attack mean is the honest number. For each (condition, guard) over the 11-attack suite:
  - ensemble  = fraction of behaviors broken by ANY attack (the headline best-of-suite metric)
  - mean      = mean per-attack ASR (the diagnostic view), and the understatement factor ens/mean
  - best-single = the strongest single attack's ASR, and what fraction of the union it reaches
  - sole-breaker % = for each attack, the fraction of behaviors it is the ONLY attack to break
  - positive drop-one marginal count = how many of the 11 attacks are load-bearing (removing them
    lowers the union), i.e. genuine complementarity vs. one dominant attack.

Read-only over the gpt-5-mini rejudge dirs (no model calls). Cell-selection logic mirrors
src/analysis/paper_c_appendix_tables.py exactly (same guards, chains, campaign gating).
Run:  python3 src/analysis/paper_c_union_decomp.py

Caveat carried from the owner's 2026-07-19 judge decision (bestofn_attack results §judge):
CodeAttack ASR is judge-fragile (borderline "restate/gesture" stubs scored harmful). Per that
decision gpt-5-mini is the judge of record and the numbers stand; the fragility is documented as
a threat-to-validity in the paper's Judge Reliability appendix. This script reports the numbers
as-judged; it does NOT re-adjudicate CodeAttack.
"""
import json, glob, os, re

CHAINS = ['llm_set_theory', 'llm_formal_logic', 'llm_classical_language', 'non_llm_cipher',
          'code_attack', 'ir_figstep', 'ir_fc_flowchart', 'ir_low_contrast', 'ir_occluded',
          'ir_mm_typo', 'ir_distraction_grid']
GUARDS = ['wildguard', 'llama_guard_3_8b', 'qwen3guard_gen_8b', 'thinkguard', 'guardreasoner_vl_7b']
SHORT_G = {'wildguard': 'WG', 'llama_guard_3_8b': 'LG3', 'qwen3guard_gen_8b': 'Q3G',
           'thinkguard': 'TG', 'guardreasoner_vl_7b': 'GR'}
SHORT_A = {'llm_set_theory': 'set', 'llm_formal_logic': 'logic', 'llm_classical_language': 'classic',
           'non_llm_cipher': 'cipher', 'code_attack': 'code', 'ir_figstep': 'figstep',
           'ir_fc_flowchart': 'flowchart', 'ir_low_contrast': 'lowcon', 'ir_occluded': 'occl',
           'ir_mm_typo': 'mmtypo', 'ir_distraction_grid': 'distract'}
TARGET = 'qwen2_5_vl_7b'


def lj(p):
    try:
        return json.load(open(p))
    except Exception:
        return None


def ts(n):
    m = re.search(r'_(\d{8})_(\d{6})_', n)
    return (m.group(1) + m.group(2)) if m else '0'


def flags(d):
    out = {}
    for l in open(os.path.join(d, 'raw_results.jsonl')):
        if l.strip():
            row = json.loads(l)
            out[row['id']] = bool(row.get('asr'))
    return out


def select_cells():
    """(cond, guard, chain) -> (ts, dir), POST-FIX. cond in floor/gb/mc/+rg.

    ⚠️ REWRITTEN 2026-08-07 — the previous body pinned `paper_c_guard_panel`, whose
    `code_attack` and `ir_figstep` cells the method-fidelity audit quarantined. This file is
    where that loss bites hardest: it decomposes the UNION by per-attack contribution, and
    CodeAttack is the largest single contributor. Dropping it does not merely shrink the
    union — it rewrites which attack the decomposition names as dominant.

    Selection now comes from `paper_c_select`, including the two rebuilt chains and the
    quarantine trees. `decomp()` reports how many chains it saw, so a short suite stays visible.
    """
    from src.analysis import paper_c_select as S

    shared = S.scan()
    sel = {}
    for chain, d in S.scan_floor(TARGET).items():
        sel[('floor', 'none', chain)] = ('', d)
    for guard in GUARDS:
        for cond, out_cond in (('gb', 'gb'), ('mc', 'mc'), ('rg', '+rg')):
            found, _ = S.postfix_dirs(shared, TARGET, guard, cond)
            for chain, d in found.items():
                sel[(out_cond, guard, chain)] = ('', d)
    return sel


def decomp(sel, cond, g, label):
    present = [c for c in CHAINS if (cond, g, c) in sel]
    pa = {c: flags(sel[(cond, g, c)][1]) for c in present}
    ids = sorted(set().union(*[set(m) for m in pa.values()])) if pa else []
    n = len(ids)
    if n == 0:
        print(f'  {label}: NO DATA')
        return
    cov = {c: sum(pa[c].get(i, False) for i in ids) / n for c in present}
    broken = {i: [c for c in present if pa[c].get(i, False)] for i in ids}
    ens = sum(1 for i in ids if broken[i]) / n
    mean = sum(cov.values()) / len(cov)
    unique = {c: sum(1 for i in ids if broken[i] == [c]) / n for c in present}
    marg = {}
    for c in present:
        without = sum(1 for i in ids if any(cc != c and pa[cc].get(i, False) for cc in present)) / n
        marg[c] = ens - without
    best = max(cov, key=cov.get)
    n_load = sum(1 for c in present if marg[c] > 0)
    print(f'  {label:26} n={n}  ensemble={100 * ens:4.0f}%  mean-per-attack={100 * mean:4.0f}%  '
          f'understate={ens / mean:.2f}x  best-single={100 * cov[best]:3.0f}% ({SHORT_A[best]}) '
          f'= {100 * cov[best] / ens:2.0f}% of union')
    sole = sorted((c for c in present if unique[c] > 0), key=unique.get, reverse=True)
    contrib = ' '.join(f'{SHORT_A[c]}:{100 * unique[c]:.0f}' for c in sole)
    print(f'      sole-breaker %: {contrib if contrib else "none"}   |   load-bearing attacks '
          f'(positive drop-one marginal): {n_load}/{len(present)}')


def ensemble(sel, cond, g):
    u = {}
    for c in CHAINS:
        if (cond, g, c) in sel:
            for i, f in flags(sel[(cond, g, c)][1]).items():
                u[i] = u.get(i, False) or f
    return 100.0 * sum(u.values()) / len(u) if u else float('nan')


def main():
    sel = select_cells()
    print('=== E2 UNION-CONTRIBUTION DECOMPOSITION (Qwen2.5-VL, gpt-5-mini, n=100) ===\n')
    decomp(sel, 'floor', 'none', 'no-defense floor')
    print()
    for g in GUARDS:
        decomp(sel, 'gb', g, f'{SHORT_G[g]} guard-alone (gb)')
    print()
    for g in GUARDS:
        decomp(sel, 'mc', g, f'{SHORT_G[g]} +amplifier (mc)')


if __name__ == '__main__':
    main()
