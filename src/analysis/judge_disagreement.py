"""Per-attack judge-disagreement analysis on stored labels (AS-3, cspaper review 5 con 9).

Review 5 con 9: "The use of a proprietary LLM judge remains a concern ... kappa=0.68 is only
moderate-to-substantial and leaves meaningful uncertainty precisely for CODEATTACK and visual
render responses. The paper ... should provide more human-label detail, PER-ATTACK DISAGREEMENT
ANALYSIS, and results under the official HarmBench classifier or a public alternative."

This module answers the per-attack half at ZERO cost, because the coverage grid was moved
gpt-5-nano -> gpt-5-mini by `rejudge`, which re-scores STORED responses without re-querying the
target. So for many cells both judges' per-prompt labels sit on disk against byte-identical
responses, which is an exact paired comparison rather than an estimate.

COVERAGE IS PRINTED LOUDLY, because this analysis has a structural hole exactly where the
reviewer pointed. `code_attack` entered the suite AFTER the nano -> mini migration, so it has no
gpt-5-nano labels anywhere and can never appear in this table. CODEATTACK is both the attack con 9
names as most uncertain and the attack con 3 shows drives the significance verdict, so a 10-of-11
table presented as "con 9 answered" would be a silent cap. Closing the hole needs a second judge
that scores every attack: the official HarmBench classifier, which is an open model and therefore a
$0 cluster rejudge over stored responses.

What it does NOT answer: the official-HarmBench-classifier half of con 9, which needs a run.
WildGuard rejudge cells exist (34) but are July cells on retired targets covering two attacks, so
they cannot serve this analysis; see `project_wildguard_invalid_as_asr_judge` for why WildGuard is
not a valid ASR judge here in any case.

INTEGRITY GATES (these can fail, unlike a self-comparison). A pair is admitted only if:
  (1) both dirs carry the SAME prompt ids AND byte-identical stored responses for every joined id
      -- a pair whose responses differ is not a judge comparison, it is two different experiments;
  (2) NEITHER dir reports `fallback_parse_count > 0` in eval_stats.

  Gate (2) exists because of a judge-failure sign not in the known set: a cell where EVERY judge
  call returned HTTP 400 still writes a clean-looking `results.json` -- `warnings: []`, a populated
  `eval_stats`, `total_evaluated: 100`, and a plausible ASR -- because the parser silently falls
  back to "no" on an unparseable response. The only trace is `fallback_parse_count`, which nothing
  was checking. A fallback label is not a judgement, so a pair carrying any is not evidence about
  judge agreement; it would show up as fake disagreement. Live-root census 2026-08-21:
  gpt-5-mini 0/3276 cells affected (the paper's judge is clean, so no published number rides on
  this), against wildguard 153/488, gpt-5-nano 123/868, harmbench_llama_2_13b_cls 12/18.

Usage:
    python3 src/analysis/judge_disagreement.py            # paper targets, table + per-attack rows
    python3 src/analysis/judge_disagreement.py --all-targets
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

REJUDGE_ROOT = "outputs/autoattack_defense/rejudge/harmbench"
PAPER_TARGETS = {"qwen2_5_vl_7b", "internvl3_8b"}
# The paper's headline suite (Table tab:suite). Any member missing from the paired table is a
# COVERAGE HOLE and is named in the output, never silently absent.
SUITE = [
    "llm_set_theory", "llm_formal_logic", "llm_classical_language", "non_llm_cipher",
    "code_attack", "ir_plain", "ir_fc_flowchart", "ir_low_contrast", "ir_occluded",
    "ir_mm_typo", "ir_distraction_grid",
]
JUDGE_A = "gpt-5-nano"   # the retired judge
JUDGE_B = "gpt-5-mini"   # the paper's judge


def _load(path):
    try:
        with open(path) as fh:
            return json.load(fh)
    except Exception:
        return None


def _fallbacks(meta):
    """Total fallback_parse_count across evaluators; > 0 means some labels are parser defaults."""
    stats = meta.get("eval_stats") or {}
    if not isinstance(stats, dict):
        return 0
    n = 0
    for _, d in stats.items():
        if isinstance(d, dict):
            n += d.get("fallback_parse_count") or 0
    return n


def _rows(cell_dir):
    """id -> (asr_bool, response) from raw_results.jsonl."""
    out = {}
    p = os.path.join(cell_dir, "raw_results.jsonl")
    if not os.path.exists(p):
        return out
    with open(p) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            rid = r.get("id")
            if rid is None or r.get("asr") is None:
                continue
            out[rid] = (bool(r["asr"]), r.get("response") or "")
    return out


def collect(all_targets=False):
    """Return (pairs, dropped) where pairs are admitted (meta_b, rows_a, rows_b) triples."""
    by_src = defaultdict(dict)
    if not os.path.isdir(REJUDGE_ROOT):
        raise SystemExit(f"missing {REJUDGE_ROOT}")
    for d in sorted(os.listdir(REJUDGE_ROOT)):
        cell = os.path.join(REJUDGE_ROOT, d)
        meta = _load(os.path.join(cell, "results.json"))
        if not meta:
            continue
        jm = meta.get("judge_model")
        src = (meta.get("upstream_ref") or {}).get("source_dir")
        if not jm or not src:
            continue
        by_src[src][jm] = (cell, meta)

    pairs, dropped = [], []
    for src, judges in sorted(by_src.items()):
        if JUDGE_A not in judges or JUDGE_B not in judges:
            continue
        (cell_a, meta_a), (cell_b, meta_b) = judges[JUDGE_A], judges[JUDGE_B]
        tgt = meta_b.get("target_model")
        if not all_targets and tgt not in PAPER_TARGETS:
            continue
        fa, fb_ = _fallbacks(meta_a), _fallbacks(meta_b)
        if fa or fb_:
            dropped.append((src, f"parse fallbacks ({JUDGE_A}={fa}, {JUDGE_B}={fb_}) -- labels are parser defaults"))
            continue
        ra, rb = _rows(cell_a), _rows(cell_b)
        shared = set(ra) & set(rb)
        if not shared:
            dropped.append((src, "no shared prompt ids"))
            continue
        mismatched = [i for i in shared if ra[i][1] != rb[i][1]]
        if mismatched:
            dropped.append((src, f"responses differ on {len(mismatched)}/{len(shared)} ids"))
            continue
        pairs.append((meta_b, {i: ra[i][0] for i in shared}, {i: rb[i][0] for i in shared}))
    return pairs, dropped


def _kappa(b, c, both, neither):
    n = b + c + both + neither
    if n == 0:
        return float("nan")
    po = (both + neither) / n
    pa1 = (both + b) / n          # judge A says harmful
    pb1 = (both + c) / n          # judge B says harmful
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    return float("nan") if pe == 1 else (po - pe) / (1 - pe)


def per_attack(pairs):
    agg = defaultdict(lambda: {"both": 0, "neither": 0, "a_only": 0, "b_only": 0, "cells": 0})
    for meta, ra, rb in pairs:
        enc = meta.get("encoding") or "?"
        s = agg[enc]
        s["cells"] += 1
        for i in ra:
            a, b = ra[i], rb[i]
            if a and b:
                s["both"] += 1
            elif a and not b:
                s["a_only"] += 1
            elif b and not a:
                s["b_only"] += 1
            else:
                s["neither"] += 1
    return agg


def main():
    all_targets = "--all-targets" in sys.argv
    pairs, dropped = collect(all_targets=all_targets)
    scope = "ALL targets" if all_targets else "paper targets (qwen2_5_vl_7b, internvl3_8b)"
    print(f"Paired {JUDGE_A} vs {JUDGE_B} rejudge cells, {scope}")
    print(f"  admitted pairs : {len(pairs)}")
    print(f"  dropped pairs  : {len(dropped)}  (integrity gate)")
    for src, why in dropped[:10]:
        print(f"    - {os.path.basename(src)}: {why}")
    if not pairs:
        raise SystemExit("no admitted pairs")

    agg = per_attack(pairs)
    tot = {"both": 0, "neither": 0, "a_only": 0, "b_only": 0}
    print()
    hdr = f"{'attack':<34}{'n':>7}{'nano%':>8}{'mini%':>8}{'agree%':>8}{'kappa':>8}{'nano+':>7}{'mini+':>7}"
    print(hdr)
    print("-" * len(hdr))
    rows = []
    for enc, s in agg.items():
        n = s["both"] + s["neither"] + s["a_only"] + s["b_only"]
        if n == 0:
            continue
        for k in tot:
            tot[k] += s[k]
        nano = 100 * (s["both"] + s["a_only"]) / n
        mini = 100 * (s["both"] + s["b_only"]) / n
        agree = 100 * (s["both"] + s["neither"]) / n
        k = _kappa(s["a_only"], s["b_only"], s["both"], s["neither"])
        rows.append((agree, enc, n, nano, mini, k, s["a_only"], s["b_only"]))
    for agree, enc, n, nano, mini, k, ao, bo in sorted(rows):
        print(f"{enc:<34}{n:>7}{nano:>8.1f}{mini:>8.1f}{agree:>8.1f}{k:>8.2f}{ao:>7}{bo:>7}")

    n = sum(tot.values())
    print("-" * len(hdr))
    nano = 100 * (tot["both"] + tot["a_only"]) / n
    mini = 100 * (tot["both"] + tot["b_only"]) / n
    agree = 100 * (tot["both"] + tot["neither"]) / n
    k = _kappa(tot["a_only"], tot["b_only"], tot["both"], tot["neither"])
    print(f"{'POOLED':<34}{n:>7}{nano:>8.1f}{mini:>8.1f}{agree:>8.1f}{k:>8.2f}{tot['a_only']:>7}{tot['b_only']:>7}")
    print()
    print("nano+ = judged harmful by gpt-5-nano only;  mini+ = by gpt-5-mini only.")
    print("Ratio nano+/mini+ > 1 means the retired judge was the LOOSER one on that attack.")

    covered = set(agg)
    missing = [a for a in SUITE if a not in covered]
    print()
    print(f"SUITE COVERAGE: {len(SUITE) - len(missing)}/{len(SUITE)} attacks paired.")
    if missing:
        print(f"  !! UNCOVERED (no {JUDGE_A} labels exist): {', '.join(missing)}")
        print("  !! This table therefore does NOT speak to those attacks. CODEATTACK in particular")
        print("     is the attack con 9 flags as most uncertain and the one con 3 shows drives the")
        print("     significance verdict. Do not report this as a complete answer to con 9.")
    else:
        print("  full suite paired.")


if __name__ == "__main__":
    main()
