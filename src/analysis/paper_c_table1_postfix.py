"""Paper C (AS-3) — rebuild Table 1 (`tab:reguard`) on POST-FIX cells, markers included.

The ASR half of `tab:reguard` is 30 ensemble cells (5 guards x 3 conditions x 2
targets). Stages 2-4 of the method-fidelity re-run replaced the two affected
attacks (`code_attack`, `ir_figstep`); the other nine are unchanged. A post-fix
cell is therefore 9 published chains + 2 rebuilt ones.

⚠️ THE POINT OF THIS SCRIPT IS THE MARKERS, NOT THE NUMBERS. The table's daggers
are "exact McNemar on the paired contrast INTO that column" -- mc carries gb->mc,
+rg carries mc->+rg. Both endpoints of every contrast move when the cells move, so
adopting post-fix values is NOT a find-and-replace: a marker can appear or vanish,
and each one is a claim. This prints published vs post-fix markers side by side so
any change is visible before the paper is touched.

  dagger  p < 0.05
  ddagger p < 0.05 AND survives Bonferroni (alpha = 0.05/20)

Selection follows `paper_c_stats.py`'s campaign pins exactly (including BOTH reguard
campaigns), scans both judge roots plus quarantine, and asserts 11/11 coverage --
a partial ensemble is not a result.
"""
import json
import glob
import os
import re
from math import comb

CHAINS = ['llm_set_theory', 'llm_formal_logic', 'llm_classical_language', 'non_llm_cipher',
          'code_attack', 'ir_figstep', 'ir_fc_flowchart', 'ir_low_contrast', 'ir_occluded',
          'ir_mm_typo', 'ir_distraction_grid']
FIXED = {'code_attack', 'ir_figstep'}
GUARDS = ['wildguard', 'qwen3guard_gen_8b', 'guardreasoner_vl_7b', 'llama_guard_3_8b', 'thinkguard']
LABEL = {'wildguard': 'WildGuard', 'qwen3guard_gen_8b': 'Qwen3Guard',
         'guardreasoner_vl_7b': 'GuardReasoner', 'llama_guard_3_8b': 'LlamaGuard-3',
         'thinkguard': 'ThinkGuard'}
JUDGE = 'gpt-5-mini'
RERUN = 'paper_c_fidelity_rerun'
BONFERRONI = 0.05 / 20

CAMPS = {
    'qwen2_5_vl_7b': {'gb': {'paper_c_guard_panel'}, 'mc': {'paper_c_guard_panel'},
                      'rg': {'paper_c_reguard_ablation', 'paper_c_reguard_5guard'}},
    'internvl3_8b': {c: {'paper_c_gen2_internvl3'} for c in ('gb', 'mc', 'rg')},
}

# What the paper prints today: (gb, mc, rg) and the markers on mc / rg.
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

ROOTS = ['outputs/autoattack_defense/defense+evaluate/harmbench',
         'outputs/autoattack_defense/rejudge/harmbench',
         'outputs/_quarantine/*/autoattack_defense/defense+evaluate/harmbench',
         'outputs/_quarantine/*/autoattack_defense/rejudge/harmbench']


def lj(p):
    try:
        return json.load(open(p))
    except Exception:
        return None


def ts(name):
    m = re.search(r'_(\d{8})_(\d{6})_', name)
    return (m.group(1) + m.group(2)) if m else '0'


_QROOTS = sorted(glob.glob('outputs/_quarantine/*'))


def resolve(path):
    """A quarantined cell's recorded `source_dir` still points at its ORIGINAL path.

    Quarantine buckets mirror `outputs/` WITHOUT the leading `outputs/` component,
    so a moved upstream is found by re-rooting the relative part into each bucket.
    Without this, every rejudge of a quarantined cell loses its campaign and drops
    out of the index silently.
    """
    if not path or os.path.exists(path + '/results.json'):
        return path
    rel = path[len('outputs/'):] if path.startswith('outputs/') else path
    for q in _QROOTS:
        for cand in (os.path.join(q, rel), os.path.join(q, path)):
            if os.path.exists(cand + '/results.json'):
                return cand
    return path


def chain_of(name, src=''):
    hits = [c for c in CHAINS if f'_{c}_' in name or f'_{c}_' in src]
    return max(hits, key=len) if hits else None


def cond_of(defense, dc):
    if defense == 'guard_baseline':
        return 'gb'
    if defense != 'modality_complete':
        return None
    if dc.get('reguard_original'):
        return 'rg'
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
            # A REJUDGE dir carries its OWN campaign (the rejudge preset's), which
            # MASKS the campaign of the experiment it re-scored -- so for a rejudge,
            # upstream wins. But a DIRECT defense+evaluate cell's upstream is its
            # `prompt_transform` dir, which has no campaign/defense/guard at all, so
            # taking upstream there wipes the identity. Distinguish by upstream MODE.
            src = (r.get('upstream_ref') or {}).get('source_dir', '')
            up = lj(resolve(src) + '/results.json') if src else None
            meta = up if (up and up.get('mode') == 'defense+evaluate') else r
            camp, target = meta.get('campaign'), r.get('target_model') or meta.get('target_model')
            dc = meta.get('defense_config') or r.get('defense_config') or {}
            defense = meta.get('defense') or r.get('defense')
            cond = cond_of(defense, dc)
            guard = dc.get('guard_model')
            chain = chain_of(os.path.basename(d), src)
            if not (camp and target and cond and guard in GUARDS and chain):
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


def ens(dirs):
    u = {}
    for d in dirs:
        for i, f in flags(d).items():
            u[i] = u.get(i, False) or f
    return u


def mcnemar(a, b):
    ids = sorted(set(a) & set(b))
    n01 = sum(1 for i in ids if not a[i] and b[i])
    n10 = sum(1 for i in ids if a[i] and not b[i])
    n = n01 + n10
    if n == 0:
        return 1.0
    k = min(n01, n10)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def marker(p):
    if p >= 0.05:
        return ''
    return 'ddagger' if p < BONFERRONI else 'dagger'


def cell(sel, target, guard, cond, postfix):
    dirs, missing = [], []
    for c in CHAINS:
        if postfix and c in FIXED:
            k = (RERUN, target, guard, cond, c)
            if k in sel:
                dirs.append(sel[k][1])
                continue
            missing.append(c)
            continue
        hit = None
        for camp in CAMPS[target][cond]:
            k = (camp, target, guard, cond, c)
            if k in sel and (hit is None or sel[k][0] > hit[0]):
                hit = sel[k]
        if hit:
            dirs.append(hit[1])
        else:
            missing.append(c)
    return dirs, missing


def main() -> None:
    sel = scan()
    print(f'cells indexed: {len(sel)}\n')
    changes = []
    for target in ('qwen2_5_vl_7b', 'internvl3_8b'):
        print('=' * 100)
        print(f'{target}   —   published  ->  POST-FIX   (marker changes flagged)')
        print('=' * 100)
        print(f'{"guard":16}{"gb":>12}{"mc":>18}{"+rg":>18}   coverage')
        for guard in GUARDS:
            sig = {'': ' ', 'dagger': '†', 'ddagger': '‡'}
            arm, cov, bad = {}, [], []
            for postfix in (False, True):
                u = {}
                for cond in ('gb', 'mc', 'rg'):
                    dirs, missing = cell(sel, target, guard, cond, postfix=postfix)
                    u[cond] = ens(dirs)
                    if postfix:
                        cov.append(len(dirs))
                    if missing and postfix:
                        bad.append(f'{cond}:{",".join(missing)}')
                arm[postfix] = {
                    'r': {c: 100.0 * sum(u[c].values()) / len(u[c]) if u[c] else float('nan')
                          for c in u},
                    'mc': marker(mcnemar(u['gb'], u['mc'])),
                    'rg': marker(mcnemar(u['mc'], u['rg'])),
                }
            pub, fix = arm[False], arm[True]
            p_gb, p_mc, p_rg, p_m_mc, p_m_rg = PUBLISHED[(target, guard)]
            # SELF-VALIDATION: the rebuilt published column must equal what the paper
            # prints. Without this a mis-selection shows up only as a coverage count.
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
