"""Sweep every stored cell for DEGENERATE guard behaviour.  ($0 -- no model calls.)

Opened by a 2026-08-08 finding: `paper_c_reguard_5guard_benign` holds a
LlamaGuard-3/Qwen benign-image cell that blocked 100/100 benign prompts while its
three campaign siblings blocked 0, 4 and 5. A guard that gates every benign input
is STUCK, not strict -- and nothing in the existing integrity checks catches it.
The rows are well-formed, the JSON parses, and a benign cell carries no `asr`
field to come back None, so every "is this cell valid" test we had says yes.

The block rate is the one quantity that exposes it, and it is free: a gated
prompt receives a fixed refusal string, so the rate is an exact count over
`raw_results.jsonl`.

Three detectors, each a different failure:

  STUCK-BLOCKING  a benign cell whose guard gated >=99% of benign prompts.
                  The guard is jammed on "unsafe"; the cell's over-refusal is
                  meaningless and its ASR (if harmful) would be fake-perfect.
  STUCK-PASSING   a harmful cell, with a guard configured, at exactly 0% blocked
                  while a replicate sibling blocked substantially. The guard is
                  jammed on "safe" -- this is the dangerous direction, because it
                  inflates the attack's apparent success against the defense.
  REPLICATE-SPLIT a group of cells identical in every configured respect
                  (target, defense, guard, reguard flag, encoding, benchmark,
                  upstream source, campaign) whose block rates span more than
                  SPREAD_LIMIT points. Run-to-run drift on block rate is a point
                  or two; a wide split means at least one member is broken.

Usage:  python src/analysis/paper_c_degenerate_cell_sweep.py [scan.tsv]

The scan file is produced by (fast, ~9s over 2.4k cells):
  awk -v T="I cannot assist ... flagged it as unsafe." \
    '{n[FILENAME]++; if (index($0,T)) b[FILENAME]++} \
     END {for (f in n) print f"\\t"n[f]"\\t"(b[f]+0)}' \
    outputs/autoattack_defense/defense+evaluate/*/*/raw_results.jsonl > scan.tsv
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

SPREAD_LIMIT = 15.0     # points; ordinary block-rate drift is 1-2
STUCK_BLOCK = 99.0      # benign cells at or above this are jammed shut
MIN_N = 50              # ignore tiny smoke cells

# Campaigns any paper table or builder draws from. A degenerate cell OUTSIDE
# this set is housekeeping; one INSIDE it can reach a published number.
PAPER_FACING = {
    "paper_c_guard_panel", "paper_c_guard_panel_benign", "paper_c_guard_panel_floor",
    "paper_c_reguard_ablation", "paper_c_reguard_5guard", "paper_c_reguard_5guard_benign",
    "paper_c_fidelity_rerun", "paper_c_fidelity_rerun_mini", "paper_c_fidelity_rerun_nodecode",
    "paper_c_gen2_internvl3", "paper_c_heldout", "paper_c_prompt_wording",
    "paper_c_replicate_r2", "paper_c_replicate_r3",
    "paper_c_replicate_r2_postfix", "paper_c_replicate_r3_postfix",
    "paper_c_crossguard_nodecode_benign", "paper_c_guard_swap",
    "paper_c_no_decode_n100",   # feeds the appendix No-Decode Ablation
}


# The degenerate cells this sweep found, quarantined by name so no builder can
# select one. All four come from ONE orchestrator run (2026-07-23 14:12:16,
# `paper_c_reguard_5guard_benign`): LlamaGuard-3 on Qwen2.5-VL gated 100/100
# benign prompts on both channels while every sibling of each cell gated 0-14.
# Verified 2026-08-08 that no PUBLISHED number came from them --- the paper's
# LlamaGuard-3 benign figures resolve to the healthy cells (over-refusal 28.0,
# guard block 5-7%) --- but only because glob sort order happened to put a
# healthy cell last. Importing this set makes that structural instead of lucky.
QUARANTINE = {
    "qwen2_5_vl_7b_modality_complete_ir_plain_20260723_141216_20322381",
    "qwen2_5_vl_7b_modality_complete_ir_plain_20260723_141216_10739989",
    "qwen2_5_vl_7b_modality_complete_non_llm_baseline_20260723_141216_54367552",
    "qwen2_5_vl_7b_modality_complete_non_llm_baseline_20260723_141216_78006417",
}


def load_scan(path):
    out = {}
    with open(path) as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue
            f, n, b = parts
            out[os.path.dirname(f)] = (int(n), int(b))
    return out


def main():
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    scan_path = sys.argv[1] if len(sys.argv) > 1 else "scan.tsv"
    scan = load_scan(scan_path)

    rows = []
    for d, (n, b) in scan.items():
        rp = os.path.join(d, "results.json")
        if not os.path.exists(rp) or n < MIN_N:
            continue
        try:
            r = json.load(open(rp, encoding="utf-8"))
        except Exception:
            continue
        dc = r.get("defense_config") or {}
        bench = (r.get("benchmark") or "").lower()
        rows.append({
            "dir": d, "n": n, "block": 100.0 * b / n,
            "campaign": r.get("campaign") or "", "defense": r.get("defense"),
            "target": r.get("target_model"), "guard": dc.get("guard_model"),
            "reguard": bool(dc.get("reguard_original")),
            "variant": dc.get("prompt_variant"),
            # decode_style / decode_text are ARM selectors, not incidental
            # config: `paper_c_no_decode_n100` runs decode-on and decode-off
            # against the same guard, target, encoding and source. Omitting them
            # from the grouping key made the two arms look like replicates of one
            # cell and produced five false "replicate-split" findings with
            # 20-51 point spreads -- which is the ablation's EFFECT, not a defect.
            "dstyle": dc.get("decode_style"),
            "dtext": dc.get("decode_text"),
            "enc": r.get("encoding"), "bench": bench,
            "benign": bench.startswith("orbench"),
            "src": (r.get("upstream_ref") or {}).get("source_dir", ""),
        })

    print(f"scanned {len(rows)} cells with n>={MIN_N}\n")
    findings = []

    # --- 1. STUCK-BLOCKING -------------------------------------------------
    stuck_b = [x for x in rows if x["benign"] and x["block"] >= STUCK_BLOCK]
    print("=" * 78)
    print(f"[1] STUCK-BLOCKING  -- benign cells with guard block >= {STUCK_BLOCK:.0f}%")
    print("=" * 78)
    if not stuck_b:
        print("  none")
    for x in sorted(stuck_b, key=lambda x: x["campaign"]):
        flag = "  <-- PAPER-FACING" if x["campaign"] in PAPER_FACING else ""
        print(f"  {x['block']:5.1f}%  {x['guard'] or '--':20s} {x['target']:15s} "
              f"[{x['campaign']}]{flag}\n      {os.path.basename(x['dir'])}")
        findings.append(("stuck-blocking", x))

    # --- 2/3. group replicates --------------------------------------------
    groups = defaultdict(list)
    for x in rows:
        groups[(x["target"], x["defense"], x["guard"], x["reguard"], x["variant"],
                x["dstyle"], x["dtext"],
                x["enc"], x["bench"], x["src"], x["campaign"])].append(x)

    print("\n" + "=" * 78)
    print(f"[2] REPLICATE-SPLIT -- identical config, block rate spread > {SPREAD_LIMIT:.0f} pts")
    print("=" * 78)
    splits = []
    for key, g in groups.items():
        if len(g) < 2:
            continue
        lo, hi = min(x["block"] for x in g), max(x["block"] for x in g)
        if hi - lo > SPREAD_LIMIT:
            splits.append((hi - lo, key, g))
    if not splits:
        print("  none")
    for spread, key, g in sorted(splits, key=lambda t: -t[0]):
        camp = key[10]
        flag = "  <-- PAPER-FACING" if camp in PAPER_FACING else ""
        print(f"  spread {spread:5.1f} pts  {key[2] or '--':20s} {key[0]:15s} "
              f"{key[7] or '--':22s} [{camp}]{flag}")
        for x in sorted(g, key=lambda x: -x["block"]):
            print(f"       {x['block']:5.1f}%  {os.path.basename(x['dir'])}")
        findings.append(("replicate-split", g))

    # --- 3. STUCK-PASSING --------------------------------------------------
    print("\n" + "=" * 78)
    print("[3] STUCK-PASSING -- harmful cell at 0% blocked while a sibling blocked >20%")
    print("=" * 78)
    zero = []
    for key, g in groups.items():
        if key[8].startswith("orbench") or key[2] is None:
            continue
        if len(g) < 2:
            continue
        if any(x["block"] == 0.0 for x in g) and any(x["block"] > 20.0 for x in g):
            zero.append((key, g))
    if not zero:
        print("  none")
    for key, g in zero:
        camp = key[10]
        flag = "  <-- PAPER-FACING" if camp in PAPER_FACING else ""
        print(f"  {key[2]:20s} {key[0]:15s} {key[5] or '--':22s} [{camp}]{flag}")
        for x in sorted(g, key=lambda x: x["block"]):
            print(f"       {x['block']:5.1f}%  {os.path.basename(x['dir'])}")
        findings.append(("stuck-passing", g))

    pf = sum(1 for kind, x in findings
             if (x["campaign"] if isinstance(x, dict) else x[0]["campaign"]) in PAPER_FACING)
    print("\n" + "=" * 78)
    print(f"TOTAL findings: {len(findings)}   paper-facing: {pf}")
    print("=" * 78)


if __name__ == "__main__":
    main()
