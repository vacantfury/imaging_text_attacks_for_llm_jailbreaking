"""Paper C (AS-3) — rebuild Table 1's undefended FLOOR and its two BASELINES.

`tab:reguard`'s section headers print an undefended floor and two baselines
(ECSO, SemanticSmooth) as 11-attack ensembles over the same eleven attacks as
the guard rows -- so they carry the two encoders `b266892` fixed, exactly as the
guard rows did. This script rebuilds them published-vs-post-fix, and reports the
oracle-leak arm alongside.

Two independent contrasts, deliberately kept apart:

  A. FIDELITY   published(original, pre-fix encoders) -> post-fix(original)
                Reproducing the published column is the check that licenses the
                comparison: it must land on 89/90/80 (Qwen) and 91/91/77 (InternVL3).

  B. ORACLE     post-fix(original) -> post-fix(encoded)          [baselines only]
                `query_source: encoded` is the threat-model-faithful arm (TODO 18).
                The floor has no query_source and does not appear here.

⚠️ TWO SELECTION TRAPS THIS SCRIPT EXISTS TO AVOID -- both cost real time already:

  1. Cells judged INLINE live under `defense+evaluate/`; cells judged by a rejudge
     pass live under `rejudge/`. A script globbing one root silently returns a
     PARTIAL ensemble. Both roots are scanned here.
  2. A missing chain must never be silently skipped. Every ensemble asserts
     11/11 coverage and prints what is missing when it is not.

Quarantined cells are read on purpose for the PUBLISHED side: the published
numbers came from them, so reproducing the published column requires them.
"""
import json
import glob
import os
from math import comb

CHAINS = ['llm_set_theory', 'llm_formal_logic', 'llm_classical_language', 'non_llm_cipher',
          'code_attack', 'ir_figstep', 'ir_fc_flowchart', 'ir_low_contrast', 'ir_occluded',
          'ir_mm_typo', 'ir_distraction_grid']
FIXED = {'code_attack', 'ir_figstep'}
JUDGE = 'gpt-5-mini'
RERUN = 'paper_c_fidelity_rerun'

# Published campaign per (defense, target). The floor is guard-independent.
PUBLISHED = {
    ('no_defense', 'qwen2_5_vl_7b'): 'paper_c_guard_panel_floor',
    ('no_defense', 'internvl3_8b'): 'paper_c_gen2_internvl3',
    ('ecso', 'qwen2_5_vl_7b'): 'paper_c_ecso_compare',
    ('ecso', 'internvl3_8b'): 'paper_c_ecso_compare',
    ('semantic_smooth', 'qwen2_5_vl_7b'): 'paper_c_semanticsmooth_baseline',
    ('semantic_smooth', 'internvl3_8b'): 'paper_c_semanticsmooth_baseline_internvl3',
}
# The 2026-08-05 deployable-arm rerun -- pre-fix on the two fixed attacks.
ORACLE = {'ecso': 'paper_c_oracle_rerun_ecso',
          'semantic_smooth': 'paper_c_oracle_rerun_semantic_smooth'}

# What the paper prints today, for the reproduction check.
PUBLISHED_VALUES = {('no_defense', 'qwen2_5_vl_7b'): 89, ('ecso', 'qwen2_5_vl_7b'): 90,
                    ('semantic_smooth', 'qwen2_5_vl_7b'): 80,
                    ('no_defense', 'internvl3_8b'): 91, ('ecso', 'internvl3_8b'): 91,
                    ('semantic_smooth', 'internvl3_8b'): 77}

ROOTS = ['outputs/autoattack_defense/defense+evaluate/harmbench',
         'outputs/autoattack_defense/rejudge/harmbench',
         'outputs/_quarantine/*/autoattack_defense/defense+evaluate/harmbench',
         'outputs/_quarantine/*/autoattack_defense/rejudge/harmbench']


def lj(path):
    try:
        return json.load(open(path))
    except Exception:
        return None


def ts(name):
    import re
    m = re.search(r'_(\d{8})_(\d{6})_', name)
    return (m.group(1) + m.group(2)) if m else '0'


def chain_of(name, src=''):
    hits = [c for c in CHAINS if f'_{c}_' in name or f'_{c}_' in src]
    return max(hits, key=len) if hits else None       # ir_figstep vs ir_fc_flowchart


def scan():
    """-> {(campaign, defense, target, chain, arm): (ts, dir)}; arm in {'-','original','encoded'}."""
    sel = {}
    for root in ROOTS:
        for d in glob.glob(root + '/*'):
            r = lj(d + '/results.json')
            if not r or r.get('asr') is None or r.get('judge_model') != JUDGE:
                continue
            defense = r.get('defense')
            if defense not in ('no_defense', 'ecso', 'semantic_smooth'):
                continue
            # A rejudge dir carries the judge but not the campaign/config -- those
            # live on the upstream cell it re-scored.
            src = (r.get('upstream_ref') or {}).get('source_dir', '')
            meta = r if r.get('campaign') else (lj(src + '/results.json') or {})
            camp = meta.get('campaign')
            target = r.get('target_model') or meta.get('target_model')
            dc = meta.get('defense_config') or r.get('defense_config') or {}
            # The PUBLISHED baseline cells predate the `query_source` knob and carry
            # no value -- but their behaviour is the knob's default, `original`.
            # Defaulting to '-' here silently hides every published baseline cell.
            arm = '-' if defense == 'no_defense' else (dc.get('query_source') or 'original')
            chain = chain_of(os.path.basename(d), src)
            if not (camp and target and chain):
                continue
            k = (camp, defense, target, chain, arm)
            t = ts(os.path.basename(d))
            if k not in sel or t > sel[k][0]:
                sel[k] = (t, d)
    return sel


def flags(directory):
    out = {}
    for line in open(os.path.join(directory, 'raw_results.jsonl')):
        if line.strip():
            row = json.loads(line)
            out[row['id']] = bool(row.get('asr'))
    return out


def ensemble(dirs):
    u = {}
    for d in dirs:
        for i, f in flags(d).items():
            u[i] = u.get(i, False) or f
    return u


def rate(u):
    return 100.0 * sum(u.values()) / len(u) if u else float('nan')


def mcnemar(a, b):
    ids = sorted(set(a) & set(b))
    n01 = sum(1 for i in ids if not a[i] and b[i])
    n10 = sum(1 for i in ids if a[i] and not b[i])
    n = n01 + n10
    if n == 0:
        return 1.0, n01, n10, len(ids)
    k = min(n01, n10)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n), n01, n10, len(ids)


def collect(sel, camp, defense, target, arm, swap=None):
    """11 chains from `camp`; chains in FIXED taken from `swap` (campaign, arm) if given."""
    dirs, missing = [], []
    for c in CHAINS:
        if swap and c in FIXED:
            k = (swap[0], defense, target, c, swap[1])
        else:
            k = (camp, defense, target, c, arm)
        if k in sel:
            dirs.append(sel[k][1])
        else:
            missing.append(c)
    return dirs, missing


def report(title, a_dirs, a_miss, b_dirs, b_miss, expect=None):
    a, b = ensemble(a_dirs), ensemble(b_dirs)
    ea, eb = rate(a), rate(b)
    p, n01, n10, npair = mcnemar(a, b)
    if not expect or ea != ea:                      # ea != ea  <=> NaN
        ok = '' if not expect else '  ⚠ no published cells'
    else:
        ok = '  ✅ reproduces' if round(ea) == expect else f'  ❌ EXPECTED {expect}'
    print(f'{title:38}{ea:6.0f} -> {eb:5.0f}   cov {len(a_dirs)}/{len(b_dirs)}'
          f'   p={p:.2f}{"*" if p < 0.05 else " "}  ({n01}/{n10}) n={npair}{ok}')
    if a_miss:
        print(f'{"":38}⚠ published missing: {", ".join(a_miss)}')
    if b_miss:
        print(f'{"":38}⚠ post-fix missing: {", ".join(b_miss)}')


def main() -> None:
    sel = scan()
    print(f'cells indexed: {len(sel)}\n')

    print('=' * 104)
    print('A. FIDELITY — published (pre-fix encoders) -> post-fix, `original` arm throughout')
    print('=' * 104)
    for target in ('qwen2_5_vl_7b', 'internvl3_8b'):
        print(f'\n-- {target} --')
        for defense in ('no_defense', 'ecso', 'semantic_smooth'):
            camp = PUBLISHED[(defense, target)]
            arm = '-' if defense == 'no_defense' else 'original'
            a_dirs, a_miss = collect(sel, camp, defense, target, arm)
            b_dirs, b_miss = collect(sel, camp, defense, target, arm,
                                     swap=(RERUN, arm))
            report(defense, a_dirs, a_miss, b_dirs, b_miss,
                   expect=PUBLISHED_VALUES[(defense, target)])

    print('\n' + '=' * 104)
    print('B. ORACLE LEAK — post-fix `original` -> post-fix `encoded` (baselines only; TODO 18)')
    print('=' * 104)
    for target in ('qwen2_5_vl_7b', 'internvl3_8b'):
        print(f'\n-- {target} --')
        for defense in ('ecso', 'semantic_smooth'):
            a_dirs, a_miss = collect(sel, PUBLISHED[(defense, target)], defense, target,
                                     'original', swap=(RERUN, 'original'))
            b_dirs, b_miss = collect(sel, ORACLE[defense], defense, target,
                                     'encoded', swap=(RERUN, 'encoded'))
            report(defense, a_dirs, a_miss, b_dirs, b_miss)

    print('\nENSEMBLE = fraction of 100 behaviors broken by ANY of the 11 attacks. Lower=better.')
    print('cov must read 11/11 — anything less is a PARTIAL ensemble, not a result.')
    print('p from exact paired McNemar on the same behaviors; * = p<0.05.')


if __name__ == '__main__':
    main()
