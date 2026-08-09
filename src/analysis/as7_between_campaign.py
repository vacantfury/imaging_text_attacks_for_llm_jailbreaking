"""AS-7 · between-campaign uncertainty on the oracle-vs-deployable gaps.

WHY THIS EXISTS. Both cspaper reviews required it independently (review 1 con 4;
review 2 con 9 + Q3): the paper's McNemar tests are prompt-paired WITHIN one
campaign, while its own drift analysis measures 0-10pp of movement BETWEEN
campaigns on nondeterministic targets. Within-campaign stars therefore cannot by
themselves show that an effect survives recollection. Campaign
`as7_protocol_grant_rep2` is an independent repetition of
`as7_protocol_grant` -- same sources, targets, defenses, configs and judge; only
the collection differs -- and this module reports the per-cell delta.

THE QUANTITY. For each (target, defense, defense_config-minus-query_source,
source_dir) cell we form the protocol GAP

    gap = ASR(query_source=encoded) - ASR(query_source=original)

within each campaign, then report `gap_rep2 - gap_c1`. The gap is the paper's
claim; its between-campaign movement is what the reviewers asked for. Comparing
raw ASRs instead would mix target drift into a quantity that is defined as a
difference, and would overstate instability.

PRE-REGISTERED READ-OUT (fixed before the data landed -- see the preset headers):
  CONFIRMS  every gap the paper calls large stays large and same-signed, and
            |delta| sits within the measured 0-10pp operational drift band.
  NARROWS   large gaps replicate; small/near-null ones move inside the band and
            are reported as indistinguishable from drift rather than as nulls.
  REFUTES   a gap the paper calls large changes sign or falls below the band.
            THIS BRANCH IS REPORTED, NOT RERUN AWAY.

⚠️ SemanticSmooth's ~0 is a SPECIFIED null (its paraphrase step always reads the
encoded prompt; the oracle read reaches only candidate SELECTION), so a non-zero
SS gap in either campaign is a rig fault to diagnose, not a finding.

⚠️ Cells are keyed the way `as7_rerun_drift.py` learned to key them: the exact
`upstream_ref.source_dir`, the FULL defense_config (minus the protocol knob being
contrasted), benchmark, judge and target. Grouping on a defense NAME alone merges
different experiments and manufactures drift.

    python3 src/analysis/as7_between_campaign.py
    python3 src/analysis/as7_between_campaign.py --band 10   # flag |delta| > band

Stdlib only, like its sibling modules.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics
import sys

C1, C2 = "as7_protocol_grant", "as7_protocol_grant_rep2"
ROOTS = ("outputs/image_presence_threshold/defense+evaluate",
         "outputs/defense_read_access/defense+evaluate")


def collect(root: str = ".") -> dict:
    """(campaign, cellkey, protocol) -> asr, for cells that actually scored."""
    out: dict = {}
    for r in ROOTS:
        for p in glob.glob(os.path.join(root, r, "*", "*", "results.json")):
            try:
                j = json.load(open(p))
            except Exception:
                continue
            camp = j.get("campaign")
            if camp not in (C1, C2):
                continue
            if j.get("asr") is None:          # dead judge / unscored -- never impute
                continue
            cfg = dict(j.get("defense_config") or {})
            proto = cfg.pop("query_source", None)
            if proto not in ("original", "encoded"):
                continue                       # denominators carry no protocol arm
            key = (str(j.get("target_model")), str(j.get("defense")),
                   json.dumps(cfg, sort_keys=True),
                   (j.get("upstream_ref") or {}).get("source_dir") or "",
                   str(j.get("benchmark")), str(j.get("judge_model")))
            out.setdefault((camp, key), {})[proto] = round(j["asr"])
    return out


def gaps(rows: dict, camp: str) -> dict:
    g = {}
    for (c, key), arms in rows.items():
        if c != camp:
            continue
        if "original" in arms and "encoded" in arms:
            g[key] = arms["encoded"] - arms["original"]
    return g


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--band", type=float, default=10.0,
                    help="operational drift band in pp (default: the measured 10)")
    a = ap.parse_args()

    rows = collect(a.root)
    g1, g2 = gaps(rows, C1), gaps(rows, C2)
    if not g2:
        print(f"no {C2} cells scored yet -- replicate has not landed", file=sys.stderr)
        print(f"({len(g1)} campaign-1 gap cells are present)", file=sys.stderr)
        return 1

    shared = sorted(set(g1) & set(g2))
    print(f"% paired protocol-gap cells: {len(shared)} "
          f"(c1={len(g1)}, rep2={len(g2)})")
    deltas, flipped, outside = [], [], []
    for k in shared:
        d = g2[k] - g1[k]
        deltas.append(abs(d))
        tgt, dfn, cfg, src = k[0], k[1], k[2], os.path.basename(k[3].rstrip("/"))
        flag = ""
        if g1[k] and g2[k] and (g1[k] > 0) != (g2[k] > 0):
            flag = "  <-- SIGN FLIP"; flipped.append(k)
        elif abs(d) > a.band:
            flag = "  <-- OUTSIDE BAND"; outside.append(k)
        print(f"%   {tgt:14} {dfn:16} {src[:20]:20} "
              f"c1={g1[k]:+4} rep2={g2[k]:+4} delta={d:+4}{flag}")

    if deltas:
        s = sorted(deltas)
        print(f"%\n% |delta|: n={len(s)} min={s[0]} median={statistics.median(s):.0f} "
              f"mean={statistics.mean(s):.1f} max={s[-1]} pp  (band={a.band:g})")
    missing = sorted(set(g1) - set(g2))
    if missing:
        print(f"% NOT REPLICATED ({len(missing)} c1 cells absent from rep2) -- "
              f"report as uncovered, never as agreement")
    if flipped:
        print(f"\nREFUTES branch: {len(flipped)} sign flip(s)", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
