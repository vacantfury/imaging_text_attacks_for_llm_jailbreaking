"""AS-7 reproducibility manifest -- generated, never hand-typed.

WHY THIS EXISTS. Review round 3 (con 6 / Q4) asked for a per-table experiment
manifest: collection dates, exact model identifiers, decoding configuration,
judge version, and whether a result is a first campaign or a replication. Every
one of those facts is already stored in each cell's `results.json` provenance
block, so the manifest is GENERATED from the data rather than maintained by hand
-- the same rule the paper's tables follow (see as7_tables.py).

Deliberately dependency-free (stdlib only, no `src` import) so it runs under a
bare login-node python3 where llm_utils is not installed.

    python3 src/analysis/as7_manifest.py            # human-readable
    python3 src/analysis/as7_manifest.py --latex    # the appendix table body
"""

import argparse
import collections
import glob
import json
import os
import re

# Campaign -> (paper surface it backs, whether it is an independent replication).
# Kept explicit rather than inferred: "which table does this campaign feed" is a
# fact about the paper, not about the data, and a wrong guess here would be a
# silently misleading manifest.
CAMPAIGNS = {
    "as7_channel_asr":         ("Channel coverage (harmful)",      False),
    "as7_benign_channel":      ("Channel coverage (benign)",       False),
    "paper_b_guard_channel":   ("Channel coverage (third target)", False),
    "as7_protocol_grant":      ("Protocol grid",                   False),
    "as7_protocol_grant_rep2": ("Protocol grid",                   True),
    "as7_read_position":       ("Within-defense read isolation",   False),
}

OUTPUT_GLOBS = (
    "outputs/**/defense+evaluate/**/results.json",
    "outputs/**/rejudge/**/results.json",
)

# Directories holding withdrawn or superseded cells. Excluded by name: they sit
# under the same campaign tags as live cells, so a scan that forgets them
# reports numbers the paper does not use.
EXCLUDE = ("_quarantine", "_QUARANTINE", "_superseded", "_invalid")

DATE_RE = re.compile(r"_(\d{4})(\d{2})(\d{2})_\d{6}_")


def collect(root="."):
    agg = collections.defaultdict(lambda: {
        "cells": 0, "sha": set(), "dirty": set(), "judges": set(),
        "jhash": set(), "dates": set(), "decoding": set(), "targets": set(),
        "guards": set(), "n": set(),
    })
    seen = set()
    for pattern in OUTPUT_GLOBS:
        for rj in glob.glob(os.path.join(root, pattern), recursive=True):
            if rj in seen or any(x in rj for x in EXCLUDE):
                continue
            seen.add(rj)
            try:
                with open(rj) as fh:
                    d = json.load(fh)
            except (OSError, ValueError):
                continue
            camp = d.get("campaign")
            if camp not in CAMPAIGNS:
                continue
            a = agg[camp]
            a["cells"] += 1
            a["sha"].add(str(d.get("git_sha"))[:7])
            a["dirty"].add(bool(d.get("git_dirty")))
            a["judges"].add(str(d.get("judge_model")))
            a["jhash"].add(str(d.get("judge_config_hash"))[:8])
            a["targets"].add(str(d.get("target_model")))
            g = (d.get("defense_config") or {}).get("guard_model")
            if g:
                a["guards"].add(str(g))
            m = DATE_RE.search(os.path.basename(os.path.dirname(rj)))
            if m:
                a["dates"].add("-".join(m.groups()))
            tc = d.get("target_model_config") or {}
            a["decoding"].add(json.dumps(
                {k: tc[k] for k in ("temperature", "top_p", "max_tokens") if k in tc},
                sort_keys=True))
            ev = d.get("eval_stats") or {}
            for v in ev.values():
                if isinstance(v, dict) and v.get("total_evaluated"):
                    a["n"].add(v["total_evaluated"])
    return agg


def _span(dates):
    ds = sorted(dates)
    if not ds:
        return "--"
    return ds[0] if len(ds) == 1 else f"{ds[0]}/{ds[-1]}"


def _decoding_line(agg):
    """One shared decoding config across every campaign is worth stating once."""
    all_dec = {d for a in agg.values() for d in a["decoding"] if d and d != "{}"}
    return all_dec.pop() if len(all_dec) == 1 else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    ap.add_argument("--latex", action="store_true")
    args = ap.parse_args()
    agg = collect(args.root)
    shared = _decoding_line(agg)

    if not args.latex:
        for camp, a in sorted(agg.items()):
            surface, rep = CAMPAIGNS[camp]
            print(f"\n{camp}   [{surface}{', REPLICATION' if rep else ''}]")
            print(f"  cells       {a['cells']}   n/cell {sorted(a['n'])}")
            print(f"  collected   {_span(a['dates'])}")
            print(f"  code        git {sorted(a['sha'])}  dirty={sorted(a['dirty'])}")
            print(f"  targets     {sorted(a['targets'])}")
            if a["guards"]:
                print(f"  guards      {sorted(a['guards'])}")
            print(f"  judge       {sorted(a['judges'])}  cfg {sorted(a['jhash'])}")
            print(f"  decoding    {sorted(a['decoding'])}")
        print(f"\nshared decoding across all campaigns: {shared or 'NOT UNIFORM'}")
        return

    for camp, a in sorted(agg.items(), key=lambda kv: CAMPAIGNS[kv[0]][0]):
        surface, rep = CAMPAIGNS[camp]
        camp_tex = camp.replace("_", r"\_")
        judges = ", ".join(sorted(j for j in a["judges"] if j != "None"))
        ns = sorted(a["n"])
        n_tex = str(ns[0]) if len(ns) == 1 else f"{ns[0]}--{ns[-1]}"
        print(f"\\texttt{{{camp_tex}}} & {surface}"
              f"{' (rep.)' if rep else ''} & {a['cells']} & {n_tex} & "
              f"{_span(a['dates'])} & \\texttt{{{judges.replace('_', chr(92)+'_')}}} & "
              f"{len(a['sha'])} \\\\")


if __name__ == "__main__":
    main()
