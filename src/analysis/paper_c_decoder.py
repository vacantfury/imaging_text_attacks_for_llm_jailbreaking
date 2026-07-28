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
# published tab:reguard, Qwen2.5-VL `+rg` column — the like-for-like baseline
PUBLISHED = {'wildguard': (43, 84), 'guardreasoner_vl_7b': (58, 87)}  # (ASR, over-ref.)


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

    if campaign:  # paired test against the published baseline
        base_cells = collect_harm()
        base_get = lambda g, c: (base_cells.get(('+rg', g, c)) or (None, None))[1]  # noqa: E731
        print('\n[McNemar exact — paired per-prompt ensemble flags vs the baseline]')
        print(f"  {'guard':24}{'fixed':>8}{'broken':>8}{'p':>12}")
        for g in GUARDS:
            base, new = union_flags(base_get, g, CHAINS), union_flags(get, g, CHAINS)
            ids = sorted(set(base) & set(new))
            if not ids:
                print(f'  {g:24} no paired ids (baseline tree not present here)')
                continue
            b = sum(1 for i in ids if base[i] and not new[i])
            c = sum(1 for i in ids if not base[i] and new[i])
            print(f'  {g:24}{b:>8}{c:>8}{mcnemar_exact(b, c):>12.2e}   (n={len(ids)})')


if __name__ == '__main__':
    report(sys.argv[1] if len(sys.argv) > 1 else None)
