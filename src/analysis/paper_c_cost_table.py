"""Rebuild tab:cost on an EXPLICITLY PINNED cell population.  ($0, stored data.)

The published version of this table said "medians over all Paper-C cells" and
pinned nothing further. The 2026-08-08 table audit could not reproduce its token
or wall columns, and a population probe explains why: the `calls` column is a
structural property of each algorithm and is stable across every population
tried, but the token columns swing 2--3x with the choice of cells, because
different campaigns weight different attacks and attacks differ enormously in
prompt length (ECSO input read 907, 1616, 1836 and 3231 tokens under four
different reasonable readings of "all Paper-C cells"). None of the four
populations reproduced the published row, so the original population is not
recoverable; this rebuilds the table on a stated one instead.

PINNED POPULATION: every `paper_c_*` cell on the primary target (Qwen2.5-VL)
scored under HarmBench. Target and benchmark are pinned because they are the two
axes that move token counts most; the campaign set is left broad on purpose, so
the table describes the paper's whole measured corpus rather than one round.

A NOTE ON THE SECONDS COLUMN, which the published caption did not make: it is
cell wall-clock divided by prompt count, under our own concurrency settings. It
is a throughput figure, NOT single-request latency, and it is the one column
that would change on different hardware or a different job budget. The main
paper's cost claims do not rest on this table -- they come from the matched-pair
analysis (n=143) -- so nothing downstream turns on it.

    python -m src.analysis.paper_c_cost_table
"""
from __future__ import annotations

import glob
import json
import os
import statistics as st

REPO = ("/Users/haoyu/Files/US study life and job/research_and_projects/"
        "AI safety/llm_guardrail_security")
TARGET = "qwen2_5_vl_7b"
LABEL = {
    "no_defense": "no defense",
    "guard_baseline": "guard alone",
    "ecso": "ECSO",
    "modality_complete": "amplifier (mc)",
    "modality_complete+rg": r"amplifier $+$reguard",
    "semantic_smooth": "SemanticSmooth",
}
ORDER = list(LABEL)


def cells():
    for d in glob.glob(os.path.join(REPO, "outputs/autoattack_defense/defense+evaluate/*/*")):
        rp = os.path.join(d, "results.json")
        if not os.path.exists(rp):
            continue
        try:
            r = json.load(open(rp, encoding="utf-8"))
        except Exception:
            continue
        if r.get("target_model") != TARGET:
            continue
        if not (r.get("campaign") or "").startswith("paper_c"):
            continue
        if not (r.get("benchmark") or "").lower().startswith("harmbench"):
            continue
        tu = (r.get("target_usage") or {}).get("total") or {}
        n = r.get("count") or 0
        if not n or not tu:
            continue
        dfn = r.get("defense")
        if dfn == "modality_complete" and (r.get("defense_config") or {}).get("reguard_original"):
            dfn = "modality_complete+rg"
        yield dfn, (tu.get("inference_count", 0) / n, tu.get("input_tokens", 0) / n,
                    tu.get("output_tokens", 0) / n, (r.get("elapsed_seconds") or 0) / n)


def main() -> None:
    by = {}
    for dfn, vals in cells():
        by.setdefault(dfn, []).append(vals)

    print(f"pinned population: paper_c_* x {TARGET} x harmbench\n")
    print(f"{'defense':24s}{'calls':>7s}{'in tok':>8s}{'out tok':>9s}{'sec':>7s}{'cells':>7s}")
    rows = []
    for dfn in ORDER:
        g = by.get(dfn) or []
        if not g:
            print(f"{LABEL[dfn]:24s}  (no cells)")
            continue
        med = tuple(st.median(x[i] for x in g) for i in range(4))
        rows.append((dfn, med, len(g)))
        print(f"{LABEL[dfn]:24s}{med[0]:7.2f}{med[1]:8.0f}{med[2]:9.0f}{med[3]:7.1f}{len(g):7d}")

    print("\n--- LaTeX body for tab:cost ---")
    for dfn, med, n in rows:
        print(f"{LABEL[dfn]:22s} & {med[0]:.2f} & {med[1]:.0f} & {med[2]:.0f} "
              f"& {med[3]:.1f} \\\\")
    print(f"\ntotal cells in population: {sum(n for _, _, n in rows)}")


if __name__ == "__main__":
    main()
