"""Paper B (AS-2) — statistics for the 2026-08-05 method-fidelity re-collection.

Recomputes, on the FIXED-encoder cells only, the two things the paper asserts and
that the re-collection invalidated:

  * per-cell ASR with Wilson 95% intervals;
  * the paired text-vs-decoy contrast per (target, defense) via an exact two-sided
    McNemar test on prompt-matched outcomes.

Pairing is by prompt `id` across the two arms, which is valid here because both arms
descend from ONE encoding (the preset builds text and decoy from the same
`prompt_transform` run) -- the same property the paper relies on for its own pairing.

`wilson`, `mcnemar_exact` and `flags` are imported from `paper_c_stats` rather than
reimplemented, so AS-2 and AS-3 report the same statistics the same way.

Also runs the short-circuit check: ECSO on text input returns the initial response
unchanged (`if not is_multimodal: return initial`), so ECSO-text and no_defense-text
should be byte-identical per prompt. The re-collection measured 2-3pp ASR gaps where
that predicts 0.0, so this compares the stored response strings directly and reports
how many differ -- distinguishing "judge flip noise on identical text" (the paper's
stated explanation) from "the responses actually differ".

Usage:
    python -m src.analysis.paper_b_fidelity_stats
"""

from __future__ import annotations

import glob
import json
import os
from collections import defaultdict

from .paper_c_stats import flags, mcnemar_exact, wilson

GRID_GLOB = "outputs/image_presence_threshold/defense+evaluate/harmbench/*"

# Explicit allow-list, not a `paper_b_` prefix match: this working tree is shared
# with concurrent sessions, and at least one other campaign
# (`paper_b_oracle_rerun_free`) writes to the same directory. A prefix match would
# silently mix another session's cells into these statistics.
CAMPAIGNS = (
    "paper_b_fidelity_regrid",           # + _camo, _sage, _claude_probe suffixes
    "paper_b_mechanism_sweep",
)


def _arm(source_dir: str) -> str:
    """text arm = the encoder step; decoy arm = the image step."""
    base = os.path.basename(source_dir.rstrip("/"))
    return "text" if base in ("code_attack", "llm_semantic_camo") else "decoy"


def _load() -> dict:
    """(attack, target, defense, arm) -> dict with dir, asr, n, per-prompt flags."""
    cells = {}
    for d in sorted(glob.glob(GRID_GLOB)):
        f = os.path.join(d, "results.json")
        if not os.path.exists(f):
            continue
        try:
            r = json.load(open(f))
        except Exception:
            continue
        camp = str(r.get("campaign", ""))
        if not camp.startswith(CAMPAIGNS):
            continue
        src = (r.get("upstream_ref") or {}).get("source_dir", "")
        attack = "semantic_camo" if "semantic_camo" in src else "code_attack"
        key = (attack, str(r.get("target_model")), str(r.get("defense")), _arm(src))
        st = (r.get("eval_stats") or {}).get("HarmBenchEvaluator", {})
        # Latest-wins is unsafe in this repo; a duplicate key is a real ambiguity.
        if key in cells:
            print(f"  !! DUPLICATE cell for {key}: {cells[key]['dir']} vs {d}")
        cells[key] = {
            "dir": d,
            "asr": r.get("asr"),
            "n": st.get("total_evaluated"),
            "k": st.get("success_count"),
            "flags": flags(d),
        }
    return cells


def main() -> None:
    cells = _load()
    print(f"loaded {len(cells)} fixed-encoder cells\n")

    # ---- per-cell ASR + Wilson ----
    print("=" * 92)
    print("PER-CELL ASR with Wilson 95% CI")
    print("=" * 92)
    print(f"{'attack':15}{'target':23}{'defense':12}{'arm':7}{'ASR':>7}{'n':>5}   Wilson 95% CI")
    for key in sorted(cells):
        c = cells[key]
        k, n = c["k"], c["n"]
        lo, hi = wilson(k, n) if (k is not None and n) else (float("nan"),) * 2
        print(f"{key[0]:15}{key[1]:23}{key[2]:12}{key[3]:7}"
              f"{c['asr']:>7}{n:>5}   [{lo:5.1f}, {hi:5.1f}]")

    # ---- paired text-vs-decoy McNemar ----
    print()
    print("=" * 92)
    print("PAIRED text-vs-decoy contrast (exact two-sided McNemar)")
    print("  b = harmful on TEXT but not DECOY (decoy helped the defense)")
    print("  c = harmful on DECOY but not TEXT")
    print("=" * 92)
    print(f"{'attack':15}{'target':23}{'defense':12}{'amp pp':>8}{'b':>5}{'c':>5}"
          f"{'paired':>8}  p-value       verdict")
    combos = sorted({(a, t, d) for (a, t, d, _) in cells})
    n_sig = n_tested = 0
    for attack, target, defense in combos:
        ct = cells.get((attack, target, defense, "text"))
        cd = cells.get((attack, target, defense, "decoy"))
        if not ct or not cd:
            print(f"{attack:15}{target:23}{defense:12}"
                  f"{'--':>8}{'--':>5}{'--':>5}{'--':>8}  "
                  f"(no pair: missing {'decoy' if ct else 'text'} arm)")
            continue
        ft, fd = ct["flags"], cd["flags"]
        shared = sorted(set(ft) & set(fd))
        b = sum(1 for i in shared if ft[i] and not fd[i])
        c = sum(1 for i in shared if fd[i] and not ft[i])
        p = mcnemar_exact(b, c)
        amp = ct["asr"] - cd["asr"]
        n_tested += 1
        sig = p < 0.05
        n_sig += bool(sig)
        verdict = "significant" if sig else "NOT significant"
        print(f"{attack:15}{target:23}{defense:12}{amp:>+8.2f}{b:>5}{c:>5}"
              f"{len(shared):>8}  {p:.3e}  {verdict}")
    print(f"\n  {n_sig}/{n_tested} contrasts significant at p<0.05")

    # ---- short-circuit byte-identity check ----
    print()
    print("=" * 92)
    print("SHORT-CIRCUIT CHECK — ECSO-text vs no_defense-text should be byte-identical")
    print("=" * 92)
    checked = 0
    for attack, target, _d in sorted({(a, t, None) for (a, t, _, _) in cells}):
        e = cells.get((attack, target, "ecso", "text"))
        n = cells.get((attack, target, "no_defense", "text"))
        if not e or not n:
            continue
        checked += 1
        er = {json.loads(l)["id"]: json.loads(l).get("response", "")
              for l in open(os.path.join(e["dir"], "raw_results.jsonl")) if l.strip()}
        nr = {json.loads(l)["id"]: json.loads(l).get("response", "")
              for l in open(os.path.join(n["dir"], "raw_results.jsonl")) if l.strip()}
        shared = sorted(set(er) & set(nr))
        differ = [i for i in shared if er[i] != nr[i]]
        ef, nf = e["flags"], n["flags"]
        flips = [i for i in shared if ef.get(i) != nf.get(i)]
        flips_on_identical = [i for i in flips if er[i] == nr[i]]
        print(f"  {attack} / {target}")
        print(f"    ASR: ecso-text {e['asr']} vs no_defense-text {n['asr']}"
              f"  (gap {e['asr'] - n['asr']:+.1f}pp)")
        print(f"    responses differing: {len(differ)}/{len(shared)}"
              f"   judge flips: {len(flips)}"
              f"   flips on BYTE-IDENTICAL responses: {len(flips_on_identical)}")
        if differ:
            print(f"      -> responses are NOT byte-identical; the short-circuit is not "
                  f"the whole story (example id: {differ[0]})")
        elif flips:
            print("      -> responses identical, judge disagreed with itself: "
                  "judge nondeterminism, matching the paper's stated explanation")
    if not checked:
        print("  (no target has both ecso-text and no_defense-text on one attack)")


if __name__ == "__main__":
    main()
