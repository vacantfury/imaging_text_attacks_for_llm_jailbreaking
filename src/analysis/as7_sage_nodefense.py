"""AS-7 · the undefended denominators for the SAGE coverage table (`tab:bypass`).

WHY THIS EXISTS. Review 1, con 3: the SAGE coverage section argues that any ASR
difference between the two arms is a property of the DEFENSE's coverage rather
than of the image being a better attack channel -- and it grounds that on a
no-defense text-vs-image comparison that appears NOWHERE in the paper. The
reviewer is right that this is not optional: without the undefended pair, an
intrinsic model-level modality shift is an equally good explanation of the whole
table. This module produces those cells so they can be printed, and pins them so
they cannot drift.

THE SELECTION RULE, AND WHY IT IS NOT "LATEST WINS". Several of these
(model, attack) cells were collected more than once, including twice on the SAME
DAY. Picking the newest would silently pair a defended cell from one job with an
undefended cell from another -- the exact cross-run contamination the reviewer
raises in con 4, and which this repo has already been burned by. Instead each
undefended cell is PINNED to the directory nearest in time to its own SAGE cell,
i.e. the same grid job; every pin below resolved within 3 minutes of its anchor,
and the two flash-lite pairs share a timestamp exactly.

THE PIN IS SELF-CHECKING. `verify_sage()` re-reads the eight SAGE cells and
asserts they still reproduce Table 4's published values. If they do not, the
window this module pins to is no longer the window the paper was built from, and
the undefended numbers must not be used -- so it RAISES rather than emitting.

    python3 src/analysis/as7_sage_nodefense.py            # check + print rows
    python3 src/analysis/as7_sage_nodefense.py --tex PATH # also verify vs paper

Stdlib only, like as7_tables.py, so it runs under a bare python3.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

MODELS = ("gemini-2.5-flash-lite", "gemini-2.5-flash", "gpt-4o-mini", "claude-sonnet-4-6")
ATTACKS = ("set_theory", "formal_logic")

# Table 4 as published: (SAGE-text, ir_plain+SAGE). The pin is validated against
# these, so a drifted window fails loudly instead of yielding mismatched pairs.
PUBLISHED_SAGE = {
    ("gemini-2.5-flash-lite", "set_theory"): (17, 43),
    ("gemini-2.5-flash-lite", "formal_logic"): (33, 41),
    ("gemini-2.5-flash", "set_theory"): (8, 11),
    ("gemini-2.5-flash", "formal_logic"): (10, 13),
    ("gpt-4o-mini", "set_theory"): (6, 21),
    ("gpt-4o-mini", "formal_logic"): (7, 43),
    ("claude-sonnet-4-6", "set_theory"): (4, 7),
    ("claude-sonnet-4-6", "formal_logic"): (16, 15),
}

# Pinned undefended cells: (model, attack, arm) -> output directory basename.
# Each is the no_defense run nearest in time to that cell's SAGE run.
PINNED = {
    ("gemini-2.5-flash-lite", "set_theory", "text"): "gemini-2.5-flash-lite_no_defense_llm_set_theory_20260803_031539_65251864",
    ("gemini-2.5-flash-lite", "set_theory", "image"): "gemini-2.5-flash-lite_no_defense_llm_set_theory_ir_plain_20260803_031539_6951267",
    ("gemini-2.5-flash-lite", "formal_logic", "text"): "gemini-2.5-flash-lite_no_defense_llm_formal_logic_20260803_031539_86787563",
    ("gemini-2.5-flash-lite", "formal_logic", "image"): "gemini-2.5-flash-lite_no_defense_llm_formal_logic_ir_plain_20260803_031539_22996076",
    ("gemini-2.5-flash", "set_theory", "text"): "gemini-2.5-flash_no_defense_llm_set_theory_20260803_032043_74850108",
    ("gemini-2.5-flash", "set_theory", "image"): "gemini-2.5-flash_no_defense_llm_set_theory_ir_plain_20260803_032048_10443082",
    ("gemini-2.5-flash", "formal_logic", "text"): "gemini-2.5-flash_no_defense_llm_formal_logic_20260803_032201_5034",
    ("gemini-2.5-flash", "formal_logic", "image"): "gemini-2.5-flash_no_defense_llm_formal_logic_ir_plain_20260803_032205_85205950",
    ("gpt-4o-mini", "set_theory", "text"): "gpt-4o-mini_no_defense_llm_set_theory_20260803_032704_23294976",
    ("gpt-4o-mini", "set_theory", "image"): "gpt-4o-mini_no_defense_llm_set_theory_ir_plain_20260803_032809_28223517",
    ("gpt-4o-mini", "formal_logic", "text"): "gpt-4o-mini_no_defense_llm_formal_logic_20260803_032952_21256516",
    ("gpt-4o-mini", "formal_logic", "image"): "gpt-4o-mini_no_defense_llm_formal_logic_ir_plain_20260803_033054_96352647",
    ("claude-sonnet-4-6", "set_theory", "text"): "claude-sonnet-4-6_no_defense_llm_set_theory_20260803_033409_71209269",
    ("claude-sonnet-4-6", "set_theory", "image"): "claude-sonnet-4-6_no_defense_llm_set_theory_ir_plain_20260803_033458_93560103",
    ("claude-sonnet-4-6", "formal_logic", "text"): "claude-sonnet-4-6_no_defense_llm_formal_logic_20260803_033619_41915823",
    ("claude-sonnet-4-6", "formal_logic", "image"): "claude-sonnet-4-6_no_defense_llm_formal_logic_ir_plain_20260803_033624_13917512",
}

ROOTS = ("outputs/image_presence_threshold/defense+evaluate",
         "outputs/defense_read_access/defense+evaluate")


def _load(basename: str, root: str = ".") -> dict:
    for r in ROOTS:
        hits = [p for p in
                (os.path.join(root, r, b, basename, "results.json")
                 for b in os.listdir(os.path.join(root, r))
                 if os.path.isdir(os.path.join(root, r, b)))
                if os.path.exists(p)]
        if hits:
            with open(hits[0]) as fh:
                return json.load(fh)
    raise FileNotFoundError(f"pinned cell not found on disk: {basename}")


def verify_sage(root: str = ".") -> None:
    """The pinned window must still reproduce Table 4, or the pins are stale."""
    bad = []
    for r in ROOTS:
        base = os.path.join(root, r)
        if not os.path.isdir(base):
            continue
        for bench in os.listdir(base):
            bdir = os.path.join(base, bench)
            if not os.path.isdir(bdir):
                continue
            for d in os.listdir(bdir):
                rj = os.path.join(bdir, d, "results.json")
                if not os.path.exists(rj) or "_sage_" not in d or "20260803" not in d:
                    continue
                with open(rj) as fh:
                    j = json.load(fh)
                tm = str(j.get("target_model"))
                src = (j.get("upstream_ref") or {}).get("source_dir") or ""
                if tm not in MODELS or not any(a in src for a in ATTACKS):
                    continue
                enc = "set_theory" if "set_theory" in src else "formal_logic"
                arm = 1 if os.path.basename(src.rstrip("/")).startswith("ir_plain") else 0
                want = PUBLISHED_SAGE.get((tm, enc))
                if want and j.get("asr") is not None and round(j["asr"]) != want[arm]:
                    bad.append(f"{tm}/{enc}/{'image' if arm else 'text'}: "
                               f"disk {j['asr']:.0f} vs published {want[arm]}")
    if bad:
        print("PINNED WINDOW NO LONGER MATCHES TABLE 4 -- undefended cells unusable:",
              file=sys.stderr)
        for b in bad:
            print("  !!", b, file=sys.stderr)
        raise SystemExit(1)
    print(f"verify OK -- pinned window reproduces all {len(PUBLISHED_SAGE)} published SAGE cells")


def rows(root: str = ".") -> list[tuple]:
    out = []
    for m in MODELS:
        for a in ATTACKS:
            t = _load(PINNED[(m, a, "text")], root)["asr"]
            i = _load(PINNED[(m, a, "image")], root)["asr"]
            out.append((m, a, round(t), round(i), round(i - t)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--tex", help="also assert every emitted value appears in this .tex")
    args = ap.parse_args()

    verify_sage(args.root)
    rs = rows(args.root)
    deltas = [r[4] for r in rs]
    print("\n% undefended denominators for tab:bypass (generated -- do not hand-edit)")
    for m, a, t, i, d in rs:
        print(f"%   {m:22} {a:13} no-def text {t:>3}  image {i:>3}  delta {d:+3}")
    print(f"%   RANGE: {min(deltas):+d} to {max(deltas):+d} pp")

    if args.tex:
        tex = open(args.tex).read()
        missing = [f"{m}/{a} no-def {lbl} {v}"
                   for m, a, t, i, _ in rs
                   for lbl, v in (("text", t), ("image", i))
                   if not re.search(rf"(?<![0-9.]){v}(?![0-9.])", tex)]
        rng = f"{min(deltas)}$ to $+{max(deltas)}" if min(deltas) < 0 else ""
        if missing:
            print("\nMISSING FROM TEX:", file=sys.stderr)
            for x in missing:
                print("  !!", x, file=sys.stderr)
            return 1
        print(f"\nverify OK -- all {2 * len(rs)} undefended values appear in {args.tex}")
        print(f"    (prose must state the range as {min(deltas):+d} to {max(deltas):+d} pp)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
