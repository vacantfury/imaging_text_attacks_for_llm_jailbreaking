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


REJUDGE_GLOB = 'outputs/autoattack_defense/rejudge/harmbench/*gpt-5-mini*'
DIRECT_GLOB = 'outputs/autoattack_defense/defense+evaluate/harmbench/*'
JUDGE = 'gpt-5-mini'


def cells():
    """Yield (cell_dir, source_results, defense, encoding, match_path) for every
    gpt-5-mini-judged harmful cell, from BOTH trees that hold them.

    Most cells were rescored by a `rejudge` pass, so reading the rejudge tree
    alone looks sufficient — but some rounds ran gpt-5-mini as the judge at RUN
    time and therefore never produced a rejudge dir. That silently dropped the
    Qwen reguard arm for LlamaGuard-3 and ThinkGuard (campaign
    paper_c_reguard_5guard, 22 cells, 2026-07-23), which is why the reguard
    layer appeared to cover 3 of the 5 guards rather than all 5. The data was
    on disk and judged the whole time; only this glob was too narrow.

    Where BOTH exist for one cell the rejudge wins: it is the deliberate
    rescoring pass, and the run-time score may predate a judge change.
    """
    covered, out = set(), []
    for d in glob.glob(REJUDGE_GLOB):
        r = lj(os.path.join(d, 'results.json'))
        if not r or r.get('asr') is None:
            continue
        src = (r.get('upstream_ref') or {}).get('source_dir', '')
        s = lj(os.path.join(src, 'results.json'))
        if not s:
            continue
        covered.add(os.path.normpath(src))
        out.append((d, s, r.get('defense'), r.get('encoding'), src))
    for d in glob.glob(DIRECT_GLOB):
        s = lj(os.path.join(d, 'results.json'))
        if not s or s.get('asr') is None or s.get('judge_model') != JUDGE:
            continue
        if os.path.normpath(d) in covered:
            continue
        out.append((d, s, s.get('defense'), s.get('encoding'), d))
    return out


def build(target):
    """(cond, guard, chain) -> (timestamp, dir), POST-FIX. cond in floor/gb/mc/mcrg.

    ⚠️ REWRITTEN 2026-08-07. The previous body pinned `paper_c_guard_panel` (and
    `paper_c_gen2_internvl3`) directly. The method-fidelity audit rebuilt `code_attack` and
    `ir_figstep` under `paper_c_fidelity_rerun` and quarantined the originals, so those two
    chains disappeared from every cell here — and `ens_flags` skipped missing chains without
    comment, so each ENSEMBLE quietly OR-reduced over nine attacks. Every Wilson CI and every
    McNemar p-value this file produced was therefore computed on a different attack suite than
    the paper's headline metric, with no visible symptom.

    Selection now comes from `paper_c_select`; coverage is asserted in `ens_flags`.
    """
    from src.analysis import paper_c_select as S

    sel = {}
    shared = S.scan()
    for chain, d in S.scan_floor(target).items():
        # The floor is guard-independent, but every contrast against it is paired per
        # behavior, so it is stored under each guard's key to keep lookups uniform.
        for g in GUARDS:
            sel[('floor', g, chain)] = ('', d)
    for guard in GUARDS:
        for cond, out_cond in (('gb', 'gb'), ('mc', 'mc'), ('rg', 'mcrg')):
            found, _ = S.postfix_dirs(shared, target, guard, cond)
            for chain, d in found.items():
                sel[(cond_key := out_cond, guard, chain)] = ('', d)
    return sel


def ens_flags(sel, cond, g):
    """OR-reduce the 11 per-attack flags. A SHORT suite raises instead of returning a number.

    This assertion is the whole lesson of the 2026-08-07 sweep: the old version's `continue`
    on a missing chain is what let a nine-attack ensemble be reported as an eleven-attack one.
    """
    u, missing = {}, []
    for c in CHAINS:
        k = (cond, g, c)
        if k not in sel:
            missing.append(c)
            continue
        for i, f in flags(sel[k][1]).items():
            u[i] = u.get(i, False) or f
    if missing:
        raise SystemExit(f'🔴 {cond}/{g}: only {len(CHAINS) - len(missing)}/{len(CHAINS)} '
                         f'chains, missing {missing}. An ensemble over a subset is not the '
                         f'paper\'s metric — do not report it.')
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


def coverage(sel) -> list[str]:
    """Report chains present per (condition, guard) so a missing arm is LOUD.

    Written after a silent one: 22 Qwen reguard cells sat on disk, judged, and
    were invisible because build() read only the rejudge tree — so the reguard
    layer looked like a 3-guard result when it was a 5-guard one. A contrast
    that is absent and a contrast that is non-significant read identically in
    the table below, which is exactly the confusion that hid it. Anything short
    of the full 11-chain suite is now printed, and a fully absent arm is named.
    """
    lines = []
    for cond in ['floor', 'gb', 'mc', 'mcrg']:
        for g in GUARDS:
            n = sum(1 for c in CHAINS if (cond, g, c) in sel)
            if n == len(CHAINS):
                continue
            lines.append(f'  {cond:6}{g:22}{n:>3}/{len(CHAINS)} chains'
                         + ('   <-- ARM ABSENT' if n == 0 else '   <-- PARTIAL'))
    return lines


def main() -> None:
    for target in ['qwen2_5_vl_7b', 'internvl3_8b']:
        sel = build(target)
        gaps = coverage(sel)
        if gaps:
            print(f'\n### {target}: INCOMPLETE CELLS (contrasts below are missing, '
                  f'not non-significant) ###')
            print('\n'.join(gaps))
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
            # floor->* are the PIPELINE-level contrasts the paper's claims rest
            # on; gb->mc is the MARGINAL one (does the amplifier add anything on
            # top of a guard). Reporting both is what separates "the defense
            # works" from "this component of it is what makes it work" — the
            # distinction review-6 con 7 forces, and they answer differently.
            for name, a, b_ in [('floor->gb', 'floor', 'gb'),
                                ('floor->mc', 'floor', 'mc'),
                                ('floor->+rg', 'floor', 'mcrg'),
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
