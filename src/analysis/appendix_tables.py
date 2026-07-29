"""LaTeX for the two appendix tables review 2 asks for. No new generations.

    python -m src.analysis.appendix_tables --table middle_band
    python -m src.analysis.appendix_tables --table dual_judge

Both read the same stored rejudge dirs the figures read, so every number here is
the one the figures and main tables are computed from.

TABLE 1 (middle_band) answers review 2's Q1. The main text decomposes each cell's
draws into explicit refusal / judged success / neither, and the reviewer asks where
the successes actually sit. Two readings of the band make opposite predictions:
"the target refuses insufficiently" (refusal disposition gates how much mass reaches
a band where success is possible) versus "the target gets confused and rambles" (the
band is itself a target-specific failure). The discriminator is whether the per-draw
hazard INSIDE the band tracks coverage. It does not — see the module's __main__
output — so we report band size and in-band hazard side by side and let the reader
see which term moves.

TABLE 2 (dual_judge) answers the single-judge concern. Every cell was judged twice:
once by the free on-cluster guard classifier (wildguard) during the run itself, and
once by gpt-5-mini, the reportable completion judge. Reporting both per cell is free
and shows the disagreement is one-directional and concentrated on the code arm.
"""

from __future__ import annotations

import argparse
import glob
import json
import os

from src.analysis.middle_band import is_refusal
from src.analysis.paper_d_figures import (
    CAMPAIGNS,
    EXPECTED_DRAWS_PER_CELL,
    REJUDGE_GLOB,
    TARGET_LABEL,
    _classify,
)

DEFENSE_TEX = {
    "no_defense": "none",
    "sage": "SAGE",
    "sage_t05": r"SAGE ($T{=}0.5$)",
    "semantic_smooth": "SemanticSmooth",
    "canonicalize": "canonicalize",
    "canonicalize_guard": r"canon.$+$WildGuard",
    "canonicalize_guard3": r"canon.$+$LlamaGuard-3",
    "guard_baseline": "LlamaGuard-3 (standalone)",
}
ATTACK_TEX = {"code": "code", "surf": "surface"}
TARGET_ORDER = ["llama", "llama70", "qwen", "gemma"]


def collect(root: str = ".") -> dict:
    """(target, defense, attack) -> per-cell record with both judges' verdicts."""
    out = {}
    for d in glob.glob(os.path.join(root, REJUDGE_GLOB), recursive=True):
        rp = os.path.join(d, "results.json")
        if not os.path.exists(rp):
            continue
        meta = json.load(open(rp))
        if meta.get("campaign") not in CAMPAIGNS:
            continue
        stats = (meta.get("eval_stats") or {}).get("HarmBenchEvaluator", {})
        if (stats.get("total_evaluated") != EXPECTED_DRAWS_PER_CELL
                or stats.get("fallback_parse_count")
                or meta.get("status") != "success"):
            continue
        src_dir = (meta.get("upstream_ref") or {}).get("source_dir", "")
        sp = os.path.join(root, src_dir, "results.json")
        if not os.path.exists(sp):
            sp = os.path.join(src_dir, "results.json")
        upstream = json.load(open(sp)) if os.path.exists(sp) else {}
        key = _classify(meta, upstream)
        if key in out:
            raise SystemExit(f"DUPLICATE cell {key}")
        refused = success = band = succ_unrefused = succ_refused = 0
        for line in open(os.path.join(d, "raw_results.jsonl")):
            row = json.loads(line)
            r = is_refusal(row.get("response") or "")
            s = bool(row.get("asr"))
            refused += r
            success += s
            band += (not r) and (not s)
            succ_unrefused += (not r) and s
            succ_refused += r and s
        out[key] = dict(
            n=EXPECTED_DRAWS_PER_CELL, mini=meta["asr"], guard=upstream.get("asr"),
            refused=refused, success=success, band=band,
            succ_unrefused=succ_unrefused, succ_refused=succ_refused,
        )
    return out


def middle_band_table(cells: dict, defense: str = "sage", attack: str = "code") -> str:
    lines = [
        r"\begin{tabular}{lrrrr}", r"\toprule",
        r"Target & Refusal & Band & \multicolumn{2}{c}{Judged success} \\",
        r"\cmidrule(lr){4-5}",
        r" & (\%) & (\%) & in band (\%) & after a refusal (\%) \\", r"\midrule",
    ]
    for t in TARGET_ORDER:
        c = cells.get((t, defense, attack))
        if not c:
            continue
        exposed = c["band"] + c["succ_unrefused"]
        haz = 100.0 * c["succ_unrefused"] / exposed if exposed else float("nan")
        pref = 100.0 * c["succ_refused"] / c["refused"] if c["refused"] else float("nan")
        lines.append(
            f"{TARGET_LABEL[t]} & {100.0*c['refused']/c['n']:.1f} & "
            f"{100.0*c['band']/c['n']:.1f} & {haz:.1f} & {pref:.2f} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(lines)


def dual_judge_table(cells: dict) -> str:
    lines = [
        r"\begin{tabular}{llrrr}", r"\toprule",
        r"Target & Defense $\times$ attack & gpt-5-mini & WildGuard & $\Delta$ \\",
        r"\midrule",
    ]
    prev = None
    for t in TARGET_ORDER:
        for (tt, de, a), c in sorted(cells.items()):
            if tt != t:
                continue
            if c["guard"] is None:
                continue
            lab = TARGET_LABEL[t] if prev != t else ""
            prev = t
            lines.append(
                f"{lab} & {DEFENSE_TEX.get(de, de)} $\\times$ {ATTACK_TEX.get(a, a)} & "
                f"{c['mini']:.2f} & {c['guard']:.2f} & "
                f"{c['guard']-c['mini']:+.2f} \\\\")
        lines.append(r"\addlinespace")
    lines += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--table", choices=["middle_band", "dual_judge", "both"],
                    default="both")
    ap.add_argument("--defense", default="sage")
    ap.add_argument("--attack", default="code")
    args = ap.parse_args()
    cells = collect(args.root)
    if args.table in ("middle_band", "both"):
        print("% ---- middle band ----")
        print(middle_band_table(cells, args.defense, args.attack))
    if args.table in ("dual_judge", "both"):
        print("\n% ---- dual judge ----")
        print(dual_judge_table(cells))
        deltas = [c["guard"] - c["mini"] for c in cells.values() if c["guard"] is not None]
        code = [c["guard"] - c["mini"] for (t, d, a), c in cells.items()
                if c["guard"] is not None and a == "code"]
        surf = [c["guard"] - c["mini"] for (t, d, a), c in cells.items()
                if c["guard"] is not None and a == "surf"]
        print(f"% cells={len(deltas)} guard-higher={sum(1 for x in deltas if x > 0)} "
              f"mean delta code={sum(code)/len(code):+.2f} surf={sum(surf)/len(surf):+.2f}")


if __name__ == "__main__":
    main()
