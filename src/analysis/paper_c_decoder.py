"""Paper C — decoder disentanglement (review-8 Q3).

Is the `+rg` residual ceiling fundamental, or an artifact of a 7B target DECODING ITS
OWN attack? The amplifier does two separable things and only one is in question:

  recover : image -> text.  Multimodal, needs a VLM.  UNCHANGED (stays on the 7B).
  decode  : encoded text -> plaintext.  TEXT-ONLY, so it can move to a large text
            model while everything else is held identical to Tables 1-2.

That separation is what makes the result attributable: target, guards, 11-attack suite,
`+rg` condition, gpt-5-mini judge and n all match the published run, so a difference is
decoder capacity and nothing else.

CHANNEL SPLIT is the diagnostic. Every attack is decoded, so a decode-side gain should
appear on both channels; an IMAGE-side gain in particular can only arrive by decoding
the recovered transcription better, never by better OCR (recover did not change). A gain
confined to text would instead mean recovery is now the binding constraint.

TWO TREES, ONE ARITHMETIC. The published baseline lives in the gpt-5-mini `rejudge/`
tree; a new decoder arm lives in `defense+evaluate/` under its own campaign. Both are
read here with the same reduction so the numbers are comparable.

Usage:
    python -m src.analysis.paper_c_decoder                     # baseline, rejudge tree
    python -m src.analysis.paper_c_decoder paper_c_decoder_r1  # an arm, live tree
"""
from __future__ import annotations

import glob
import json
import math
import os
import sys

from .paper_c_conditional import (CHAINS, IMAGE_CHAINS, TEXT_CHAINS, _flags, _lj,
                                  collect_harm)

GUARDS = ['wildguard', 'guardreasoner_vl_7b']
# POST-FIX tab:reguard, Qwen2.5-VL `+rg` column — the like-for-like baseline.
# GuardReasoner was 58 pre-audit and rebuilds to 63; WildGuard is unchanged at 43.
PUBLISHED = {'wildguard': (43, 84), 'guardreasoner_vl_7b': (63, 87)}  # (ASR, over-ref.)

# ⚠️ THE ARM IS INCOMPLETE, and the contrast must be matched to say so (2026-08-07).
# `paper_c_decoder_r1` ran on 2026-07-28, BEFORE `b266892` rebuilt the two fixed encoders,
# so its `code_attack` and `ir_figstep` cells are quarantined and no post-fix replacements
# exist. The baseline's do. OR-reducing each side over "whatever it has" therefore compared
# an 11-attack baseline against a 9--10-attack arm and credited the difference to decoder
# scale -- the arm looks better partly because it was measured over fewer attacks.
# Until those four cells are re-run (2 chains x 2 guards), every contrast below is computed
# on the chains present on BOTH sides, per guard, and the subset is printed.


def arm_cells(campaign: str) -> dict:
    """(guard, chain) -> cell dir, for a decoder arm in the live tree."""
    out = {}
    for d in glob.glob('outputs/autoattack_defense/defense+evaluate/*/*'):
        r = _lj(os.path.join(d, 'results.json'))
        if not r or r.get('campaign') != campaign:
            continue
        out[((r.get('defense_config') or {}).get('guard_model'), r.get('encoding'))] = d
    return out


def union_flags(get_dir, guard, subset) -> dict:
    """OR-reduce per-prompt jailbreak flags over `subset` of the attack suite."""
    u: dict = {}
    for c in subset:
        d = get_dir(guard, c)
        if d:
            for i, v in _flags(d).items():
                u[i] = u.get(i, False) or v
    return u


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar. b = fixed by the new arm, c = newly broken by it."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(b, c) + 1))
    return min(1.0, 2 * tail / 2 ** n)


def report(campaign: str | None) -> None:
    if campaign:
        cells = arm_cells(campaign)
        get = lambda g, c: cells.get((g, c))  # noqa: E731
        label = f'ARM {campaign}'
    else:
        cells = collect_harm()
        get = lambda g, c: (cells.get(('+rg', g, c)) or (None, None))[1]  # noqa: E731
        label = 'BASELINE +rg (7B self-decode, published)'

    print('=' * 74)
    print(label)
    print('=' * 74)
    for g in GUARDS:
        print(f'\n--- {g} ---')
        for c in CHAINS:
            d = get(g, c)
            if not d:
                print(f'  MISSING {c}')
                continue
            f = _flags(d)
            tag = 'text ' if c in TEXT_CHAINS else 'image'
            print(f'  {tag} {c:26}{100.0 * sum(f.values()) / len(f):5.0f}%')
        for name, subset in (('TEXT ', sorted(TEXT_CHAINS)),
                             ('IMAGE', sorted(IMAGE_CHAINS)),
                             ('ALL  ', CHAINS)):
            u = union_flags(get, g, subset)
            if u:
                print(f'  >> {name} ensemble ASR = '
                      f'{100.0 * sum(u.values()) / len(u):.0f}%  (n={len(u)})')

    if campaign:  # paired test against the published baseline, on MATCHED chains
        base_cells = collect_harm()
        base_get = lambda g, c: (base_cells.get(('+rg', g, c)) or (None, None))[1]  # noqa: E731
        print('\n[McNemar exact — paired ensemble flags vs the baseline, MATCHED subset]')
        print(f"  {'guard':22}{'k/11':>6}{'base':>7}{'arm':>6}{'fixed':>7}{'broken':>8}{'p':>11}")
        owed = []
        for g in GUARDS:
            shared = [c for c in CHAINS if get(g, c) and base_get(g, c)]
            owed += [(g, c) for c in CHAINS if base_get(g, c) and not get(g, c)]
            base, new = union_flags(base_get, g, shared), union_flags(get, g, shared)
            ids = sorted(set(base) & set(new))
            if not ids:
                print(f'  {g:22} no paired ids (baseline tree not present here)')
                continue
            b = sum(1 for i in ids if base[i] and not new[i])
            c = sum(1 for i in ids if not base[i] and new[i])
            br = 100.0 * sum(base[i] for i in ids) / len(ids)
            nr = 100.0 * sum(new[i] for i in ids) / len(ids)
            print(f'  {g:22}{len(shared):>4}/11{br:>7.0f}{nr:>6.0f}{b:>7}{c:>8}'
                  f'{mcnemar_exact(b, c):>11.2e}')
        if owed:
            print('\n  🔴 ARM INCOMPLETE — no post-fix cell for: '
                  + ', '.join(f'{g.split("_")[0]}/{c}' for g, c in owed))
            print('     The rows above are matched-subset contrasts, NOT the paper\'s '
                  '11-attack ensemble.\n     Report them as such, or re-run the '
                  f'{len(owed)} missing cells.')


if __name__ == '__main__':
    report(sys.argv[1] if len(sys.argv) > 1 else None)
