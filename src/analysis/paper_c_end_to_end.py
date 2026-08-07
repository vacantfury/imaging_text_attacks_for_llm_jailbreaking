"""Paper C (AS-3) — the END-TO-END amplifier effect, on BOTH axes.

The paper decomposed the stack into gb->mc (amplifier) and mc->+rg (reguard) and
reported each, but never reported the contrast a deployer actually asks about:
guard alone vs the FULL stack. That omission made the contribution read as marginal
-- a reader scanning Table 1 sees "four of ten, none surviving correction", which is
true of *mc*, and never sees that the end-to-end effect is ten of ten.

⚠️ BOTH AXES OR NEITHER. Reporting the safety gain of a defense without the benign
cost of the SAME transition is the asymmetry this paper criticizes elsewhere, and the
ceiling claim is two-dimensional by construction. So over-refusal is computed here on
the same paired principal, with the same exact McNemar and the same Bonferroni
denominator -- not as a footnote.

⚠️ JUDGE PROVENANCE, and why the benign side uses a different campaign. The harm side
takes r1 panel cells (+ the fidelity reruns for the two fixed attacks). The benign
side CANNOT: r1's benign guard cells were judged by gpt-5-nano, and the paper's
decided main judge is gpt-5-mini, so the only complete gpt-5-mini benign guard grid
is `paper_c_replicate_r2`. Mixing judges across the two axes of one claim would be a
worse error than crossing campaigns, so the campaign is pinned and named in the
output rather than silently chosen.
"""
import json
import glob
import os
import sys
from math import comb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paper_c_table1_postfix as T           # noqa: E402  (harm-side selection, already validated)

CHANNELS = ['non_llm_baseline', 'ir_plain']
BENIGN_CAMPAIGN = 'paper_c_replicate_r2'
JUDGE = 'gpt-5-mini'
BONF = 0.05 / 20
LAB = {'wildguard': 'WildGuard', 'qwen3guard_gen_8b': 'Qwen3Guard',
       'guardreasoner_vl_7b': 'GuardReasoner', 'llama_guard_3_8b': 'LlamaGuard-3',
       'thinkguard': 'ThinkGuard'}


def cond_of(defense, dc):
    if defense == 'guard_baseline':
        return 'gb'
    if defense == 'modality_complete':
        if dc.get('reguard_original'):
            return 'rg'
        return 'ro' if dc.get('decode_text') is False else 'mc'
    return defense


def refusal_flags(d):
    out = {}
    for line in open(os.path.join(d, 'raw_results.jsonl')):
        if line.strip():
            row = json.loads(line)
            out[row['id']] = bool(row.get('refusal'))
    return out


def mcnemar(a, b):
    ids = sorted(set(a) & set(b))
    n01 = sum(1 for i in ids if not a[i] and b[i])
    n10 = sum(1 for i in ids if a[i] and not b[i])
    n = n01 + n10
    if n == 0:
        return 1.0
    k = min(n01, n10)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def scan_benign():
    sel = {}
    for root in ('outputs/autoattack_defense/defense+evaluate/orbench_benign_hard',
                 'outputs/autoattack_defense/rejudge/orbench_benign_hard'):
        for d in glob.glob(root + '/*'):
            try:
                r = json.load(open(d + '/results.json'))
            except Exception:
                continue
            if r.get('refusal_rate') is None or r.get('judge_model') != JUDGE:
                continue
            src = (r.get('upstream_ref') or {}).get('source_dir', '')
            meta = r if r.get('campaign') else (
                json.load(open(src + '/results.json'))
                if os.path.exists(src + '/results.json') else {})
            if meta.get('campaign') != BENIGN_CAMPAIGN:
                continue
            dc = meta.get('defense_config') or {}
            guard = dc.get('guard_model')
            if guard not in LAB:
                continue
            hay = src + ' ' + os.path.basename(d)
            channel = next((c for c in CHANNELS if c in hay), None)
            if channel:
                sel[(r.get('target_model'), guard,
                     cond_of(meta.get('defense'), dc), channel)] = d
    return sel


def pooled_benign(bsel, target, guard, cond):
    """Both benign channels pooled into ONE paired principal (200 prompts)."""
    out = {}
    for ch in CHANNELS:
        d = bsel.get((target, guard, cond, ch))
        if not d:
            return None
        for i, v in refusal_flags(d).items():
            out[(ch, i)] = v
    return out


def mark(p):
    return '‡' if p < BONF else ('†' if p < 0.05 else '')


def main() -> None:
    sel, bsel = T.scan(), scan_benign()
    print(f'harm cells indexed: {len(sel)}   benign cells indexed: {len(bsel)}')
    print(f'benign campaign pinned: {BENIGN_CAMPAIGN} (judge {JUDGE}) — see module docstring\n')
    print('END-TO-END: guard alone (gb) vs FULL STACK (+rg), 11-attack ensemble / pooled benign')
    print(f'{"target":15}{"guard":15}{"ASR gb":>7}{"+rg":>5}{"d":>5}{"p":>10}{"m":>2}'
          f'{"| ref gb":>9}{"+rg":>5}{"d":>5}{"p":>10}{"m":>2}')
    n_asr = n_asr_b = n_ref = n_ref_b = 0
    for target in ('qwen2_5_vl_7b', 'internvl3_8b'):
        for g in T.GUARDS:
            dg, mg = T.cell(sel, target, g, 'gb', True)
            dr, mr = T.cell(sel, target, g, 'rg', True)
            if mg or mr:
                print(f'{target:15}{LAB[g]:15}  ⚠ partial coverage {11-len(mg)}/{11-len(mr)}')
                continue
            a, b = T.ens(dg), T.ens(dr)
            ra, rb = 100.0 * sum(a.values()) / len(a), 100.0 * sum(b.values()) / len(b)
            pa = T.mcnemar(a, b)
            A, B = pooled_benign(bsel, target, g, 'gb'), pooled_benign(bsel, target, g, 'rg')
            if A is None or B is None:
                print(f'{target:15}{LAB[g]:15}  ⚠ benign cells missing')
                continue
            fa, fb = 100.0 * sum(A.values()) / len(A), 100.0 * sum(B.values()) / len(B)
            pr = mcnemar(A, B)
            n_asr += pa < 0.05; n_asr_b += pa < BONF
            n_ref += pr < 0.05; n_ref_b += pr < BONF
            print(f'{target:15}{LAB[g]:15}{ra:7.0f}{rb:5.0f}{rb-ra:+5.0f}{pa:10.1e}{mark(pa):>2}'
                  f'{fa:9.0f}{fb:5.0f}{fb-fa:+5.0f}{pr:10.1e}{mark(pr):>2}')
    print(f'\nASR significant {n_asr}/10 (Bonferroni {n_asr_b}/10) · '
          f'over-refusal significant {n_ref}/10 (Bonferroni {n_ref_b}/10)')
    print('Lower ASR is better; HIGHER over-refusal is worse — the two columns are the')
    print('two axes of the frontier, and a gain on one is only meaningful beside the other.')


if __name__ == '__main__':
    main()
