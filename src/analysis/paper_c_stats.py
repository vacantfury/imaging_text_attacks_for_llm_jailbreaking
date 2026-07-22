"""Statistical significance for the Paper-C ENSEMBLE headline contrasts.

For each guard/target, builds the per-prompt best-of-11 ensemble flag for gb / mc /
mc+reguard, then reports Wilson 95% CIs on each ensemble ASR and exact two-sided
McNemar p-values on the PAIRED within-guard contrasts (gb vs mc, mc vs +rg) — same
100 prompts, so McNemar (not a two-proportion test). Addresses the reviewer's ask
for CIs + paired significance on the gb/mc/+rg comparisons.
"""
import json, glob, os, re, math
from math import comb

CHAINS = ['llm_set_theory', 'llm_formal_logic', 'llm_classical_language', 'non_llm_cipher',
          'code_attack', 'ir_figstep', 'ir_fc_flowchart', 'ir_low_contrast', 'ir_occluded',
          'ir_mm_typo', 'ir_distraction_grid']
GUARDS = ['wildguard', 'qwen3guard_gen_8b', 'guardreasoner_vl_7b']


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


def wilson(k, n, z=1.96):
    if n == 0:
        return (float('nan'), float('nan'))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (100 * (c - h), 100 * (c + h))


def mcnemar_exact(b, c):
    """Exact two-sided McNemar p on discordant counts b, c."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(comb(n, i) for i in range(0, k + 1)) * (0.5 ** n)
    return min(1.0, 2 * p)


def build(target):
    sel = {}
    for d in glob.glob('outputs/autoattack_defense/rejudge/harmbench/*gpt-5-mini*'):
        r = lj(d + '/results.json')
        if not r or r.get('asr') is None:
            continue
        src = (r.get('upstream_ref') or {}).get('source_dir', '')
        s = lj(src + '/results.json') or {}
        if s.get('target_model') != target:
            continue
        enc = r.get('encoding')
        chain = enc if enc in CHAINS else next((c for c in CHAINS if f'_{c}_' in src or src.endswith('/' + c)), None)
        if chain is None:
            continue
        dc = s.get('defense_config') or {}
        guard = dc.get('guard_model', 'none')
        camp = s.get('campaign')
        reg = bool(dc.get('reguard_original'))
        panel = 'paper_c_gen2_internvl3' if target == 'internvl3_8b' else 'paper_c_guard_panel'
        rgcamp = 'paper_c_gen2_internvl3' if target == 'internvl3_8b' else 'paper_c_reguard_ablation'
        if camp == panel and r.get('defense') == 'guard_baseline' and guard in GUARDS:
            cond = 'gb'
        elif camp == panel and r.get('defense') == 'modality_complete' and guard in GUARDS and not reg \
                and dc.get('decode_text') is True and dc.get('decode_style') == 'recover':
            cond = 'mc'
        elif camp == rgcamp and guard in GUARDS and reg:
            cond = 'mcrg'
        else:
            continue
        k = (cond, guard, chain)
        t = ts(os.path.basename(d))
        if k not in sel or t > sel[k][0]:
            sel[k] = (t, d)
    return sel


def ens_flags(sel, cond, g):
    u = {}
    for c in CHAINS:
        k = (cond, g, c)
        if k not in sel:
            continue
        for i, f in flags(sel[k][1]).items():
            u[i] = u.get(i, False) or f
    return u


for target in ['qwen2_5_vl_7b', 'internvl3_8b']:
    sel = build(target)
    print(f'\n=== {target} — ensemble ASR with Wilson 95% CI + paired McNemar ===')
    print(f'{"guard":16}{"gb [CI]":>18}{"mc [CI]":>18}{"+rg [CI]":>18}   gb>mc p    mc>+rg p')
    for g in GUARDS:
        fg = {c: ens_flags(sel, c, g) for c in ['gb', 'mc', 'mcrg']}
        n = len(fg['gb']) or 100
        cells = {}
        for c in ['gb', 'mc', 'mcrg']:
            k = sum(fg[c].values())
            lo, hi = wilson(k, len(fg[c]) or 100)
            cells[c] = f'{100*k/(len(fg[c]) or 100):.0f} [{lo:.0f}-{hi:.0f}]'
        ids = set(fg['gb']) & set(fg['mc']) & set(fg['mcrg'])
        b1 = sum(1 for i in ids if fg['gb'][i] and not fg['mc'][i]); c1 = sum(1 for i in ids if fg['mc'][i] and not fg['gb'][i])
        b2 = sum(1 for i in ids if fg['mc'][i] and not fg['mcrg'][i]); c2 = sum(1 for i in ids if fg['mcrg'][i] and not fg['mc'][i])
        p1 = mcnemar_exact(b1, c1); p2 = mcnemar_exact(b2, c2)
        print(f'{g:16}{cells["gb"]:>18}{cells["mc"]:>18}{cells["mcrg"]:>18}   {p1:.1e}   {p2:.1e}')
print('\nWilson CI = 95%; McNemar = exact two-sided on paired (same-100-prompt) ensemble flags. n=100.')
