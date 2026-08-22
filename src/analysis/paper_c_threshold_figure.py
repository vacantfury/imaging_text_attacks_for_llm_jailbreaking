"""Threshold-sweep FIGURE — the swept curves review-7 con 1 asks to see.

The paper reports the sweep numerically (a best-operating-point table plus a
multi-budget table). Con 1's remaining half is that a *curve* is what actually
distinguishes a mis-calibrated guard from a genuine ceiling: a table of chosen
points still invites "you picked the wrong points". Plotting every achievable
(over-refusal, ensemble-ASR) pair per guard removes that objection --- the
reader sees the whole reachable set.

This reuses the sweep machinery in `paper_c_guard_threshold` rather than
re-deriving it, so the figure and the tables cannot drift apart.

Usage::

    python -m src.analysis.paper_c_threshold_figure outputs/autoattack_defense/guard_scores/<ts>
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .guard_threshold import load_config, load_records, sweep_guard
from .paper_c_guard_threshold import load_benign_floor_labels, load_floor_labels

# ⚠️ STALE BEFORE THE 2026-08-22 refactor, not caused by it: `as-3/latex/` has
# not existed since the 2026-08-01 paper-dir reorganization. Left pointing at
# the mechanically-updated path so the breakage stays visible; the live Paper-C
# figure dir is `as-3/aaai_2027_ai_alignment/aaai_aia_latex/figs` (see
# paper_c_figures.py FIGS_ALT). Repoint deliberately when this script next runs.
FIGS = "paper/my_papers/as-3/latex/figs"

# Display names + a stable colour per guard, matching the other Paper-C figures.
GUARDS = {
    "wildguard":           ("WildGuard",        "#1f77b4"),
    "llama_guard_3_8b":    ("LlamaGuard-3",     "#e6b800"),
    "qwen3guard_gen_8b":   ("Qwen3Guard",       "#2ca02c"),
    "thinkguard":          ("ThinkGuard",       "#d62728"),
    "guardreasoner_vl_7b": ("GuardReasoner-VL", "#9467bd"),
}
BUDGET = 35.0   # the over-refusal budget the main text argues from


def main(argv: Optional[list[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(__doc__)
        return 2

    cfg = load_config()
    harmful_labels, floor_asr = load_floor_labels()
    benign_labels, benign_floors = load_benign_floor_labels()
    benign_floor = 100 * (sum(benign_floors.values()) / len(benign_floors)) \
        if benign_floors else None

    files = sorted({p for d in (Path(a) for a in argv) for p in d.glob("*.jsonl")})
    if not files:
        print(f"no capture JSONL under {argv}")
        return 2

    fig, ax = plt.subplots(figsize=(3.5, 2.9))

    # Budget band + benign floor: the two reference lines the argument rests on.
    ax.axvspan(0, BUDGET, color="0.90", zorder=0)
    ax.text(BUDGET - 1, 96, f"$\\leq${BUDGET:.0f}% budget", fontsize=6,
            ha="right", va="top", color="0.35")
    if benign_floor is not None:
        # Line only, no inline label: at x~26 every free spot collides with
        # either the legend or the LlamaGuard-3 curve. The caption names it.
        ax.axvline(benign_floor, color="0.55", lw=0.8, ls=":", zorder=1)
    ax.axhline(100 * floor_asr, color="0.55", lw=0.8, ls="--", zorder=1)
    ax.text(2, 100 * floor_asr - 2, f"undefended {100*floor_asr:.0f}%",
            fontsize=6, color="0.35", va="top")

    for path in files:
        label, colour = GUARDS.get(path.stem, (path.stem, None))
        curve = sweep_guard(load_records(path), harmful_labels, benign_labels, cfg)
        pts = sorted(curve.points, key=lambda p: p.over_refusal)
        xs = [100 * p.over_refusal for p in pts]
        ys = [100 * p.ensemble_asr for p in pts]
        ax.plot(xs, ys, "-", color=colour, lw=1.2, label=label, zorder=3)

        # The shipped operating point: same rule as the tables (first grid cut
        # strictly above 0.5 — see paper_c_guard_threshold.main for why).
        above = [p for p in curve.points if p.threshold > 0.50]
        shipped = min(above, key=lambda p: p.threshold) if above else None
        if shipped is not None:
            ax.plot(100 * shipped.over_refusal, 100 * shipped.ensemble_asr,
                    "o", color=colour, ms=4.5, mec="white", mew=0.7, zorder=4)

    ax.set_xlabel("Benign over-refusal (%)", fontsize=8)
    ax.set_ylabel("Ensemble ASR (%)", fontsize=8)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=5.6, loc="lower left", frameon=False, ncol=1)
    fig.tight_layout()
    fig.savefig(FIGS + "/threshold_curves.pdf")
    fig.savefig(FIGS + "/threshold_curves.png", dpi=300)
    print(f"wrote {FIGS}/threshold_curves.pdf (+.png)")
    print("Markers = as-shipped operating point; curves = every reachable cut.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
