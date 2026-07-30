"""Paper-C ADAPTIVE SPLIT attacks: per-cell ASR + paired significance.

Builds the two appendix tables for the appendix section *Adaptive Split Attacks* --- the
two attacks we constructed against the reguard conjunction G(d) AND G(r):

  * positional  (`cross_modal_split`, split_ratio 0.3, campaign `paper_c_cross_modal_split`)
  * semantic    (`ir_semantic_split`,                  campaign `paper_c_semantic_split`)

Both were evaluated with a THROWAWAY cluster judge and then re-judged with gpt-5-mini, so
this reads the `rejudge/` tree and follows each cell's `upstream_ref.source_dir` back to the
`defense+evaluate` dir for its condition/guard labels and its stored target responses (the
guard-block count is a text match on the canned refusal in those responses).

Why the PAIRED tests carry the claim rather than the ASR levels: the same 100 behaviors run
in every cell, so McNemar exact on the discordant counts separates three statements the
levels alone conflate --- (i) a text-only guard's protection against a split is NOT
significant (it is blind to the image channel, not weak on it), (ii) the amplifier's gain
over that guard IS, and (iii) the amplifier adds nothing significant for a vision-language
guard that already read the channel. `mc -> mc+rg` is n.s. everywhere here because the
amplifier cells already sit at 1-4%: the paper reports those levels, never a reguard gain.

Canary: any cell with `fallback_parse_count != 0` is VOID and flagged loudly --- the
WildGuard judge failed exactly this way on both attacks (scoring every row a success), so
never read a table row without checking that column.

    python -m src.analysis.paper_c_splits
"""
import json, glob, os, math

REJUDGE_GLOB = 'outputs/autoattack_defense/rejudge/harmbench/*'
BLOCK_TEXT = 'I cannot assist with this request because the guard model flagged it as unsafe.'
CAMPAIGNS = {'paper_c_cross_modal_split': 'positional (rho=0.3)',
             'paper_c_semantic_split': 'semantic'}
GUARD_SHORT = {'wildguard': 'WG', 'guardreasoner_vl_7b': 'GR'}
COND_ORDER = ['floor', 'gb', 'mc', 'mc+rg']


def mcnemar_exact(b: int, c: int) -> float:
    """Exact two-sided McNemar p on discordant counts b, c (binomial, p=0.5)."""
    n = b + c
    if n == 0:
        return 1.0
    obs = abs(b - n / 2)
    tot = sum(math.comb(n, k) for k in range(n + 1)
              if abs(k - n / 2) >= obs - 1e-12)
    return min(1.0, tot / 2 ** n)


def _condition(defense: str, dc: dict) -> str:
    if defense == 'no_defense':
        return 'floor'
    if defense == 'guard_baseline':
        return 'gb'
    if defense == 'modality_complete':
        return 'mc+rg' if dc.get('reguard_original') else 'mc'
    return defense


def _flags(path: str) -> dict:
    out = {}
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            if line.strip():
                row = json.loads(line)
                out[row.get('id')] = 1 if row.get('asr') else 0
    return out


def collect() -> dict:
    """{campaign: {(cond, guard): {'asr','n','fallback','blocks','flags'}}}"""
    out = {c: {} for c in CAMPAIGNS}
    for d in sorted(glob.glob(REJUDGE_GLOB)):
        res = os.path.join(d, 'results.json')
        if not os.path.isfile(res):
            continue
        r = json.load(open(res, encoding='utf-8'))
        up = (r.get('upstream_ref') or {}).get('source_dir', '')
        up_res = os.path.join(up, 'results.json')
        if not os.path.isfile(up_res):
            continue
        s = json.load(open(up_res, encoding='utf-8'))
        camp = s.get('campaign')
        if camp not in CAMPAIGNS:
            continue
        dc = s.get('defense_config') or {}
        cond = _condition(s.get('defense'), dc)
        guard = GUARD_SHORT.get(dc.get('guard_model'), dc.get('guard_model') or '--')
        # guard blocks: canned refusals in the UPSTREAM (target-response) dir
        blocks = 0
        up_raw = os.path.join(up, 'raw_results.jsonl')
        if os.path.isfile(up_raw):
            with open(up_raw, encoding='utf-8') as fh:
                blocks = sum(1 for l in fh
                             if l.strip() and BLOCK_TEXT in str(json.loads(l).get('response') or ''))
        stats = (r.get('eval_stats') or {}).get('HarmBenchEvaluator', {})
        flags = _flags(os.path.join(d, 'raw_results.jsonl'))
        out[camp][(cond, guard)] = {'asr': r.get('asr'), 'n': len(flags), 'blocks': blocks,
                                    'fallback': stats.get('fallback_parse_count'), 'flags': flags}
    return out


def report() -> None:
    data = collect()
    for camp, label in CAMPAIGNS.items():
        cells = data.get(camp) or {}
        print('\n' + '=' * 72)
        print('%s   [%s]' % (label, camp))
        print('=' * 72)
        if not cells:
            print('  no cells found (are the rejudge outputs synced?)')
            continue
        print('  %-6s %-4s %8s %7s %6s %10s' % ('cond', 'guard', 'blocks', 'ASR', 'n', 'fallback'))
        for key in sorted(cells, key=lambda k: (COND_ORDER.index(k[0]) if k[0] in COND_ORDER else 9, k[1])):
            c = cells[key]
            void = '' if c['fallback'] == 0 else '   <-- VOID, do not report'
            print('  %-6s %-4s %6d/100 %7s %6d %10s%s'
                  % (key[0], key[1], c['blocks'], c['asr'], c['n'], c['fallback'], void))

        print('  --- paired contrasts (McNemar exact, same behaviors) ---')
        floor = cells.get(('floor', '--'))
        for guard in ('WG', 'GR'):
            chain = [('floor', floor), ('gb', cells.get(('gb', guard))),
                     ('mc', cells.get(('mc', guard))), ('mc+rg', cells.get(('mc+rg', guard)))]
            for (na, a), (nb, b) in zip(chain, chain[1:]):
                if not a or not b:
                    continue
                ids = sorted(set(a['flags']) & set(b['flags']))
                bb = sum(1 for i in ids if a['flags'][i] and not b['flags'][i])
                cc = sum(1 for i in ids if not a['flags'][i] and b['flags'][i])
                p = mcnemar_exact(bb, cc)
                print('  %-16s %-4s paired n=%-4d b=%-3d c=%-3d p=%-10.3g %s'
                      % ('%s -> %s' % (na, nb), guard, len(ids), bb, cc, p,
                         '*' if p < 0.05 else 'n.s.'))


if __name__ == '__main__':
    report()
