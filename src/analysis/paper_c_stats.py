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
GUARDS = ['wildguard', 'llama_guard_3_8b', 'qwen3guard_gen_8b', 'thinkguard',
          'guardreasoner_vl_7b']

# Bootstrap over BEHAVIORS (review-6 con 7 asks for "variation over prompts …
# samples"). Resampling the 100 behaviors with replacement gives an uncertainty
# that makes no normal-approximation assumption, unlike the Wilson interval, and
# it is the right unit: the ensemble flag is defined per behavior.
BOOTSTRAP_N = 10000
BOOTSTRAP_SEED = 20260725      # fixed so the reported interval is reproducible


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
        floorcamp = ('paper_c_gen2_internvl3' if target == 'internvl3_8b'
                     else 'paper_c_guard_panel_floor')
        # The undefended floor is guard-independent, but every contrast against
        # it is paired per behavior, so it is stored under each guard's key to
        # keep the downstream lookup uniform.
        if camp == floorcamp and r.get('defense') == 'no_defense':
            for g in GUARDS:
                k0 = ('floor', g, chain)
                t0 = ts(os.path.basename(d))
                if k0 not in sel or t0 > sel[k0][0]:
                    sel[k0] = (t0, d)
            continue
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


def bootstrap_ci(flags_by_id, n_boot=BOOTSTRAP_N, seed=BOOTSTRAP_SEED, alpha=0.05):
    """Percentile CI for an ensemble rate, resampling BEHAVIORS with replacement."""
    import random
    vals = [1 if v else 0 for v in flags_by_id.values()]
    n = len(vals)
    if n == 0:
        return (0.0, 0.0)
    rng = random.Random(seed)
    rates = []
    for _ in range(n_boot):
        rates.append(sum(vals[rng.randrange(n)] for _ in range(n)) / n)
    rates.sort()
    return (100 * rates[int(alpha / 2 * n_boot)],
            100 * rates[min(n_boot - 1, int((1 - alpha / 2) * n_boot))])


def contrast(fa, fb):
    """Paired discordant counts + exact McNemar p for ensemble flags A vs B.

    Returns (b, c, p) where b = broken under A but NOT B (the contrast's gain)
    and c = broken under B but not A (its cost). Reporting b and c — not just p —
    is the point: review-6 con 7 says the paper "does not provide the paired
    contingency counts needed to assess why some contrasts are significant and
    others are not". They were computed all along and simply not printed.
    """
    ids = set(fa) & set(fb)
    b = sum(1 for i in ids if fa[i] and not fb[i])
    c = sum(1 for i in ids if fb[i] and not fa[i])
    return b, c, mcnemar_exact(b, c)


def main() -> None:
    for target in ['qwen2_5_vl_7b', 'internvl3_8b']:
        sel = build(target)
        print(f'\n{"=" * 104}')
        print(f'=== {target} — ensemble ASR: Wilson + behavior-bootstrap CIs ===')
        print(f'{"guard":20}{"floor":>16}{"gb":>16}{"mc":>16}{"+rg":>16}'
              f'   (rate [Wilson] {{bootstrap}})')
        any_row = False
        for g in GUARDS:
            fg = {c: ens_flags(sel, c, g) for c in ['floor', 'gb', 'mc', 'mcrg']}
            if not fg['gb']:
                continue
            any_row = True
            cells = {}
            for c in ['floor', 'gb', 'mc', 'mcrg']:
                n = len(fg[c])
                if not n:
                    cells[c] = '—'
                    continue
                k = sum(fg[c].values())
                lo, hi = wilson(k, n)
                blo, bhi = bootstrap_ci(fg[c])
                cells[c] = f'{100*k/n:.0f} [{lo:.0f}-{hi:.0f}] {{{blo:.0f}-{bhi:.0f}}}'
            print(f'{g:20}' + ''.join(f'{cells[c]:>16}'
                                      for c in ['floor', 'gb', 'mc', 'mcrg']))
        if not any_row:
            continue

        print(f'\n--- PAIRED CONTINGENCY COUNTS (con 7 asked for these explicitly) ---')
        print(f'{"guard":20}{"contrast":14}{"b = A-only":>12}{"c = B-only":>12}'
              f'{"discordant":>12}{"McNemar p":>12}   reading')
        for g in GUARDS:
            fg = {c: ens_flags(sel, c, g) for c in ['floor', 'gb', 'mc', 'mcrg']}
            if not fg['gb']:
                continue
            for name, a, b_ in [('floor->gb', 'floor', 'gb'),
                                ('gb->mc', 'gb', 'mc'),
                                ('mc->+rg', 'mc', 'mcrg')]:
                if not fg[a] or not fg[b_]:
                    continue
                bb, cc, p = contrast(fg[a], fg[b_])
                # A contrast can only be resolved by the behaviors that DISAGREE;
                # a small discordant total is why some contrasts miss significance
                # despite a visible rate gap. That is the reviewer's question.
                note = ('significant' if p < 0.05 else
                        f'n.s. — only {bb + cc} discordant behaviors')
                print(f'{g:20}{name:14}{bb:>12}{cc:>12}{bb + cc:>12}{p:>12.1e}   {note}')

    print(f'\nWilson = normal-approx 95%; {{bootstrap}} = percentile 95% over '
          f'{BOOTSTRAP_N} resamples of the 100 BEHAVIORS (seed {BOOTSTRAP_SEED}).')
    print('McNemar = exact two-sided on paired same-behavior ensemble flags. '
          'b = broken under A only, c = broken under B only;')
    print('only discordant behaviors carry information about the contrast.')


if __name__ == "__main__":
    main()
