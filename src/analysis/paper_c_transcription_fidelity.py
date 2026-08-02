"""Review-20 con 8 — measured transcription fidelity on the distraction grid.

The paper claims reguard repairs the dispersed/distraction attack because
transcription reassembles the scattered grid; review 20 asks that this be backed
by measured transcription fidelity, not only block-rate shifts. This measures it
from the stored decode traces (outputs/autoattack_defense/decode_traces/fidelity/,
written by decode_fidelity.yaml) -- no new runs, no API.

Metric: content-word recall of the ORIGINAL harmful behavior in a given view --
|content(original) present in view| / |content(original)| -- computed for
  wrapper    the encoded text channel, the only text a guard sees under gb
             (contains no payload by construction: the floor)
  recovered  the target's transcription of the grid image (what reguard adds)
  union      wrapper + recovered, the exact text reguard screens

Verbatim token match after lowercasing/punctuation-stripping, no stemming: the
aux-LLM decomposition REPHRASES sub-questions, so this is a stated LOWER BOUND
on semantic fidelity. The claim needs only the contrast: near-zero under the
guard-alone view, high after transcription.

Ground truth on the grid text itself (which items were payload) was not
persisted by the renderer, so recall is measured against the original behavior
-- which is the mechanism-relevant quantity anyway: does the reassembled view
surface the REQUEST to the guard?

Usage:  .venv/bin/python -m src.analysis.paper_c_transcription_fidelity
"""

from __future__ import annotations

import json
import re

import numpy as np

TRACE = "outputs/autoattack_defense/decode_traces/fidelity/{target}_ir_distraction_grid.jsonl"
SOURCE = (
    "outputs/autoattack_defense/prompt_transform/harmbench/"
    "ir_distraction_grid_20260718_183500_23630684/ir_distraction_grid/prompts.jsonl"
)
TARGETS = ["qwen2_5_vl_7b", "internvl3_8b"]

STOP = set(
    """a an the and or but if then else of in on at to for from with without into onto
    is are was were be been being do does did done have has had having will would can
    could may might must shall should this that these those it its they them their he
    she his her you your we our i me my not no nor so such as by about against between
    through during before after above below up down out off over under again further
    once here there when where why how all any both each few more most other some own
    same than too very just also please write provide describe explain give detailed
    step steps""".split()
)


def content_words(text: str) -> set[str]:
    toks = re.findall(r"[a-z]+", text.lower())
    return {t for t in toks if len(t) >= 4 and t not in STOP}


def recall(original: str, view: str) -> float:
    ref = content_words(original)
    if not ref:
        return float("nan")
    got = set(re.findall(r"[a-z]+", view.lower()))
    return len(ref & got) / len(ref)


def main() -> None:
    originals = {}
    with open(SOURCE) as f:
        for line in f:
            row = json.loads(line)
            originals[row["id"]] = row["original"]

    for target in TARGETS:
        rows = [json.loads(l) for l in open(TRACE.format(target=target))]
        r_wrap, r_rec, r_uni = [], [], []
        for row in rows:
            orig = originals[row["id"]]
            r_wrap.append(recall(orig, row["original_encoded"]))
            r_rec.append(recall(orig, row["recovered"]))
            r_uni.append(recall(orig, row["union"]))
        r_wrap, r_rec, r_uni = map(np.array, (r_wrap, r_rec, r_uni))
        print(f"\n== {target}  (n={len(rows)} behaviors)")
        for name, v in (("wrapper (gb view)", r_wrap), ("recovered", r_rec), ("union (+rg view)", r_uni)):
            print(
                f"  {name:>18}: mean {v.mean():.2f} | median {np.median(v):.2f} "
                f"| >=0.5 in {100*np.mean(v >= 0.5):.0f}% | >=0.3 in {100*np.mean(v >= 0.3):.0f}% "
                f"| =0 in {100*np.mean(v == 0):.0f}%"
            )


if __name__ == "__main__":
    main()
