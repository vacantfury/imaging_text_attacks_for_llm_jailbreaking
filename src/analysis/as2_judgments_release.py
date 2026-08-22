"""AS-2 per-prompt evaluation release.

WHY THIS EXISTS. AS-2's artifact statement promises, verbatim, "the per-prompt
evaluation rows for every cell, each carrying the model response together with
the judge's output, reasoning and raw response", so that "any individual
judgment in this paper can therefore be inspected, and any table recomputed,
without re-querying a target model". This module is what makes that sentence
literally true. It is the AS-2 twin of `as7_judgments_release.py` and follows
the same shape deliberately: pin cells by CAMPAIGN, project each stored
`raw_results.jsonl`, and refuse to ship a release whose rows do not reproduce
the metric its own `results.json` recorded.

WHY CAMPAIGN AND NOT PATH. Arm identity lives in the config and in
`upstream_ref.source_dir`, never in the directory name, and a failure-triggered
rerun is the NEWEST directory -- so "latest wins" prefers broken data. Pinning
the campaign tag selects the round that was actually reported.

WHY A SUPERSET. The pinned campaigns contain some arms the paper does not
report. They ship anyway. For a reproducibility artifact the safe direction is
more than was reported, never less, and a reviewer who can see the unreported
arms of a round can check that nothing was selected after the fact.

RICH, NOT LEAN. AS-7 ships {id, asr, refusal}; AS-2 promised the response and
both judge trails, so that is what goes in. The two rubrics are kept separate
(`judge_*` is the harm rubric, `refusal_judge_*` the refusal rubric) because
collapsing them would silently merge two different instruments.
"""
from __future__ import annotations

import glob
import json
import os

OUT_ROOT = "outputs/image_presence_threshold/judgments_release"

# The rounds behind AS-2's tables, main paper and supplementary alike.
CAMPAIGNS = {
    "paper_b_sensitivity_ladder",        # tab:ladder
    "paper_b_topic_stratified",          # stratified benign cost
    "paper_b_presence_controls",         # tab:presence
    "paper_b_image_property_ablation",   # hosted rows of tab:imgvsimg
    "paper_b_property_ablation_ow",      # open-checkpoint row of tab:imgvsimg
    "paper_b_attachment_mention",        # tab:factorial
    "paper_b_attachment_mention_flash",
    "paper_b_mention_placebo_flash",     # the asserted-attachment ladder
    "paper_b_token_budget_control",      # tab:tokenbudget
    "paper_b_serving_stack",             # tab:sameweights
    "paper_b_threshold_shift_openweight",# tab:ow_threshold
    "paper_b_alignment_tier_scan",       # model-selection scan
    "paper_b_generational_ladder",       # within-family replication
    "paper_b_harmful_ladder",            # generational ladder, harmful rungs
    "paper_b_exchange_rate_ow",          # tab:owladder -- the open checkpoint's own
                                         # ladder plus its matched harmful rung. Also
                                         # missing until 2026-08-22: the 2%% plain-harmful
                                         # figure quoted in the abstract, intro, results
                                         # and conclusion is computed from these cells.
    "paper_b_harmful_headroom",          # tab:headroom
    "paper_b_sign_inversion",            # the llava inversion
    "paper_b_symmetry_test",             # tab:hostedharm -- the hosted models'
                                         # harmful side. This campaign was MISSING
                                         # from the release until 2026-08-22: the
                                         # four contrasts it holds are half the
                                         # paper's central price claim and the whole
                                         # input to the break-even table, and they
                                         # shipped in no table and no artifact.
    "paper_b_interleaved_confirm",       # randomised-interleaving control
}

ROW_FIELDS = ("id", "asr", "refusal", "response",
              "judge_output", "judge_reasoning", "judge_raw_response",
              "refusal_judge_output", "refusal_judge_reasoning",
              "refusal_judge_raw_response",
              "num_images", "prompt_stage")

CELL_FIELDS = ("target_model", "defense", "defense_config", "guard_model",
               "transformation_list", "benchmark", "judge_model", "judge_method",
               "campaign", "mode", "asr", "refusal_rate", "primary_metric",
               "eval_stats", "git_sha", "system_message")


def _rows(cell_dir: str, redact_response: bool) -> list[dict]:
    """Project one cell's stored rows.

    `redact_response` is set for cells scored under the HARM rubric. Those rows
    hold working jailbreak completions to public HarmBench behaviours, and this
    archive goes to reviewers as a file. We withhold the completion text and keep
    everything needed to audit the JUDGMENT: the verdict, the judge's reasoning,
    its raw response, and the completion's length. The artifact statement says so
    explicitly rather than leaving a reader to discover a field is missing.
    Benign-rubric cells, which are what every headline number in this paper is
    computed from, ship in full."""
    path = os.path.join(cell_dir, "raw_results.jsonl")
    if not os.path.exists(path):
        return []
    out = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            # A missing verdict stays None. It is a fact about the run, and
            # coercing it to False has moved a published number before.
            row = {k: r.get(k) for k in ROW_FIELDS}
            if redact_response:
                resp = r.get("response")
                row["response"] = None if resp is None else "<withheld: harmful-rubric cell>"
                row["response_chars"] = None if resp is None else len(resp)
            out.append(row)
    return out


def _is_harm_rubric(cell: dict) -> bool:
    """The `benchmark` field selects the JUDGE RUBRIC, not the prompt file:
    `harmbench` means the harm rubric was applied, `jailbreakbench_benign` the
    refusal rubric (which is what the OR-Bench benign rungs are scored with)."""
    return (cell.get("benchmark") or "").lower() == "harmbench"


def _gather(root: str = ".") -> list[str]:
    seen = set()
    for pattern in ("outputs/image_presence_threshold/**/results.json",
                    "outputs/image_presence_threshold/rejudge/**/results.json"):
        for rj in glob.glob(os.path.join(root, pattern), recursive=True):
            try:
                d = json.load(open(rj))
            except Exception:
                continue
            if d.get("campaign") in CAMPAIGNS:
                seen.add(os.path.dirname(rj))
    return sorted(seen)


def _recompute(rows: list[dict], key: str) -> float | None:
    """Rate over rows that HAVE a verdict, as a PERCENTAGE.

    results.json stores these metrics in percent (asr=2.0 means 2%), so the
    recomputed rate is scaled to match. Getting this backwards is what the
    first run of this checker caught: every cell "disagreed" by exactly a
    factor of 100 while the data agreed perfectly."""
    vals = [r.get(key) for r in rows if r.get(key) is not None]
    return (100.0 * sum(1 for v in vals if v) / len(vals)) if vals else None


def emit(root: str = ".", tol: float = 1.1) -> int:
    """Write the release and REFUSE if a cell does not reproduce its own metric (tol in points)."""
    out_root = os.path.join(root, OUT_ROOT)
    os.makedirs(out_root, exist_ok=True)
    index, empty, mismatched = [], [], []

    for cell_dir in _gather(root):
        d = json.load(open(os.path.join(cell_dir, "results.json")))
        rows = _rows(cell_dir, redact_response=_is_harm_rubric(d))
        if not rows:
            empty.append(os.path.relpath(cell_dir, os.path.abspath(root)))
            continue

        # The release must reproduce the number the cell recorded, or it is
        # worse than useless: it would look like an audit trail and disagree.
        for stored_key, row_key in (("asr", "asr"), ("refusal_rate", "refusal")):
            stored = d.get(stored_key)
            if stored is None:
                continue
            got = _recompute(rows, row_key)
            if got is None or abs(got - stored) > tol:
                mismatched.append((os.path.relpath(cell_dir, os.path.abspath(root)),
                                   stored_key, stored, got))

        name = os.path.basename(cell_dir.rstrip("/"))
        with open(os.path.join(out_root, f"{name}.jsonl"), "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        entry = {k: d.get(k) for k in CELL_FIELDS}
        entry.update({"file": f"{name}.jsonl", "n_rows": len(rows),
                      "response_withheld": _is_harm_rubric(d),
                      "stored_dir": os.path.relpath(cell_dir, os.path.abspath(root)),
                      "upstream_ref": d.get("upstream_ref")})
        index.append(entry)

    with open(os.path.join(out_root, "index.json"), "w") as fh:
        json.dump({"campaigns": sorted(CAMPAIGNS), "cells": index}, fh,
                  indent=1, sort_keys=True)

    print(f"wrote {len(index)} cells to {OUT_ROOT}")
    if empty:
        print(f"  {len(empty)} cell(s) had no raw_results.jsonl and were SKIPPED:")
        for e in empty[:10]:
            print(f"    {e}")
    if mismatched:
        print(f"  !! {len(mismatched)} cell/metric pair(s) DO NOT reproduce:")
        for c, k, stored, got in mismatched[:10]:
            print(f"    {c}: stored {k}={stored} vs recomputed {got}")
        raise SystemExit("release refused: a released cell disagrees with its own results.json")
    print("  every released cell reproduces its stored metric")
    return len(index)


if __name__ == "__main__":
    emit()
