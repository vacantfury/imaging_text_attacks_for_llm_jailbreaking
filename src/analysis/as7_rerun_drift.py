"""AS-7 · campaign-level drift measured from cells that were collected twice.

WHY THIS EXISTS. Review 1, con 4: the paper reports single-campaign point
estimates and acknowledges run-to-run drift, but never quantifies it, so a reader
cannot tell whether a reported effect exceeds the noise between collections. A
full answer needs fresh repeated campaigns. This is the part that needs no new
data: several cells were, in the course of building the paper, collected more
than once on different days -- those pairs ARE repeated measurements, and the
spread across them is a measured drift band.

⚠️ THE HARD PART IS DECIDING WHAT COUNTS AS A RERUN, AND THE OBVIOUS KEY IS
WRONG THREE TIMES OVER. Two cells are the same experiment only if EVERY one of
the following matches; each was found the hard way, and each silently inflated
the drift band by merging distinct conditions:

  1. `target_model`, `defense`, `benchmark`, `judge_model`  -- the obvious ones.
  2. `upstream_ref.source_dir` EXACTLY, not the step name. Two dirs can both end
     in `ir_plain` and be different experiments: with `keep_text=False` the
     payload is RELOCATED into the image and the text channel is a placeholder,
     with `keep_text=True` the text keeps the payload and the image is a
     REDUNDANT copy. Merging them produced a fake 44-point "drift".
  3. The FULL `defense_config` dict, not selected keys. `{"as_system": true}`
     (SAGE delivered as a system message) versus `{}` (SAGE wrapping the user
     turn) are different defenses: on gpt-4o-mini/formal_logic the first scores
     43 and the second scores 0. Merging them produced a fake 43-point "drift".
  4. `system_message` -- which is a TASK-level field and is NOT part of
     `defense_config`. The stacked-defense arm runs `defense: ecso` with a SAGE
     system message on top; its recorded config is byte-identical to plain ECSO.
     Merging them produced a fake 51-point "drift" (8 vs 59).

Point 4 is a provenance gap worth knowing about generally: a cell's CONDITION is
not recoverable from `defense_config` alone. Any analysis that groups cells by
config -- drift, replication, latest-wins selection -- must also key on the
system message, or it will compare different experiments and report the
difference as noise.

    python3 src/analysis/as7_rerun_drift.py
    python3 src/analysis/as7_rerun_drift.py --tex PATH   # verify vs the paper

Stdlib only, like its sibling modules.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import glob
import hashlib
import json
import os
import re
import statistics
import sys

ROOTS = ("outputs/image_presence_threshold/defense+evaluate/*/*/results.json",
         "outputs/defense_read_access/defense+evaluate/*/*/results.json")


def _stamp(dirname: str):
    m = re.search(r"_(20\d{6})_(\d{6})_", dirname + "_")
    if not m:
        return None
    return datetime.datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")


def gather(root: str = ".") -> dict:
    recs = collections.defaultdict(list)
    for pat in ROOTS:
        for p in glob.glob(os.path.join(root, pat)):
            try:
                with open(p) as fh:
                    d = json.load(fh)
            except Exception:
                continue
            if d.get("asr") is None:
                continue
            src = ((d.get("upstream_ref") or {}).get("source_dir")
                   or d.get("source_transform_subdir") or "")
            t = _stamp(os.path.basename(os.path.dirname(p)))
            if not src or t is None:
                continue
            key = (
                str(d.get("target_model")),
                str(d.get("defense")),
                json.dumps(d.get("defense_config") or {}, sort_keys=True),
                src,
                str(d.get("benchmark")),
                str(d.get("judge_model")),
                # system_message is task-level and NOT in defense_config -- see
                # point 4 in the module docstring. Hashed only to keep the key small.
                hashlib.sha1((d.get("system_message") or "").encode()).hexdigest()[:8],
            )
            recs[key].append((t, round(d["asr"])))
    return recs


def spreads(recs) -> list[tuple]:
    out = []
    for k, v in recs.items():
        days = {t.strftime("%Y-%m-%d") for t, _ in v}
        if len(days) < 2:                 # same-job duplicates are not reruns
            continue
        vals = sorted(a for _, a in v)
        out.append((k, vals, vals[-1] - vals[0], len(days)))
    return sorted(out, key=lambda r: -r[2])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--tex")
    a = ap.parse_args()

    rows = spreads(gather(a.root))
    if not rows:
        print("no repeated collections found", file=sys.stderr)
        return 1
    sp = sorted(r[2] for r in rows)
    print(f"% campaign-level drift: {len(rows)} cells collected on >1 day, "
          f"all confounds held fixed")
    for k, vals, s, nd in rows:
        print(f"%   {k[0]:22} {k[1]:15} {os.path.basename(k[3].rstrip('/'))[:18]:18} "
              f"vals={vals} spread={s:>3}")
    med = statistics.median(sp)
    p90 = sp[int(0.9 * (len(sp) - 1))]
    print(f"%\n% n={len(sp)}  min={sp[0]}  median={med:.0f}  mean={statistics.mean(sp):.1f}  "
          f"p90={p90}  max={sp[-1]} pp")

    if a.tex:
        tex = open(a.tex).read()
        need = [str(int(med)), str(p90), str(sp[-1]), str(len(sp))]
        missing = [n for n in need
                   if not re.search(rf"(?<![0-9.]){n}(?![0-9.])", tex)]
        if missing:
            print(f"\nMISSING FROM TEX: {missing}", file=sys.stderr)
            return 1
        print(f"\nverify OK -- drift band (n={len(sp)}, median {med:.0f}, "
              f"p90 {p90}, max {sp[-1]}) appears in {a.tex}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
