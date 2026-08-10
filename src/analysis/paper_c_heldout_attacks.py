"""HELD-OUT ATTACK SUITE: does the paper's conclusion survive on attacks the amplifier never saw?

cspaper review 3 (con 2 / Q3): the held-out replication splits *behaviors* (dev 0-99 vs held-out
100-199), but the amplifier's recover/decode wording was developed against the attack SUITE. A
reviewer can therefore still ask whether the finding is an artifact of the eleven attacks we happened
to build against. Splitting behaviors does not answer that; splitting ATTACKS does.

THE SPLIT IS TEMPORAL, NOT CHOSEN (this is what makes it a real held-out set)
-----------------------------------------------------------------------------
The amplifier landed in `e7937ae` (2026-05-31, "paper_c_defenders_modality_complete_and_joint_verify").
Four of the eleven attacks landed in `3321bda` (2026-07-16,
"add_established_multimodal_attacks_lowcontrast_occluded_mmtypo_distraction") -- six and a half weeks
LATER, imported from the established multimodal-attack literature rather than designed here. The
recover/decode prompts were fixed before those four existed, so they are held out by construction and
not by a split we chose after seeing results. The other seven date to `03d90ef` (2026-05-30).

THE CONFOUND, STATED UP FRONT
-----------------------------
The four late attacks are ALL image-channel. So DEV(7) = 5 text + 2 image and HELD-OUT(4) = 4 image;
any dev-vs-held-out difference could be modality rather than recency. The image-only control below
compares DEV-IMAGE(2) against HELD-OUT-IMAGE(4), which holds modality fixed and varies only recency.
Reporting the temporal split without that control would be the more flattering and less honest
analysis.

WHAT IS AND IS NOT COMPARABLE
-----------------------------
Ensemble ASR is an OR-reduction, so it is MONOTONE in suite membership: a 4-attack ensemble is
mechanically below an 11-attack one. Levels therefore do NOT transfer across subsets and we never
compare them. What transfers is the CONTRAST within a subset -- gb->mc and mc->+rg, paired per
behavior -- which is the form every claim in the paper takes anyway.

This costs nothing to run: it re-reduces per-prompt flags already on disk (the same move as
`app:conditional`), so it is inside the experiment freeze.

    python -m src.analysis.paper_c_heldout_attacks
"""
from __future__ import annotations

from src.analysis import paper_c_select as T

# `3321bda`, 2026-07-16 -- after the amplifier was fixed.
HELD_OUT = ['ir_low_contrast', 'ir_occluded', 'ir_mm_typo', 'ir_distraction_grid']
DEV = [c for c in T.CHAINS if c not in HELD_OUT]
# modality control: the image attacks that predate the amplifier
DEV_IMAGE = ['ir_figstep', 'ir_fc_flowchart']

SUBSETS = [
    ('DEV(7)', DEV),
    ('HELD-OUT(4)', HELD_OUT),
    ('dev-image(2)', DEV_IMAGE),
    ('full(11)', T.CHAINS),
]
TRANSITIONS = [('gb', 'mc', 'gb->mc  amplifier'), ('mc', 'rg', 'mc->+rg re-screen')]


def cell(sel, target, guard, cond, chains):
    """Per-prompt OR over exactly `chains`. Fails loudly on any missing chain."""
    found, missing = T.postfix_dirs(sel, target, guard, cond)
    want = [c for c in chains if c in found]
    gone = [c for c in chains if c not in found]
    if gone:
        raise SystemExit(f'🔴 {target}/{guard}/{cond}: missing {gone} — a partial ensemble '
                         'is not a result.')
    return T.ens([found[c] for c in want])


def main() -> None:
    sel = T.scan()
    print(f'cells indexed: {len(sel)}')
    print(f'DEV(7)      = {DEV}')
    print(f'HELD-OUT(4) = {HELD_OUT}   (all image-channel — see the modality control)\n')

    # ---- the contrasts, per subset -------------------------------------------------
    tally = {}
    for label, chains in SUBSETS:
        print(f'=== {label} — ensemble ASR, paired McNemar '
              f'(‡ survives Bonferroni {T.BONFERRONI:.4f}) ===')
        print(f'{"target":15}{"guard":15}{"gb":>6}{"mc":>6}{"+rg":>6}'
              f'{"d amp":>7}{"p amp":>10}{"  ":2}{"d rescr":>8}{"p rescr":>10}')
        n_amp = n_res = 0
        for target in ('qwen2_5_vl_7b', 'internvl3_8b'):
            for g in T.GUARDS:
                u = {c: cell(sel, target, g, c, chains) for c in ('gb', 'mc', 'rg')}
                r = {c: T.rate(v) for c, v in u.items()}
                p_amp = T.mcnemar(u['gb'], u['mc'])
                p_res = T.mcnemar(u['mc'], u['rg'])
                n_amp += p_amp < T.BONFERRONI
                n_res += p_res < T.BONFERRONI
                print(f'{target:15}{T.LABEL[g]:15}{r["gb"]:6.0f}{r["mc"]:6.0f}{r["rg"]:6.0f}'
                      f'{r["mc"]-r["gb"]:+7.0f}{p_amp:10.2g}{T.marker(p_amp):2}'
                      f'{r["rg"]-r["mc"]:+8.0f}{p_res:10.2g}{T.marker(p_res)}')
        tally[label] = (n_amp, n_res)
        print(f'  -> surviving Bonferroni: amplifier {n_amp}/10, re-screening {n_res}/10\n')

    print('SUMMARY — the paper\'s claim is "no amplifier contrast survives; re-screening does".')
    print(f'{"subset":15}{"amplifier":>12}{"re-screening":>14}   verdict')
    for label, _ in SUBSETS:
        a, r = tally[label]
        ok = 'holds' if a == 0 and r > 0 else ('BREAKS' if a > 0 else 'no re-screen effect')
        print(f'{label:15}{a:>8}/10{r:>11}/10   {ok}')

    # ---- leave-one-attack-out: is any single attack load-bearing? -------------------
    print('\n=== LEAVE-ONE-ATTACK-OUT on the full suite (re-screening contrasts surviving '
          'Bonferroni, /10) ===')
    base_a = base_r = None
    for drop in [None] + T.CHAINS:
        chains = [c for c in T.CHAINS if c != drop]
        n_amp = n_res = 0
        for target in ('qwen2_5_vl_7b', 'internvl3_8b'):
            for g in T.GUARDS:
                u = {c: cell(sel, target, g, c, chains) for c in ('gb', 'mc', 'rg')}
                n_amp += T.mcnemar(u['gb'], u['mc']) < T.BONFERRONI
                n_res += T.mcnemar(u['mc'], u['rg']) < T.BONFERRONI
        if drop is None:
            base_a, base_r = n_amp, n_res
            print(f'{"(none dropped)":26} amplifier {n_amp}/10   re-screening {n_res}/10')
        else:
            flag = '  <-- changes the verdict' if (n_amp > 0) != (base_a > 0) else ''
            print(f'{"drop " + drop:26} amplifier {n_amp}/10   re-screening {n_res}/10{flag}')


def per_attack() -> None:
    """Why one attack governs a union: the amplifier's effect is not uniform in SIGN."""
    sel = T.scan()
    print('\n=== PER-ATTACK ASR (%), averaged over the 10 guard-target pairs ===')
    print(f'{"attack":24}{"gb":>6}{"mc":>6}{"+rg":>6}{"d amp":>7}{"d rescr":>8}')
    for ch in T.CHAINS:
        acc = {c: [] for c in ('gb', 'mc', 'rg')}
        for target in ('qwen2_5_vl_7b', 'internvl3_8b'):
            for g in T.GUARDS:
                for c in acc:
                    f, _ = T.postfix_dirs(sel, target, g, c)
                    if ch in f:
                        acc[c].append(T.rate(T.flags(f[ch])))
        r = {c: sum(v) / len(v) for c, v in acc.items() if v}
        if len(r) == 3:
            star = '   <-- the only attack the amplifier makes WORSE' if r['mc'] > r['gb'] + 5 else ''
            print(f'{ch:24}{r["gb"]:6.0f}{r["mc"]:6.0f}{r["rg"]:6.0f}'
                  f'{r["mc"]-r["gb"]:+7.0f}{r["rg"]-r["mc"]:+8.0f}{star}')


if __name__ == '__main__':
    main()
    per_attack()
