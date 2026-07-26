"""Paper-D (`bestofn_attack`) figures, built from the R7 gpt-5-mini rejudge dirs.

Two figures, both read-only over saved per-draw judgments (no model calls):

  fig1_asr_vs_n.pdf      union ASR@N per target, attack x defense -- shows the
                         SemanticSmooth crossover at N~10 and SAGE's flat curves.
  fig2_metric_flip.pdf   undefended coverage vs median QtFS side by side -- the
                         paper's methodological point: coverage ranks the two
                         attacks as near-equals (and on Llama ranks the WEAKER
                         one higher), while query cost differs ~10x.

Estimators (identical to text_docs/bestofn_attack/experiment_results.md):
  union ASR@N = mean_behaviors[1 - C(M-k, N)/C(M, N)]   exact over random
                N-subsets, so it is unbiased and low-variance (NOT a first-N
                prefix, which would be one noisy sample of the same quantity).
  QtFS        = (M+1)/(k+1), the expected index of the first success under a
                random draw ordering; behaviors with k=0 are censored and
                excluded from the median (coverage already reports them).

Usage:  python -m src.analysis.paper_d_figures [--outdir DIR]
"""

from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import statistics
from math import comb

CAMPAIGN = "bestofn_attack_p1_text_full_mini"
REJUDGE_GLOB = "outputs/bestofn_attack/rejudge/**/*"
DEFAULT_OUTDIR = "paper/bestofn_attack/latex/figs"

TARGETS = ["llama", "qwen", "gemma"]
TARGET_LABEL = {
    "llama": "Llama-3.1-8B",
    "qwen": "Qwen2.5-7B",
    "gemma": "Gemma-2-9B",
}
DEFENSES = ["no_defense", "sage", "semantic_smooth"]
DEFENSE_LABEL = {
    "no_defense": "no defense",
    "sage": "SAGE",
    "semantic_smooth": "SemanticSmooth",
}
# Colorblind-safe (Okabe-Ito): defense -> colour, attack -> linestyle/hatch.
DEFENSE_COLOR = {
    "no_defense": "#0072B2",
    "sage": "#009E73",
    "semantic_smooth": "#D55E00",
}
ATTACK_LABEL = {"code": "BoN-wrapped CodeAttack", "surf": "original BoN"}
N_GRID = [1, 2, 3, 5, 7, 10, 15, 20, 30, 50, 70, 100]


def _classify(basename: str) -> tuple[str, str, str]:
    target = (
        "llama" if basename.startswith("llama")
        else "qwen" if basename.startswith("qwen")
        else "gemma"
    )
    defense = (
        "no_defense" if "_no_defense_" in basename
        else "sage" if "_sage_" in basename
        else "semantic_smooth"
    )
    attack = "code" if "code_attack" in basename else "surf"
    return target, defense, attack


def load_cells(root: str = ".") -> dict[tuple[str, str, str], tuple[collections.Counter, collections.Counter]]:
    """(target, defense, attack) -> (successes per behavior, draws per behavior)."""
    cells: dict[tuple[str, str, str], tuple[collections.Counter, collections.Counter]] = {}
    for d in glob.glob(os.path.join(root, REJUDGE_GLOB), recursive=True):
        results = os.path.join(d, "results.json")
        if not os.path.exists(results):
            continue
        meta = json.load(open(results))
        if meta.get("campaign") != CAMPAIGN:
            continue
        upstream = os.path.basename((meta.get("upstream_ref") or {}).get("source_dir", ""))
        hits: collections.Counter = collections.Counter()
        draws: collections.Counter = collections.Counter()
        for line in open(os.path.join(d, "raw_results.jsonl")):
            row = json.loads(line)
            behavior = row["id"].rsplit("__", 1)[0]
            draws[behavior] += 1
            if row.get("asr"):
                hits[behavior] += 1
        cells[_classify(upstream)] = (hits, draws)
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
    path = os.path.join(outdir, "fig1_asr_vs_n.pdf")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def fig_metric_flip(cells, outdir: str) -> str:
    """Undefended only: coverage says one thing, query cost says another."""
    import matplotlib.pyplot as plt
    import numpy as np

    cov = {a: [] for a in ("code", "surf")}
    qtfs = {a: [] for a in ("code", "surf")}
    for target in TARGETS:
        for attack in ("code", "surf"):
            c, q = coverage_and_qtfs(*cells[(target, "no_defense", attack)])
            cov[attack].append(c)
            qtfs[attack].append(q if q is not None else float("nan"))

    x = np.arange(len(TARGETS))
    width = 0.36
    fig, (ax_cov, ax_cost) = plt.subplots(1, 2, figsize=(8.2, 3.0))

    for ax, data, ylabel, logy in (
        (ax_cov, cov, "coverage = ASR@$N$=100 (%)", False),
        (ax_cost, qtfs, "median queries to first success", True),
    ):
        ax.bar(x - width / 2, data["code"], width, label=ATTACK_LABEL["code"],
               color="#0072B2", edgecolor="none")
        ax.bar(x + width / 2, data["surf"], width, label=ATTACK_LABEL["surf"],
               color="#E69F00", edgecolor="none")
        ax.set_xticks(x)
        ax.set_xticklabels([TARGET_LABEL[t] for t in TARGETS], fontsize=8.5)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.grid(axis="y", alpha=0.25, linewidth=0.5)
        ax.set_axisbelow(True)
        ax.tick_params(labelsize=8)
        if logy:
            ax.set_yscale("log")
        for xi, (a, b) in enumerate(zip(data["code"], data["surf"])):
            ax.text(xi - width / 2, a, f"{a:.0f}" if not logy else f"{a:.1f}",
                    ha="center", va="bottom", fontsize=7.5)
            ax.text(xi + width / 2, b, f"{b:.0f}" if not logy else f"{b:.1f}",
                    ha="center", va="bottom", fontsize=7.5)

    ax_cov.set_ylim(0, 105)
    ax_cov.set_title("coverage ranks them as near-equals", fontsize=9.5)
    ax_cost.set_title("query cost differs by ~10$\\times$", fontsize=9.5)
    ax_cov.legend(fontsize=8, frameon=False, loc="lower right")
    fig.tight_layout()
    path = os.path.join(outdir, "fig2_metric_flip.pdf")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", default=DEFAULT_OUTDIR)
    parser.add_argument("--root", default=".", help="repo root containing outputs/")
    args = parser.parse_args()

    cells = load_cells(args.root)
    expected = len(TARGETS) * len(DEFENSES) * 2
    if len(cells) != expected:
        raise SystemExit(
            f"expected {expected} cells for campaign {CAMPAIGN}, found {len(cells)} — "
            "sync outputs/ or check the campaign tag"
        )
    os.makedirs(args.outdir, exist_ok=True)
    for path in (fig_asr_vs_n(cells, args.outdir), fig_metric_flip(cells, args.outdir)):
        print("wrote", path)


if __name__ == "__main__":
    main()
