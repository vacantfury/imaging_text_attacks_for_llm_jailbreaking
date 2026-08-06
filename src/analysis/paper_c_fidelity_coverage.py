"""Paper C (AS-3) — does ANY paper number still rest on a pre-fix cell?

The method-fidelity audit quarantined every cell produced by a defective attack or
defense. Stages 2-5 re-collected the ones we knew the paper reads. This script is the
CLOSING GATE on that claim: it asks, mechanically, whether every quarantined cell that
a paper-facing analysis actually consumes now has a post-fix replacement.

Method, in three steps:

  1. WHICH CAMPAIGNS DOES THE PAPER READ? Harvested from the analysis layer itself --
     every `paper_c_*` campaign literal appearing in `src/analysis/*.py` -- rather than
     from memory. If a script reads a campaign, that campaign is paper-facing.
  2. WHAT IS QUARANTINED? Every cell under `outputs/_quarantine/`, keyed by the
     experimental identity that makes two cells interchangeable:
     (target, defense, guard, condition, query_source, chain).
  3. IS IT REPLACED? A live cell under a `paper_c_fidelity_rerun*` campaign with the
     SAME identity is a replacement. Anything else is a gap.

A gap in a paper-facing campaign is a defect: some number in the paper is still built
on an implementation we ourselves call a bug. A gap in a non-paper campaign is fine and
is reported separately so the distinction stays visible rather than assumed.

⚠️ This checks IDENTITY coverage, not whether a given number was recomputed. It answers
"do correct cells exist for everything the paper reads", which is the precondition for
the tables being rebuildable -- not "was every table rebuilt".
"""
import json
import glob
import os
import re
import collections

CHAINS = ['llm_set_theory', 'llm_formal_logic', 'llm_classical_language', 'non_llm_cipher',
          'code_attack', 'ir_figstep', 'ir_fc_flowchart', 'ir_low_contrast', 'ir_occluded',
          'ir_mm_typo', 'ir_distraction_grid', 'non_llm_baseline', 'ir_plain', 'ir_camo',
          'non_llm_homoglyph', 'non_llm_artprompt', 'deep_inception', 'llm_semantic_camo']
RERUN_PREFIX = 'paper_c_fidelity_rerun'


def lj(p):
    try:
        return json.load(open(p))
    except Exception:
        return None


def paper_campaigns():
    """Campaigns the analysis layer actually reads — harvested, not remembered."""
    found = set()
    for f in glob.glob('src/analysis/*.py'):
        if os.path.basename(f) == os.path.basename(__file__):
            continue
        txt = open(f, errors='ignore').read()
        found |= set(re.findall(r"['\"](paper_c_[a-z0-9_]+)['\"]", txt))
    return {c for c in found if not c.startswith(RERUN_PREFIX)}


def chain_of(name):
    hits = [c for c in CHAINS if f'_{c}_' in name or name.endswith('_' + c)]
    return max(hits, key=len) if hits else None


def cond_of(defense, dc):
    if defense == 'guard_baseline':
        return 'gb'
    if defense == 'modality_complete':
        if dc.get('reguard_original'):
            return 'rg'
        if dc.get('decode_text') is False:
            return 'recover_only'
        return 'mc'
    return defense


def identity(r, path):
    dc = r.get('defense_config') or {}
    defense = r.get('defense')
    # `query_source` postdates the published ECSO/SemanticSmooth cells, which carry no
    # value but BEHAVE as the knob's default. Comparing a bare '-' against an explicit
    # 'original' invents gaps that are really the same condition.
    arm = dc.get('query_source') or ('original' if defense in ('ecso', 'semantic_smooth') else '-')
    return (r.get('target_model'), defense, dc.get('guard_model'),
            cond_of(defense, dc), arm, chain_of(os.path.basename(path)))


# Quarantine buckets are REASONS. Only these came from the method-fidelity audit
# (`b266892` fixed four encoders, `c42e71a`/`53e589e` two defenses). `oracle_leak` is a
# SEPARATE defect with its own re-run (TODO 18) and must not be scored here, or this
# gate reports another bug's debt as this one's.
FIDELITY_BUCKETS = {'code_attack_appendleft', 'figstep_incomplete', 'semantic_camo_response',
                    'amia_verbatim', 'cider_clipspace'}


def bucket_of(path):
    """Bucket name WITHOUT its date suffix.

    Buckets are named `<reason>_YYYYMMDD`, so matching the reason exactly against a
    raw directory name silently matches nothing -- and a coverage gate that checks
    nothing reports a green. Strip the suffix so the membership test is real.
    """
    m = re.search(r'_quarantine/([^/]+)/', path)
    if not m:
        return '?'
    return re.sub(r'_\d{8}$', '', m.group(1))


def is_fidelity(bucket):
    return bucket in FIDELITY_BUCKETS


def scan(roots, want_rerun):
    out = collections.defaultdict(list)
    for root in roots:
        for d in glob.glob(root + '/*'):
            r = lj(d + '/results.json')
            if not r or r.get('mode') != 'defense+evaluate':
                continue
            camp = r.get('campaign') or ''
            is_rerun = camp.startswith(RERUN_PREFIX)
            if is_rerun != want_rerun:
                continue
            if r.get('asr') is None and want_rerun:
                continue          # a failed replacement is not a replacement
            out[(bucket_of(d), camp) + identity(r, d)].append(d)
    return out


def main() -> None:
    papers = paper_campaigns()
    quarantined = scan(glob.glob('outputs/_quarantine/*/autoattack_defense/**/harmbench'), False)
    replacements = scan(['outputs/autoattack_defense/defense+evaluate/harmbench'], True)
    repl_ids = {k[2:] for k in replacements}

    print(f'paper-facing campaigns found in src/analysis/: {len(papers)}')
    print(f'quarantined cell identities: {len(quarantined)}')
    print(f'post-fix replacement identities: {len(repl_ids)}')

    by_bucket = collections.Counter(k[0] for k in quarantined)
    print('\nquarantined identities by bucket (REASON):')
    for b, n in by_bucket.most_common():
        tag = 'FIDELITY (in scope)' if b in FIDELITY_BUCKETS else 'other defect (out of scope here)'
        print(f'  {b:34}{n:5}   {tag}')
    print()

    gaps = collections.defaultdict(list)
    covered = collections.Counter()
    for key, dirs in quarantined.items():
        bucket, camp, ident = key[0], key[1], key[2:]
        if bucket not in FIDELITY_BUCKETS:
            continue                      # another defect's debt, not this gate's
        if ident in repl_ids:
            covered[camp] += 1
        else:
            gaps[camp].append(ident)

    paper_gaps = {c: v for c, v in gaps.items() if c in papers}
    other_gaps = {c: v for c, v in gaps.items() if c not in papers}

    print('=' * 96)
    print('A. PAPER-FACING campaigns with UNREPLACED quarantined cells  ← these are defects')
    print('=' * 96)
    if not paper_gaps:
        print('  ✅ none — every quarantined cell a paper-facing analysis reads has a post-fix twin.')
    for camp in sorted(paper_gaps, key=lambda c: -len(paper_gaps[c])):
        print(f'\n  🔴 {camp}   unreplaced={len(paper_gaps[camp])}  replaced={covered[camp]}')
        for ident in sorted(paper_gaps[camp], key=str)[:8]:
            t, d, g, c, q, ch = ident
            print(f'       {str(t):15}{str(d):18}{str(g):20}{c:13}{q:9}{ch}')
        if len(paper_gaps[camp]) > 8:
            print(f'       … and {len(paper_gaps[camp]) - 8} more')

    print('\n' + '=' * 96)
    print('B. NON-paper campaigns with unreplaced cells  ← expected; listed so it stays visible')
    print('=' * 96)
    for camp in sorted(other_gaps, key=lambda c: -len(other_gaps[c])):
        print(f'  {camp:46} unreplaced={len(other_gaps[camp])}')
    if not other_gaps:
        print('  (none)')

    print('\n' + '=' * 96)
    print('C. Paper-facing campaigns FULLY covered')
    print('=' * 96)
    for camp in sorted(c for c in covered if c in papers and c not in paper_gaps):
        print(f'  ✅ {camp:46} replaced={covered[camp]}')

    print(f'\nVERDICT: {"✅ no paper number rests on a pre-fix cell" if not paper_gaps else f"🔴 {sum(len(v) for v in paper_gaps.values())} unreplaced identities across {len(paper_gaps)} paper-facing campaign(s)"}')


if __name__ == '__main__':
    main()
