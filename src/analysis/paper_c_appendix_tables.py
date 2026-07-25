"""Full 5-guard per-attack + ensemble tables for the Paper-C technical appendix.

Qwen2.5-VL: per-attack floor, and per-attack gb/mc for all FIVE guards, plus the
ensemble (best-of-11) gb/mc per guard. Reuses the same selection logic as
paper_c_reguard.py but over all five panel guards. gpt-5-mini rejudge cells only.
"""
import json, glob, os, re

CHAINS = ['llm_set_theory', 'llm_formal_logic', 'llm_classical_language', 'non_llm_cipher',
          'code_attack', 'ir_figstep', 'ir_fc_flowchart', 'ir_low_contrast', 'ir_occluded',
          'ir_mm_typo', 'ir_distraction_grid']
GUARDS = ['wildguard', 'llama_guard_3_8b', 'qwen3guard_gen_8b', 'thinkguard', 'guardreasoner_vl_7b']
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


def rate(cond, g, c):
    k = (cond, g, c)
    if k not in sel:
        return None
    m = flags(sel[k][1])
    return 100.0 * sum(m.values()) / len(m)


def ens(cond, g):
    u = {}
    for c in CHAINS:
        k = (cond, g, c)
        if k not in sel:
            continue
        for i, f in flags(sel[k][1]).items():
            u[i] = u.get(i, False) or f
    return 100.0 * sum(u.values()) / len(u) if u else float('nan')


def main() -> None:
    global sel
    sel = {}
    for d in glob.glob('outputs/autoattack_defense/rejudge/harmbench/*gpt-5-mini*'):
        r = lj(d + '/results.json')
        if not r or r.get('asr') is None:
            continue
        src = (r.get('upstream_ref') or {}).get('source_dir', '')
        s = lj(src + '/results.json') or {}
        if s.get('target_model') != TARGET:
            continue
        enc = r.get('encoding')
        chain = enc if enc in CHAINS else next((c for c in CHAINS if f'_{c}_' in src or src.endswith('/' + c)), None)
        if chain is None:
            continue
        dc = s.get('defense_config') or {}
        guard = dc.get('guard_model', 'none')
        camp = s.get('campaign')
        reg = bool(dc.get('reguard_original'))
        if camp == 'paper_c_guard_panel_floor' and r.get('defense') == 'no_defense':
            cond, gk = 'floor', 'none'
        elif camp == 'paper_c_guard_panel' and r.get('defense') == 'guard_baseline' and guard in GUARDS:
            cond, gk = 'gb', guard
        elif camp == 'paper_c_guard_panel' and r.get('defense') == 'modality_complete' and guard in GUARDS \
                and dc.get('decode_text') is True and dc.get('decode_style') == 'recover' and not reg:
            cond, gk = 'mc', guard
        else:
            continue
        k = (cond, gk, chain)
        t = ts(os.path.basename(d))
        if k not in sel or t > sel[k][0]:
            sel[k] = (t, d)

    short = {'wildguard': 'WG', 'llama_guard_3_8b': 'LG3', 'qwen3guard_gen_8b': 'Q3G',
             'thinkguard': 'TG', 'guardreasoner_vl_7b': 'GR'}
    print('=== ENSEMBLE (best-of-11) ASR, Qwen2.5-VL, gpt-5-mini ===')
    print(f'{"guard":10}{"gb":>6}{"mc":>6}')
    for g in GUARDS:
        print(f'{short[g]:10}{ens("gb", g):5.0f} {ens("mc", g):5.0f}')
    print()
    print('=== PER-ATTACK ASR (gb/mc per guard), Qwen2.5-VL ===')
    hdr = f'{"attack":22}{"floor":>6}  ' + '  '.join(f'{short[g]:>8}' for g in GUARDS)
    print(hdr)
    for c in CHAINS:
        fl = rate('floor', 'none', c)
        cells = []
        for g in GUARDS:
            gb = rate('gb', g, c)
            mc = rate('mc', g, c)
            cells.append(f'{(gb if gb is not None else float("nan")):3.0f}/{(mc if mc is not None else float("nan")):3.0f}')
        print(f'{c:22}{(fl if fl is not None else float("nan")):5.0f}%  ' + '  '.join(f'{x:>8}' for x in cells))


if __name__ == "__main__":
    main()
