"""Paper-D (`bestofn_attack`) figures, built from the P2 gpt-5-mini rejudge dirs.

Two figures, both read-only over saved per-draw judgments (no model calls):

  fig1_inversion.pdf   attack reach retained under each defense, normalised by
                       that attack's own UNDEFENDED coverage at N=100. The
                       paper's headline shape: against the two TRANSFORM
                       defenses the code encoding survives far better than the
                       character search, and against the GATE the ordering
                       inverts -- so "which attack is stronger" is a property of
                       the defense, not of the attacks.
  fig2_asr_vs_n.pdf    union ASR@N per target, attack x defense -- shows how far
                       a query budget carries each composition, and that SAGE's
                       protection erodes rather than holding flat.

WHICH DATASET. Only the P2 rejudge campaigns are read (`CAMPAIGNS` below). The
earlier P1 campaign is deliberately NOT accepted: its code arm had no best-of-N
variation channel (deterministic template + target temperature 0), so its
union-over-N numbers describe an OR over serving noise rather than an attacker's
search. Per-draw numbers from that round survive; nothing aggregated over N does.
See text_docs/bestofn_attack/experiment_results.md, "R7 VALIDITY DEFECT".

Estimators (identical to text_docs/bestofn_attack/experiment_results.md):
  union ASR@N = mean_behaviors[1 - C(M-k, N)/C(M, N)]   exact over random
                N-subsets, so it is unbiased and low-variance (NOT a first-N
                prefix, which would be one noisy sample of the same quantity).
  QtFS        = (M+1)/(k+1), the expected index of the first success under a
                random draw ordering; behaviors with k=0 are censored and
                excluded from the median (coverage already reports them).

COVERAGE GATE. A failed judge API call is scored "safe" by the HarmBench
evaluator, so a quota trip reads as a LOW ASR rather than an error. Every cell is
therefore gated on total_evaluated == EXPECTED_DRAWS_PER_CELL,
fallback_parse_count == 0 and status == "success" before any number is plotted.
Pass --no-gate only to inspect a known-partial run; never to produce paper figures.

Usage:  python -m src.analysis.paper_d_figures [--outdir DIR] [--root REPO]
"""

from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import statistics
from math import comb

# P2 = the repaired matrix (uniform target temperature 1.0 on BOTH arms).
CAMPAIGNS = {
    "bestofn_attack_p2_rejudge_llama",  # run A: the 6 llama cells
    "bestofn_attack_p2_rejudge_rest",   # run B: 12 qwen + gemma cells
    "bestofn_attack_p2_rejudge_probe",  # run C: 4 probe-count cells (llama)
}
REJUDGE_GLOB = "outputs/bestofn_attack/rejudge/**/*"
DEFAULT_OUTDIR = "paper/bestofn_attack/latex/figs"
EXPECTED_DRAWS_PER_CELL = 10_000  # 100 behaviors x 100 draws

TARGETS = ["llama", "qwen", "gemma"]
TARGET_LABEL = {
    "llama": "Llama-3.1-8B",
    "qwen": "Qwen2.5-7B",
    "gemma": "Gemma-2-9B",
}
# Main matrix (fig2) vs the probe-count panel (fig1's third facet, llama only).
DEFENSES = ["no_defense", "sage", "semantic_smooth"]
PROBE_DEFENSES = ["canonicalize", "canonicalize_guard"]
DEFENSE_LABEL = {
    "no_defense": "no defense",
    "sage": "SAGE",
    "semantic_smooth": "SemanticSmooth",
    "canonicalize": "canonicalize",
    "canonicalize_guard": "canon.$+$guard",
}
# Colorblind-safe (Okabe-Ito): defense -> colour, attack -> linestyle/hatch.
DEFENSE_COLOR = {
    "no_defense": "#0072B2",
    "sage": "#009E73",
    "semantic_smooth": "#D55E00",
    "canonicalize": "#CC79A7",
    "canonicalize_guard": "#56B4E9",
}
ATTACK_LABEL = {"code": "BoN-wrapped CodeAttack", "surf": "original BoN"}
ATTACK_COLOR = {"code": "#c0392b", "surf": "#2c6fb5"}
N_GRID = [1, 2, 3, 5, 7, 10, 15, 20, 30, 50, 70, 100]

# fig1 facets: (title, defense key, targets to show)
INVERSION_PANELS = [
    ("SAGE  (transform)", "sage", TARGETS),
    ("SemanticSmooth  (transform)", "semantic_smooth", TARGETS),
    ("canon.+guard\n(gate)", "canonicalize_guard", ["llama"]),
]


def _classify(basename: str) -> tuple[str, str, str]:
    target = (
        "llama" if basename.startswith("llama")
        else "qwen" if basename.startswith("qwen")
        else "gemma"
    )
    # Order matters: "_canonicalize_guard_" also contains "_canonicalize".
    if "_no_defense_" in basename:
        defense = "no_defense"
    elif "_sage_" in basename:
        defense = "sage"
    elif "_semantic_smooth_" in basename:
        defense = "semantic_smooth"
    elif "_canonicalize_guard_" in basename:
        defense = "canonicalize_guard"
    elif "_canonicalize_" in basename:
        defense = "canonicalize"
    else:
        raise ValueError(f"unrecognised defense in output dir name: {basename}")
    attack = "code" if "code_attack" in basename else "surf"
    return target, defense, attack


def load_cells(
    root: str = ".", gate: bool = True
) -> dict[tuple[str, str, str], tuple[collections.Counter, collections.Counter]]:
    """(target, defense, attack) -> (successes per behavior, draws per behavior)."""
    cells: dict[tuple[str, str, str], tuple[collections.Counter, collections.Counter]] = {}
    failures: list[str] = []
    for d in glob.glob(os.path.join(root, REJUDGE_GLOB), recursive=True):
        results = os.path.join(d, "results.json")
        if not os.path.exists(results):
            continue
        meta = json.load(open(results))
        if meta.get("campaign") not in CAMPAIGNS:
            continue
        upstream = os.path.basename((meta.get("upstream_ref") or {}).get("source_dir", ""))
        if gate:
            stats = (meta.get("eval_stats") or {}).get("HarmBenchEvaluator", {})
            evaluated = stats.get("total_evaluated")
            fallbacks = stats.get("fallback_parse_count")
            if (evaluated != EXPECTED_DRAWS_PER_CELL or fallbacks
                    or meta.get("status") != "success"):
                failures.append(
                    f"{upstream}: status={meta.get('status')} "
                    f"evaluated={evaluated} fallback_parse={fallbacks}"
                )
                continue
        hits: collections.Counter = collections.Counter()
        draws: collections.Counter = collections.Counter()
        for line in open(os.path.join(d, "raw_results.jsonl")):
            row = json.loads(line)
            behavior = row["id"].rsplit("__", 1)[0]
            draws[behavior] += 1
            if row.get("asr"):
                hits[behavior] += 1
        cells[_classify(upstream)] = (hits, draws)
    if failures:
        raise SystemExit(
            "coverage gate FAILED — a silently-safe judge failure would read as a low "
            "ASR, so no figure is produced:\n  " + "\n  ".join(failures)
        )
    return cells


def union_asr_at_n(hits: collections.Counter, draws: collections.Counter, n: int) -> float:
    total = 0.0
    for behavior, m in draws.items():
        k = hits[behavior]
        total += 1.0 if m - k < n else 1.0 - comb(m - k, n) / comb(m, n)
    return 100.0 * total / len(draws)


def coverage_and_qtfs(hits: collections.Counter, draws: collections.Counter) -> tuple[float, float | None]:
    costs = []
    for behavior, m in draws.items():
        k = hits[behavior]
        if k > 0:
            costs.append((m + 1) / (k + 1))
    coverage = 100.0 * len(costs) / len(draws)
    return coverage, (statistics.median(costs) if costs else None)


def fig_inversion(cells, outdir: str) -> str:
    """Retained reach = defended coverage / that attack's own undefended coverage.

    Normalising per (target, attack) is what makes the inversion legible: the two
    attacks have different undefended ceilings, so raw defended coverage would
    conflate "the defense stopped it" with "it was weaker to begin with".
    """
    import matplotlib.pyplot as plt
    import numpy as np

    fig, axes = plt.subplots(
        1, len(INVERSION_PANELS), figsize=(7.2, 2.45), sharey=True,
        gridspec_kw=dict(width_ratios=[3, 3, 1.25], wspace=0.12),
    )
    for ax, (title, defense, targets) in zip(axes, INVERSION_PANELS):
        x = np.arange(len(targets))
        width = 0.34 if len(targets) > 1 else 0.30
        for offset, attack in ((-0.5, "code"), (0.5, "surf")):
            heights = []
            for target in targets:
                defended = union_asr_at_n(*cells[(target, defense, attack)], 100)
                undefended = union_asr_at_n(*cells[(target, "no_defense", attack)], 100)
                heights.append(defended / undefended if undefended else float("nan"))
            bars = ax.bar(x + offset * width, heights, width,
                          color=ATTACK_COLOR[attack], label=ATTACK_LABEL[attack])
            for rect in bars:
                ax.text(rect.get_x() + rect.get_width() / 2, rect.get_height() + 0.025,
                        f"{rect.get_height():.2f}", ha="center", fontsize=6.4, color="0.25")
        ax.set_xticks(x)
        ax.set_xticklabels([TARGET_LABEL[t].split("-")[0] for t in targets], fontsize=8)
        ax.set_title(title, fontsize=8.5, pad=4)
        ax.axhline(1.0, color="0.45", lw=0.8, ls=":")
        ax.set_ylim(0, 1.20)
        ax.set_xlim(-0.62, len(targets) - 0.38)
        ax.tick_params(labelsize=8)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
    axes[0].set_ylabel("retained attack reach\n(defended $\\div$ undefended)", fontsize=8.5)
    axes[0].set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    axes[-1].set_facecolor("#f6f6f6")  # the gate panel, visually set apart

    handles, labels = axes[0].get_legend_handles_labels()
    labels = [f"{labels[0]} (ours)"] + labels[1:]
    fig.legend(handles, labels, fontsize=7.6, frameon=False, loc="lower center",
               bbox_to_anchor=(0.5, -0.08), ncol=2, handlelength=1.3, columnspacing=1.8)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    path = os.path.join(outdir, "fig1_inversion.pdf")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def fig_asr_vs_n(cells, outdir: str) -> str:
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.2), sharey=True)
    for ax, target in zip(axes, TARGETS):
        for defense in DEFENSES:
            for attack, style in (("code", "-"), ("surf", "--")):
                key = (target, defense, attack)
                if key not in cells:
                    continue
                hits, draws = cells[key]
                ys = [union_asr_at_n(hits, draws, n) for n in N_GRID]
                ax.plot(
                    N_GRID, ys, style, color=DEFENSE_COLOR[defense],
                    linewidth=1.7, marker="o" if attack == "code" else None,
                    markersize=2.6,
                )
        ax.set_xscale("log")
        ax.set_xlim(1, 100)
        ax.set_ylim(0, 100)
        ax.set_title(TARGET_LABEL[target], fontsize=10)
        ax.set_xlabel("query budget $N$", fontsize=9)
        ax.grid(alpha=0.25, linewidth=0.5)
        ax.tick_params(labelsize=8)
    axes[0].set_ylabel("union ASR@$N$ (%)", fontsize=9)

    handles = [
        plt.Line2D([], [], color=DEFENSE_COLOR[d], linewidth=1.7, label=DEFENSE_LABEL[d])
        for d in DEFENSES
    ] + [
        plt.Line2D([], [], color="0.35", linewidth=1.7, marker="o", markersize=2.6,
                   label=ATTACK_LABEL["code"]),
        plt.Line2D([], [], color="0.35", linewidth=1.7, linestyle="--", label=ATTACK_LABEL["surf"]),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=5, fontsize=8, frameon=False,
               bbox_to_anchor=(0.5, -0.10))
    fig.tight_layout()
    path = os.path.join(outdir, "fig2_asr_vs_n.pdf")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def print_table(cells) -> None:
    """The main paper's Table 3, so the figures and the table cannot drift apart."""
    header = "{:<9}{:<20}{:<22}{:>9}{:>7}{:>7}{:>8}{:>7}"
    print(header.format("target", "defense", "attack", "per-draw",
                        "N=1", "N=10", "N=100", "QtFS"))
    print("-" * 89)
    for target in TARGETS:
        for defense in DEFENSES + PROBE_DEFENSES:
            for attack in ("code", "surf"):
                key = (target, defense, attack)
                if key not in cells:
                    continue
                hits, draws = cells[key]
                per_draw = 100.0 * sum(hits.values()) / sum(draws.values())
                _, qtfs = coverage_and_qtfs(hits, draws)
                print(header.format(
                    target, DEFENSE_LABEL[defense].replace("$+$", "+"), ATTACK_LABEL[attack],
                    f"{per_draw:.2f}",
                    *[f"{union_asr_at_n(hits, draws, n):.1f}" for n in (1, 10, 100)],
                    f"{qtfs:.1f}" if qtfs else "--",
                ))
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", default=DEFAULT_OUTDIR)
    parser.add_argument("--root", default=".", help="repo root containing outputs/")
    parser.add_argument("--no-gate", action="store_true",
                        help="skip the coverage gate (inspection only — never for paper figures)")
    parser.add_argument("--table", action="store_true", help="also print the main results table")
    args = parser.parse_args()

    cells = load_cells(args.root, gate=not args.no_gate)
    expected = len(TARGETS) * len(DEFENSES) * 2 + len(PROBE_DEFENSES) * 2  # 18 main + 4 probe
    if len(cells) != expected:
        raise SystemExit(
            f"expected {expected} cells across campaigns {sorted(CAMPAIGNS)}, found "
            f"{len(cells)} — sync outputs/ or check the campaign tags"
        )
    os.makedirs(args.outdir, exist_ok=True)
    for path in (fig_inversion(cells, args.outdir), fig_asr_vs_n(cells, args.outdir)):
        print("wrote", path)
    if args.table:
        print()
        print_table(cells)


if __name__ == "__main__":
    main()
