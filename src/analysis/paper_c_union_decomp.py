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


def decomp(sel, cond, g, label, quiet=False):
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
    if not quiet:
        print(f'  {label:26} n={n}  ensemble={100 * ens:4.0f}%  mean-per-attack={100 * mean:4.0f}%  '
              f'understate={ens / mean:.2f}x  best-single={100 * cov[best]:3.0f}% ({SHORT_A[best]}) '
              f'= {100 * cov[best] / ens:2.0f}% of union')
    sole = sorted((c for c in present if unique[c] > 0), key=unique.get, reverse=True)
    contrib = ' '.join(f'{SHORT_A[c]}:{100 * unique[c]:.0f}' for c in sole)
    if not quiet:
        print(f'      sole-breaker %: {contrib if contrib else "none"}   |   load-bearing attacks '
              f'(positive drop-one marginal): {n_load}/{len(present)}')
    return {
        'label': label,
        'ensemble': 100 * ens,
        'mean': 100 * mean,
        'understate': ens / mean,
        'best_share': 100 * cov[best] / ens,
        'best_attack': SHORT_A[best],
        'load_bearing': n_load,
        'sole': {SHORT_A[c]: 100 * unique[c] for c in present},
    }


def ensemble(sel, cond, g):
    u = {}
    for c in CHAINS:
        if (cond, g, c) in sel:
            for i, f in flags(sel[(cond, g, c)][1]).items():
                u[i] = u.get(i, False) or f
    return 100.0 * sum(u.values()) / len(u) if u else float('nan')


def collect(quiet=False):
    """Every reported cell's decomposition, in one pass. Verify and print share this."""
    sel = select_cells()
    floor = decomp(sel, 'floor', 'none', 'no-defense floor', quiet=quiet)
    if not quiet:
        print()
    gb = [decomp(sel, 'gb', g, f'{SHORT_G[g]} guard-alone (gb)', quiet=quiet) for g in GUARDS]
    if not quiet:
        print()
    mc = [decomp(sel, 'mc', g, f'{SHORT_G[g]} +amplifier (mc)', quiet=quiet) for g in GUARDS]
    return floor, gb, mc


# ---------------------------------------------------------------------------
# Drift guard.
#
# These are the ranges the PAPER states in prose, in the main text and in the
# Union-Contribution Decomposition appendix. They were hand-copied once and drifted:
# on 2026-08-21 the main text still claimed 4-7 load-bearing attacks, a 56-71% best-single
# share and a 3.2-6.6x understatement, against the true 4-6, 63-71 and 3.3-6.8, while the
# appendix was correct. Prose is not regenerated by any builder, so it needs an assertion.
# Update BOTH the paper and this block together, never one alone.
# ---------------------------------------------------------------------------
PAPER_CLAIMS = {
    'gb_best_share':   (53, 73),   # "reaches only 53-73% of the union guard-alone"
    'mc_best_share':   (63, 71),   # "63-71% under the amplifier"
    'load_bearing':    (4, 6),     # "four to six of the eleven attacks are load-bearing"
    'understate':      (3.3, 6.8), # "understates the attacker by 3.3x-6.8x"
    'mc_sole_code':    (18, 27),   # "CodeAttack is the sole breaker of 18-27%"
    'mc_sole_distr':   (6, 13),    # "distraction of 6-13%"
    'mc_sole_other_max': 6,        # "no other attack exceeds 6% in any cell"
    # "a 3.3--4.7x gap between the two (mean 3.9 over the undefended floor and the ten
    # guard-alone cells)" -- this one spans BOTH targets, so it is checked separately below.
    'floor_gb_understate': (3.3, 4.7),
    'floor_gb_understate_mean': 3.9,
}


def verify():
    floor, gb, mc = collect(quiet=True)
    fails = []

    def rng(vals, key, decimals=0):
        lo, hi = min(vals), max(vals)
        want_lo, want_hi = PAPER_CLAIMS[key]
        ok = round(lo, decimals) == round(want_lo, decimals) and \
            round(hi, decimals) == round(want_hi, decimals)
        got = f'{lo:.{decimals}f}-{hi:.{decimals}f}'
        want = f'{want_lo}-{want_hi}'
        print(f"  {'OK  ' if ok else 'FAIL'}  {key:<20} paper says {want:<12} data says {got}")
        if not ok:
            fails.append(f'{key}: paper {want}, data {got}')

    rng([c['best_share'] for c in gb], 'gb_best_share')
    rng([c['best_share'] for c in mc], 'mc_best_share')
    rng([c['load_bearing'] for c in gb + mc], 'load_bearing')
    rng([c['understate'] for c in [floor] + gb + mc], 'understate', decimals=1)
    rng([c['sole'].get('code', 0) for c in mc], 'mc_sole_code')
    rng([c['sole'].get('distract', 0) for c in mc], 'mc_sole_distr')

    other = max(v for c in mc for a, v in c['sole'].items() if a not in ('code', 'distract'))
    cap = PAPER_CLAIMS['mc_sole_other_max']
    ok = other <= cap
    print(f"  {'OK  ' if ok else 'FAIL'}  {'mc_sole_other_max':<20} paper says <={cap:<10} "
          f'data says {other:.0f}')
    if not ok:
        fails.append(f'mc_sole_other_max: paper <={cap}, data {other:.0f}')

    # The floor+guard-alone understatement range is stated over BOTH targets, so it needs a
    # second pass with TARGET re-pointed. Verified 2026-08-21: 3.30-4.71, mean 3.93.
    global TARGET
    keep = TARGET
    cells = []
    try:
        for tgt in ('qwen2_5_vl_7b', 'internvl3_8b'):
            TARGET = tgt
            s = select_cells()
            cells.append(decomp(s, 'floor', 'none', f'{tgt} floor', quiet=True))
            cells += [decomp(s, 'gb', g, f'{tgt} {g}', quiet=True) for g in GUARDS]
    finally:
        TARGET = keep
    u = [c['understate'] for c in cells]
    lo, hi, mean = min(u), max(u), sum(u) / len(u)
    want_lo, want_hi = PAPER_CLAIMS['floor_gb_understate']
    want_mean = PAPER_CLAIMS['floor_gb_understate_mean']
    ok = (round(lo, 1) == want_lo and round(hi, 1) == want_hi
          and round(mean, 1) == want_mean and len(cells) == 12)
    print(f"  {'OK  ' if ok else 'FAIL'}  {'floor_gb_understate':<20} "
          f'paper says {want_lo}-{want_hi} m{want_mean}  '
          f'data says {lo:.1f}-{hi:.1f} m{mean:.1f} over {len(cells)} cells (both targets)')
    if not ok:
        fails.append(f'floor_gb_understate: paper {want_lo}-{want_hi} mean {want_mean}, '
                     f'data {lo:.2f}-{hi:.2f} mean {mean:.2f} over {len(cells)} cells')

    print()
    if fails:
        print(f'DRIFT: {len(fails)} of the paper\'s union-decomposition claims no longer match '
              'the stored data.')
        for f in fails:
            print(f'  - {f}')
        raise SystemExit(1)
    print('OK: every union-decomposition range stated in the paper matches the stored data.')


def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'verify':
        print('=== union-decomposition drift guard (paper prose vs stored data) ===\n')
        verify()
        return
    print('=== E2 UNION-CONTRIBUTION DECOMPOSITION (Qwen2.5-VL, gpt-5-mini, n=100) ===\n')
    collect()


if __name__ == '__main__':
    main()
