"""Paper C (AS-3) — rebuild `tab:ablation` (recover vs decode) on post-fix cells.

`tab:ablation` isolates RECOVER from DECODE. Its gb and mc cells are the same cells
Table 1 prints, so once stages 2-4 rebuilt those, this table contradicted Table 1 until
its RECOVER-ONLY arm was re-collected too (stage 5). This rebuilds all three rows from
one consistent selection, so the two tables cannot drift apart again.

Two blocks, matching the paper:

  MAIN (WildGuard, both targets)   gb -> recover-only -> mc, per-attack mean AND ensemble
  CROSS-GUARD (Qwen, 4 guards)     mc -> recover-only, ensemble + paired McNemar

⚠️ THE TEXT-CELL IDENTITY, and why it is not a shortcut. For a TEXT-ONLY guard with
decode off, the recover path and the guard-alone path hand the guard an identical
string -- so for WildGuard the five TEXT attacks' recover-only cells ARE their gb cells,
and only the six IMAGE attacks were ever run. The paper states this. It does NOT hold
for the cross-guard block, because GuardReasoner-VL is multimodal, so that block runs
all eleven. This script encodes the distinction rather than assuming one rule.

Self-validating: the published column is rebuilt too and asserted against what the paper
prints. A selection bug that silently returns a partial ensemble is the failure mode this
whole analysis layer keeps hitting; here it must announce itself.
"""
import json
import glob
import os
import re
from math import comb

TEXT = ['llm_set_theory', 'llm_formal_logic', 'llm_classical_language', 'non_llm_cipher',
        'code_attack']
IMAGE = ['ir_figstep', 'ir_fc_flowchart', 'ir_low_contrast', 'ir_occluded', 'ir_mm_typo',
         'ir_distraction_grid']
CHAINS = TEXT + IMAGE
FIXED = {'code_attack', 'ir_figstep'}
JUDGE = 'gpt-5-mini'
RERUN_GB_MC = 'paper_c_fidelity_rerun'
RERUN_NODECODE = 'paper_c_fidelity_rerun_nodecode'

PANEL = {'qwen2_5_vl_7b': {'gb': {'paper_c_guard_panel'}, 'mc': {'paper_c_guard_panel'}},
         'internvl3_8b': {'gb': {'paper_c_gen2_internvl3'}, 'mc': {'paper_c_gen2_internvl3'}}}
NODECODE = {'qwen2_5_vl_7b': {'paper_c_no_decode', 'paper_c_no_decode_n100'},
            'internvl3_8b': {'paper_c_no_decode_internvl3'}}
CROSS = 'paper_c_crossguard_nodecode'
GUARDS_X = ['qwen3guard_gen_8b', 'thinkguard', 'llama_guard_3_8b', 'guardreasoner_vl_7b']
LABEL = {'qwen3guard_gen_8b': 'Qwen3Guard', 'thinkguard': 'ThinkGuard',
         'llama_guard_3_8b': 'LlamaGuard-3', 'guardreasoner_vl_7b': 'GuardReasoner'}

# What the paper prints today (mean, ens) for the main block, and ens pairs for cross-guard.
PUB_MAIN = {('qwen2_5_vl_7b', 'gb'): (20.1, 75), ('qwen2_5_vl_7b', 'ro'): (8.4, 61),
            ('qwen2_5_vl_7b', 'mc'): (11.2, 72), ('internvl3_8b', 'gb'): (19.6, 81),
            ('internvl3_8b', 'ro'): (10.6, 65), ('internvl3_8b', 'mc'): (8.6, 63)}
PUB_CROSS = {'qwen3guard_gen_8b': (65, 62), 'thinkguard': (77, 70),
             'llama_guard_3_8b': (79, 60), 'guardreasoner_vl_7b': (71, 89)}

ROOTS = ['outputs/autoattack_defense/defense+evaluate/harmbench',
         'outputs/autoattack_defense/rejudge/harmbench',
         'outputs/_quarantine/*/autoattack_defense/defense+evaluate/harmbench',
         'outputs/_quarantine/*/autoattack_defense/rejudge/harmbench']
_QROOTS = sorted(glob.glob('outputs/_quarantine/*'))


def lj(p):
    try:
        return json.load(open(p))
    except Exception:
        return None


def resolve(path):
    if not path or os.path.exists(path + '/results.json'):
        return path
    rel = path[len('outputs/'):] if path.startswith('outputs/') else path
    for q in _QROOTS:
        for cand in (os.path.join(q, rel), os.path.join(q, path)):
            if os.path.exists(cand + '/results.json'):
                return cand
    return path


def ts(name):
    m = re.search(r'_(\d{8})_(\d{6})_', name)
    return (m.group(1) + m.group(2)) if m else '0'


def chain_of(name, src=''):
    hits = [c for c in CHAINS if f'_{c}_' in name or f'_{c}_' in src]
    return max(hits, key=len) if hits else None


def cond_of(defense, dc):
    if defense == 'guard_baseline':
        return 'gb'
    if defense != 'modality_complete':
        return None
    if dc.get('reguard_original'):
        return None
    if dc.get('decode_text') is False:
        return 'ro'
    if dc.get('decode_text') is True and dc.get('decode_style') == 'recover':
        return 'mc'
    return None


def scan():
    sel = {}
    for root in ROOTS:
        for d in glob.glob(root + '/*'):
            r = lj(d + '/results.json')
            if not r or r.get('asr') is None or r.get('judge_model') != JUDGE:
                continue
            src = (r.get('upstream_ref') or {}).get('source_dir', '')
            up = lj(resolve(src) + '/results.json') if src else None
            meta = up if (up and up.get('mode') == 'defense+evaluate') else r
            dc = meta.get('defense_config') or {}
            cond = cond_of(meta.get('defense') or r.get('defense'), dc)
            target = r.get('target_model') or meta.get('target_model')
            chain = chain_of(os.path.basename(d), src)
            camp, guard = meta.get('campaign'), dc.get('guard_model')
            if not (camp and target and cond and guard and chain):
                continue
            k = (camp, target, guard, cond, chain)
            t = ts(os.path.basename(d))
            if k not in sel or t > sel[k][0]:
                sel[k] = (t, d)
    return sel


def flags(d):
    out = {}
    for line in open(os.path.join(d, 'raw_results.jsonl')):
        if line.strip():
            row = json.loads(line)
            out[row['id']] = bool(row.get('asr'))
    return out


def pick(sel, camps, target, guard, cond, chain):
    hit = None
    for c in camps:
        k = (c, target, guard, cond, chain)
        if k in sel and (hit is None or sel[k][0] > hit[0]):
            hit = sel[k]
    return hit[1] if hit else None


def cells(sel, target, guard, cond, postfix, text_identity):
    """-> (per-chain dirs, missing). `text_identity`: recover-only text chains come from gb."""
    out, missing = {}, []
    for ch in CHAINS:
        d = None
        if cond == 'ro':
            if text_identity and ch in TEXT:
                # identity: recover-only == guard-alone for a text attack + text-only guard
                d = (pick(sel, {RERUN_GB_MC}, target, guard, 'gb', ch) if (postfix and ch in FIXED)
                     else pick(sel, PANEL[target]['gb'], target, guard, 'gb', ch))
            elif postfix and ch in FIXED:
                d = pick(sel, {RERUN_NODECODE}, target, guard, 'ro', ch)
            else:
                camps = NODECODE[target] if text_identity else {CROSS}
                d = pick(sel, camps, target, guard, 'ro', ch)
        else:
            d = (pick(sel, {RERUN_GB_MC}, target, guard, cond, ch) if (postfix and ch in FIXED)
                 else pick(sel, PANEL[target][cond], target, guard, cond, ch))
        if d:
            out[ch] = d
        else:
            missing.append(ch)
    return out, missing


def mean_and_ens(percell):
    per, u = [], {}
    for ch, d in percell.items():
        m = flags(d)
        per.append(100.0 * sum(m.values()) / len(m))
        for i, f in m.items():
            u[i] = u.get(i, False) or f
    mean = sum(per) / len(per) if per else float('nan')
    ens = 100.0 * sum(u.values()) / len(u) if u else float('nan')
    return mean, ens, u


def mcnemar(a, b):
    ids = sorted(set(a) & set(b))
    n01 = sum(1 for i in ids if not a[i] and b[i])
    n10 = sum(1 for i in ids if a[i] and not b[i])
    n = n01 + n10
    if n == 0:
        return 1.0
    k = min(n01, n10)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def main() -> None:
    sel = scan()
    print(f'cells indexed: {len(sel)}\n')
    print('=' * 92)
    print('MAIN BLOCK — WildGuard, published -> POST-FIX   (mean / ensemble)')
    print('=' * 92)
    for target in ('qwen2_5_vl_7b', 'internvl3_8b'):
        print(f'\n-- {target} --')
        for cond, name in (('gb', 'guard alone (raw input)'), ('ro', 'recover only (no decode)'),
                           ('mc', 'recover + decode (mc)')):
            pc_pub, miss_pub = cells(sel, target, 'wildguard', cond, False, True)
            pc_fix, miss_fix = cells(sel, target, 'wildguard', cond, True, True)
            mp, ep, _ = mean_and_ens(pc_pub)
            mf, ef, _ = mean_and_ens(pc_fix)
            exp = PUB_MAIN[(target, cond)]
            ok = ('✅' if (ep == ep and round(ep) == exp[1]) else f'❌exp ens {exp[1]}')
            print(f'  {name:26}{mp:6.1f}/{ep:3.0f}  ->{mf:6.1f}/{ef:3.0f}   '
                  f'cov {len(pc_pub)}/{len(pc_fix)}  {ok}')
            if miss_fix:
                print(f'{"":28}⚠ post-fix missing: {", ".join(miss_fix)}')

    print('\n' + '=' * 92)
    print('CROSS-GUARD BLOCK — Qwen, mc -> recover-only (ensemble), published -> POST-FIX')
    print('=' * 92)
    for g in GUARDS_X:
        row = []
        for postfix in (False, True):
            pc_mc, _ = cells(sel, 'qwen2_5_vl_7b', g, 'mc', postfix, False)
            pc_ro, miss = cells(sel, 'qwen2_5_vl_7b', g, 'ro', postfix, False)
            _, e_mc, u_mc = mean_and_ens(pc_mc)
            _, e_ro, u_ro = mean_and_ens(pc_ro)
            row.append((e_mc, e_ro, mcnemar(u_mc, u_ro), len(pc_mc), len(pc_ro), miss))
        (pm, pr, pp, cm1, cr1, _), (fm, fr, fp, cm2, cr2, miss) = row
        exp = PUB_CROSS[g]
        ok = '✅' if (pm == pm and round(pm) == exp[0] and round(pr) == exp[1]) else '❌repro'
        print(f'  {LABEL[g]:15}{pm:4.0f}->{pr:3.0f} (p={pp:.3f})   =>   '
              f'{fm:4.0f}->{fr:3.0f} (p={fp:.3f})   cov {cm2}/{cr2}  {ok}')
        if miss:
            print(f'{"":17}⚠ post-fix missing: {", ".join(miss)}')

    print('\ncov must read 11/11 (cross-guard) — the main block\'s recover-only row takes its five')
    print('TEXT chains from the guard-alone cells by the pipeline identity, not from a separate run.')


if __name__ == '__main__':
    main()
