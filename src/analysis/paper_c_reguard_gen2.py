"""Second-target (InternVL3-8B) ensemble/reguard fold-in for Paper C.

Reads the gpt-5-mini rejudge cells of campaign `paper_c_gen2_internvl3` (which ran
floor + gb + mc + mc+reguard x 3 guards x 11 attacks in ONE campaign) and reports,
per guard, the ensemble (best-of-11) ASR for gb / mc / mc+reguard, plus the floor
(no_defense) ensemble and the code_attack per-attack coverage. Mirrors
paper_c_reguard.py (Qwen) but keyed on the single gen2 campaign + target filter.
"""
import json, glob, os, re

CHAINS = ['llm_set_theory', 'llm_formal_logic', 'llm_classical_language', 'non_llm_cipher',
          'code_attack', 'ir_figstep', 'ir_fc_flowchart', 'ir_low_contrast', 'ir_occluded',
          'ir_mm_typo', 'ir_distraction_grid']
GUARDS = ['wildguard', 'qwen3guard_gen_8b', 'guardreasoner_vl_7b']
TARGET = 'internvl3_8b'
CAMPAIGN = 'paper_c_gen2_internvl3'


def lj(p):
    try:
        return json.load(open(p))
    except Exception:
        return None


def ts(n):
    m = re.search(r'_(\d{8})_(\d{6})_', n)
    return (m.group(1) + m.group(2)) if m else '0'


def ids(d):
    out = {}
    for l in open(os.path.join(d, 'raw_results.jsonl')):
        if l.strip():
            row = json.loads(l)
            out[row['id']] = bool(row.get('asr'))
    return out


sel = {}          # (cond, guard, chain) -> (ts, dir)   ; guard='none' for floor
for d in glob.glob('outputs/autoattack_defense/rejudge/harmbench/*gpt-5-mini*'):
    r = lj(d + '/results.json')
    if not r or r.get('asr') is None:
        continue
    src = (r.get('upstream_ref') or {}).get('source_dir', '')
    s = lj(src + '/results.json') or {}
    if s.get('target_model') != TARGET or s.get('campaign') != CAMPAIGN:
        continue
    enc = r.get('encoding')
    chain = enc if enc in CHAINS else next((c for c in CHAINS if f'_{c}_' in src or src.endswith('/' + c)), None)
    if chain is None:
        continue
    dc = s.get('defense_config') or {}
    guard = dc.get('guard_model', 'none')
    defense = r.get('defense') or s.get('defense')
    reguard = bool(dc.get('reguard_original'))
    if defense == 'no_defense':
        cond, gkey = 'floor', 'none'
    elif defense == 'guard_baseline' and guard in GUARDS:
        cond, gkey = 'gb', guard
    elif defense == 'modality_complete' and guard in GUARDS and not reguard \
            and dc.get('decode_text') is True and dc.get('decode_style') == 'recover':
        cond, gkey = 'mc', guard
    elif defense == 'modality_complete' and guard in GUARDS and reguard:
        cond, gkey = 'mcrg', guard
    else:
        continue
    k = (cond, gkey, chain)
    t = ts(os.path.basename(d))
    if k not in sel or t > sel[k][0]:
        sel[k] = (t, d)


def ens(cond, g):
    u = {}
    per = {}
    for c in CHAINS:
        k = (cond, g, c)
        if k not in sel:
            continue
        m = ids(sel[k][1])
        per[c] = 100.0 * sum(m.values()) / len(m)
        for i, f in m.items():
            u[i] = u.get(i, False) or f
    return (100.0 * sum(u.values()) / len(u) if u else float('nan')), per, len(per)


efloor, pfloor, nfloor = ens('floor', 'none')
print(f'TARGET={TARGET}  campaign={CAMPAIGN}')
print(f'FLOOR (no_defense) ensemble ASR: {efloor:.0f}%   (n attacks={nfloor})')
print()
print(f'{"guard":22}{"gb":>6}{"mc":>6}{"mc+rg":>7}   code_attack cov gb/mc/mcrg   n(gb/mc/mcrg)')
print('-' * 92)
for g in GUARDS:
    egb, pgb, ngb = ens('gb', g)
    emc, pmc, nmc = ens('mc', g)
    erg, prg, nrg = ens('mcrg', g)
    code = '%.0f/%.0f/%.0f' % (pgb.get('code_attack', -1), pmc.get('code_attack', -1), prg.get('code_attack', -1))
    print(f'{g:22}{egb:5.0f}%{emc:5.0f}%{erg:6.0f}%   {code:>22}   {ngb}/{nmc}/{nrg}')
print()
print('ENSEMBLE = fraction of 100 behaviors broken by ANY of the 11 attacks (gpt-5-mini judge). Lower=better.')
