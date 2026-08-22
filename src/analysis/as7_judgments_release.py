"""Emit AS-7's per-prompt JUDGMENTS release: {id, asr, refusal}, no response text.

WHAT THIS IS FOR. AS-7's artifact paragraph promises the per-cell `results.json`
and the per-prompt records behind every table, minus the raw harmful completions
(released on request, not posted). A reviewer must be able to recompute every
published number with no model calls. This emitter produces exactly that layer;
`scripts/build_code_artifact.py --paper as7` packages it with the code layer.

WHAT IS RELEASED AND WHAT IS NOT.
  released  -- prompt id, the harm judgment flag, the refusal judgment flag, and
               a per-cell index carrying target/defense/chain/arm/judge/n/metrics
               plus the stored dir and git sha the cell came from.
  withheld  -- the model's response text, and the judge's free-text reasoning,
               which quotes it. Those are the successful-attack outputs the
               ethics statement declines to post openly.

CELL SELECTION IS NEVER AD HOC. Three validated sources, no fresh scanning:
  * the pinned AS-7 campaigns, from as7_tables.CAMPAIGNS (the paper's own builder)
  * the deployable ECSO grid, pinned by campaign tag
  * the May granted grid, resolved by PROVENANCE through as7_may_cells, whose
    selftest reproduces all 60 published tab:main values before anything is
    emitted here

VERIFY IS THE POINT, NOT A COURTESY. `--verify` recomputes each cell's headline
metric FROM THE EMITTED FILE and requires it to equal the value stored in that
cell's own results.json. A release whose files do not reproduce the numbers they
are released to support is worse than no release, so a mismatch is an error, not
a warning.

    python3 src/analysis/as7_judgments_release.py emit
    python3 src/analysis/as7_judgments_release.py verify
"""
from __future__ import annotations

import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import as7_may_cells as may  # noqa: E402
import as7_tables as tables  # noqa: E402

OUT_ROOT = "outputs/defense_read_access/judgments_release"
DEPLOYABLE_CAMPAIGN = "paper_b_ecso_deployable_grid"


def _load_cell(results_json: str) -> dict:
    with open(results_json) as fh:
        return json.load(fh)


def _per_prompt(cell_dir: str) -> list[dict]:
    """{id, asr, refusal} per stored row. A missing verdict stays None -- it is a
    fact about the run and coercing it to False has moved a published number."""
    path = os.path.join(cell_dir, "raw_results.jsonl")
    if not os.path.exists(path):
        return []
    rows = []
    with open(path) as fh:
        for line in fh:
            r = json.loads(line)
            rows.append({"id": r.get("id"), "asr": r.get("asr"), "refusal": r.get("refusal")})
    return rows


def _slug(cell_dir: str) -> str:
    return os.path.basename(cell_dir.rstrip("/"))


def _gather(root: str = ".") -> list[dict]:
    """(group, cell_dir) for every cell the paper's numbers rest on."""
    picked: dict[str, dict] = {}

    def add(group: str, cell_dir: str) -> None:
        real = os.path.realpath(cell_dir)
        picked.setdefault(real, {"group": group, "dir": real})

    for pattern in ("outputs/defense_read_access/**/results.json",
                    "outputs/image_presence_threshold/**/results.json"):
        for rj in glob.glob(os.path.join(root, pattern), recursive=True):
            d = _load_cell(rj)
            campaign = d.get("campaign")
            if campaign in tables.CAMPAIGNS:
                add("as7_campaigns", os.path.dirname(rj))
            elif campaign == DEPLOYABLE_CAMPAIGN:
                add("deployable_grid", os.path.dirname(rj))

    # Refusal numbers reach gpt-5-mini by rejudge, not by a fresh run, so the
    # rejudge dirs are first-class release members (as7_tables.collect does not
    # walk them -- that gap is why this emitter reads them directly).
    for rj in glob.glob(os.path.join(root, "outputs/defense_read_access/rejudge/**/results.json"),
                        recursive=True):
        add("as7_campaigns_rejudge", os.path.dirname(rj))

    cells = may.scan(root)
    for (model, chain), defs in may.TAB_MAIN.items():
        for defense, (t_asr, d_asr) in defs.items():
            for asr, arm in ((t_asr, "text"), (d_asr, "decoy")):
                for c in cells.get((model, defense, chain, arm), []):
                    if round(c["asr"]) == round(asr):
                        add("granted_grid", c["dir"])
    return sorted(picked.values(), key=lambda x: (x["group"], x["dir"]))


def emit(root: str = ".") -> int:
    out_root = os.path.join(root, OUT_ROOT)
    os.makedirs(out_root, exist_ok=True)
    index = []
    empty = []
    for item in _gather(root):
        cell_dir, group = item["dir"], item["group"]
        d = _load_cell(os.path.join(cell_dir, "results.json"))
        rows = _per_prompt(cell_dir)
        if not rows:
            empty.append(os.path.relpath(cell_dir, os.path.abspath(root)))
            continue
        group_dir = os.path.join(out_root, group)
        os.makedirs(group_dir, exist_ok=True)
        name = _slug(cell_dir)
        with open(os.path.join(group_dir, f"{name}.jsonl"), "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        index.append({
            "group": group, "file": f"{group}/{name}.jsonl",
            "target_model": d.get("target_model"), "defense": d.get("defense"),
            "defense_config": d.get("defense_config"), "guard_model": d.get("guard_model"),
            "transformation_list": d.get("transformation_list"),
            "benchmark": d.get("benchmark"), "judge_model": d.get("judge_model"),
            "judge_method": d.get("judge_method"), "campaign": d.get("campaign"),
            "mode": d.get("mode"), "n_rows": len(rows),
            "asr": d.get("asr"), "refusal_rate": d.get("refusal_rate"),
            "eval_stats": d.get("eval_stats"), "git_sha": d.get("git_sha"),
            "stored_dir": os.path.relpath(cell_dir, os.path.abspath(root)),
        })
    with open(os.path.join(out_root, "index.json"), "w") as fh:
        json.dump({"cells": index}, fh, indent=1, sort_keys=True)
    by_group: dict[str, int] = {}
    for c in index:
        by_group[c["group"]] = by_group.get(c["group"], 0) + 1
    print(f"wrote {len(index)} cells to {OUT_ROOT}")
    for g, n in sorted(by_group.items()):
        print(f"  {n:4d}  {g}")
    if empty:
        # Loud, never silent: a cell with no stored per-prompt file cannot be
        # part of a release that claims every number recomputes.
        print(f"  !! {len(empty)} cells have no raw_results.jsonl and were SKIPPED:")
        for e in empty[:10]:
            print("     ", e)
    return 0


def verify(root: str = ".") -> int:
    """Recompute each cell's headline metric from the EMITTED file."""
    index_path = os.path.join(root, OUT_ROOT, "index.json")
    if not os.path.exists(index_path):
        print("no release found -- run `emit` first", file=sys.stderr)
        return 1
    with open(index_path) as fh:
        cells = json.load(fh)["cells"]
    bad = []
    for c in cells:
        rows = [json.loads(l) for l in open(os.path.join(root, OUT_ROOT, c["file"]))]
        judged = [r for r in rows if r["asr"] is not None]
        stored = (c.get("eval_stats") or {}).get("HarmBenchEvaluator") or {}
        if "success_count" in stored and judged:
            got = 100.0 * sum(1 for r in judged if r["asr"]) / len(judged)
            want = 100.0 * stored["success_count"] / stored["total_evaluated"]
            if abs(got - want) > 0.05:
                bad.append(f"{c['file']}: recomputed ASR {got:.1f} != stored {want:.1f}")
    print(f"verify: {len(cells)} cells, {len(cells) - len(bad)} reproduce their stored metric")
    for b in bad:
        print("  !!", b)
    return 1 if bad else 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "emit"
    if cmd == "emit":
        raise SystemExit(emit())
    if cmd == "verify":
        raise SystemExit(verify())
    raise SystemExit(f"unknown command {cmd!r} (emit | verify)")
