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
# P3 = the review-1 response round (second gate, temperature ablation, 70B target).
CAMPAIGNS = {
    "bestofn_attack_p2_rejudge_llama",  # run A: the 6 llama cells
    "bestofn_attack_p2_rejudge_rest",   # run B: 12 qwen + gemma cells
    "bestofn_attack_p2_rejudge_probe",  # run C: 4 probe-count cells (llama)
    "bestofn_attack_p3_rejudge",        # run D: 2nd gate + T=0.5 + 4 Llama-3.3-70B cells
    "bestofn_attack_p4_rejudge",        # run E: the PUBLISHED gate, no canonicalization prefix
}
REJUDGE_GLOB = "outputs/bestofn_attack/rejudge/**/*"
DEFAULT_OUTDIR = "paper/bestofn_attack/latex/figs"
EXPECTED_DRAWS_PER_CELL = 10_000  # 100 behaviors x 100 draws

# Registry model id -> target key. EXPLICIT, because classifying by name PREFIX is
# unsafe here: "llama_3_3_70b_instruct" and "llama3_1_8b_cluster" both start with
# "llama", so a prefix test silently folds the 70B into the 8B's cells and the last
# one loaded wins. That is a wrong-number bug with no error, so the mapping is a
# lookup with a hard failure on anything unrecognised.
TARGET_MODEL_KEY = {
    "llama3_1_8b_cluster": "llama",
    "llama_3_3_70b_instruct": "llama70",
    "qwen2_5_7b_instruct": "qwen",
    "gemma2_9b_it": "gemma",
}
TARGETS = ["llama", "qwen", "gemma"]          # the published 7-9B panel
TARGETS_WITH_70B = TARGETS + ["llama70"]
TARGET_LABEL = {
    "llama": "Llama-3.1-8B",
    "qwen": "Qwen2.5-7B",
    "gemma": "Gemma-2-9B",
    "llama70": "Llama-3.3-70B",
}
# Axis ticks: TARGET_LABEL.split("-")[0] would render BOTH Llama targets as "Llama",
# so the 8B and 70B bars would be indistinguishable. Short labels are explicit.
TARGET_SHORT = {
    "llama": "Llama\n8B",
    "qwen": "Qwen",
    "gemma": "Gemma",
    "llama70": "Llama\n70B",
}
# Main matrix (fig2) vs the probe-count panel (fig1's gate facets).
DEFENSES = ["no_defense", "sage", "semantic_smooth"]
PROBE_DEFENSES = ["canonicalize", "canonicalize_guard", "canonicalize_guard3",
                  "guard_baseline"]
DEFENSE_LABEL = {
    "no_defense": "no defense",
    "sage": "SAGE",
    "sage_t05": "SAGE ($T{=}0.5$)",
    "semantic_smooth": "SemanticSmooth",
    "canonicalize": "canonicalize",
    "canonicalize_guard": "canon.$+$WildGuard",
    "canonicalize_guard3": "canon.$+$LlamaGuard-3",
    "guard_baseline": "LlamaGuard-3 (as published)",
}
# Colorblind-safe (Okabe-Ito): defense -> colour, attack -> linestyle/hatch.
DEFENSE_COLOR = {
    "no_defense": "#0072B2",
    "sage": "#009E73",
    "sage_t05": "#66C2A5",
    "semantic_smooth": "#D55E00",
    "canonicalize": "#CC79A7",
    "canonicalize_guard": "#56B4E9",
    "canonicalize_guard3": "#E69F00",
    "guard_baseline": "#8C564B",
}
ATTACK_LABEL = {"code": "BoN-wrapped CodeAttack", "surf": "original BoN"}
ATTACK_COLOR = {"code": "#c0392b", "surf": "#2c6fb5"}
N_GRID = [1, 2, 3, 5, 7, 10, 15, 20, 30, 50, 70, 100]

# fig1 facets: (title, defense key, targets to show). The three GATE facets sit
# last and carry the paper's claim that the inversion is a property of gates: the
# first two hold the architecture fixed and swap the classifier, the third drops
# our canonicalization prefix entirely and runs LlamaGuard-3 as it ships.
# Facet titles are kept SHORT and two-line: with five facets the full defense names
# ("canon.+LlamaGuard-3", "LlamaGuard-3 as published") collide horizontally.
INVERSION_PANELS = [
    ("SAGE\n(transform)", "sage", TARGETS_WITH_70B),
    ("SemanticSmooth\n(transform)", "semantic_smooth", TARGETS),
    ("canon.+WildGuard\n(gate)", "canonicalize_guard", ["llama"]),
    ("canon.+LG-3\n(gate)", "canonicalize_guard3", ["llama"]),
    ("LG-3 as shipped\n(gate)", "guard_baseline", ["llama"]),
]


def _classify(meta: dict, upstream_meta: dict) -> tuple[str, str, str]:
    """(target, defense, attack) from RESULT METADATA, not from directory names.

    `meta` is the rejudge results.json (authoritative `target_model` / `defense`);
    `upstream_meta` is the source defense+evaluate results.json, needed for the two
    fields the rejudge does not carry forward: `defense_config.guard_model` and
    `target_model_config.temperature`. Both are load-bearing here because the P3
    round reuses existing (target, defense, attack) triples with a different guard
    classifier and a different temperature, and would otherwise OVERWRITE published
    P2 cells in the returned dict.
    """
    model = meta.get("target_model") or ""
    if model not in TARGET_MODEL_KEY:
        raise ValueError(
            f"unrecognised target_model {model!r} — add it to TARGET_MODEL_KEY "
            f"rather than relying on a name prefix")
    target = TARGET_MODEL_KEY[model]

    defense = meta.get("defense") or ""
    if defense not in ("no_defense", "sage", "semantic_smooth",
                       "canonicalize", "canonicalize_guard", "guard_baseline"):
        raise ValueError(f"unrecognised defense {defense!r} in {meta.get('output_dir')}")

    # Split the gate by its CLASSIFIER: same defense architecture, different model.
    if defense == "canonicalize_guard":
        guard = ((upstream_meta.get("defense_config") or {}).get("guard_model") or "")
        if "llama_guard_3" in guard:
            defense = "canonicalize_guard3"
        elif guard and "wildguard" not in guard:
            raise ValueError(f"unrecognised guard_model {guard!r}; add a defense key")

    # The PUBLISHED gate (no canonicalization prefix) was run on LlamaGuard-3 only.
    # Fail rather than fold a future second classifier into the same key — that is
    # exactly the silent overwrite the guard split above exists to prevent.
    if defense == "guard_baseline":
        guard = ((upstream_meta.get("defense_config") or {}).get("guard_model") or "")
        if "llama_guard_3" not in guard:
            raise ValueError(
                f"guard_baseline with guard_model {guard!r}: only LlamaGuard-3 is "
                f"published; add a distinct defense key before plotting it")

    # Split SAGE by target temperature so the ablation cannot overwrite the T=1.0 cell.
    if defense == "sage":
        temp = (upstream_meta.get("target_model_config") or {}).get("temperature")
        if temp is not None and abs(float(temp) - 1.0) > 1e-9:
            defense = f"sage_t{str(temp).replace('.', '')[:2]}"

    src = os.path.basename((meta.get("upstream_ref") or {}).get("source_dir", ""))
    attack = "code" if "code_attack" in src else "surf"
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

        # The upstream carries guard_model / temperature, which _classify needs to
        # keep P3's reused triples off P2's published cells.
        src_dir = (meta.get("upstream_ref") or {}).get("source_dir", "")
        src_results = os.path.join(root, src_dir, "results.json")
        if not os.path.exists(src_results):
            src_results = os.path.join(src_dir, "results.json")
        upstream_meta = json.load(open(src_results)) if os.path.exists(src_results) else {}
        key = _classify(meta, upstream_meta)

        # A duplicate key means two cells claim the same (target, defense, attack).
        # Silently keeping the last one is precisely how a P3 cell would overwrite a
        # published P2 number, so this is fatal rather than last-write-wins.
        if key in cells:
            failures.append(
                f"DUPLICATE cell {key} — {upstream} collides with an already-loaded "
                f"cell; give one of them a distinct defense/target key")
            continue
        cells[key] = (hits, draws)
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


def bootstrap_ci(hits: collections.Counter, draws: collections.Counter,
                 n: int = 100, resamples: int = 10_000,
                 seed: int = 20260728) -> tuple[float, float]:
    """95% bootstrap interval for union ASR@n, matching the appendix Estimator note.

    Two nested resampling axes, exactly as published: behaviors are resampled with
    replacement, and WITHIN each resample each behavior's success count is redrawn
    as Binomial(M, k_b/M). Union ASR is then recomputed by the exact estimator on
    every resample; we report the 2.5th/97.5th percentiles.

    Seeded so a rerun reproduces the published interval rather than jittering the
    last digit of a number that is already in the paper.
    """
    import numpy as np
    rng = np.random.default_rng(seed)
    behaviors = list(draws)
    nb = len(behaviors)
    ms = np.array([draws[b] for b in behaviors])
    ks = np.array([hits[b] for b in behaviors])

    # P(no success in a random N-subset) as a lookup over k, per distinct M. Vectorising
    # this is what makes 10^4 x 100 x 100 tractable; the arithmetic is the same exact
    # estimator, just precomputed instead of recomputed inside the loop.
    surv = {}
    for m in np.unique(ms):
        m = int(m)
        surv[m] = np.array([0.0 if m - k < n else comb(m - k, n) / comb(m, n)
                            for k in range(m + 1)])

    pick = rng.integers(0, nb, size=(resamples, nb))       # behavior axis
    m_s, k_s = ms[pick], ks[pick]
    k_re = rng.binomial(m_s, np.divide(k_s, m_s, out=np.zeros_like(k_s, dtype=float),
                                       where=m_s > 0))     # draw axis
    stats = np.zeros(resamples)
    for m in np.unique(ms):                                # one pass per distinct M (here: 1)
        m = int(m)
        table = surv[m]
        contrib = np.where(m_s == m, 1.0 - table[np.clip(k_re, 0, m)], 0.0)
        stats += contrib.sum(axis=1)
    stats = 100.0 * stats / nb
    return float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))


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

    # Drop any target a panel has no data for (e.g. SemanticSmooth was never run on
    # the 70B), so adding a target cannot KeyError the whole figure.
    panels = []
    for title, defense, targets in INVERSION_PANELS:
        avail = [t for t in targets
                 if (t, defense, "code") in cells and (t, "no_defense", "code") in cells]
        if avail:
            panels.append((title, defense, avail))
    widths = [max(1.25, 1.0 * len(t)) for _, _, t in panels]

    # Fixed page width: this is a full-width (two-column) float, so the figure must
    # be ~7.6in regardless of how many facets there are — panel COUNT changes the
    # width_ratios, never the total. A width that scales with the facet count would
    # be silently downscaled by LaTeX and shrink every font below legibility.
    fig, axes = plt.subplots(
        1, len(panels), figsize=(7.6, 2.45), sharey=True,
        gridspec_kw=dict(width_ratios=widths, wspace=0.12),
    )
    axes = np.atleast_1d(axes)
    for ax, (title, defense, targets) in zip(axes, panels):
        x = np.arange(len(targets))
        width = 0.34 if len(targets) > 1 else 0.30
        for offset, attack in ((-0.5, "code"), (0.5, "surf")):
            heights = []
            for target in targets:
                key, base = (target, defense, attack), (target, "no_defense", attack)
                if key not in cells or base not in cells:
                    heights.append(float("nan"))
                    continue
                defended = union_asr_at_n(*cells[key], 100)
                undefended = union_asr_at_n(*cells[base], 100)
                heights.append(defended / undefended if undefended else float("nan"))
            bars = ax.bar(x + offset * width, heights, width,
                          color=ATTACK_COLOR[attack], label=ATTACK_LABEL[attack])
            for rect in bars:
                h = rect.get_height()
                if h != h:      # NaN -> no cell for this (target, defense, attack)
                    continue
                ax.text(rect.get_x() + rect.get_width() / 2, h + 0.025,
                        f"{h:.2f}", ha="center", fontsize=6.4, color="0.25")
        ax.set_xticks(x)
        ax.set_xticklabels([TARGET_SHORT[t] for t in targets], fontsize=8)
        ax.set_title(title, fontsize=8.5, pad=4)
        ax.axhline(1.0, color="0.45", lw=0.8, ls=":")
        ax.set_ylim(0, 1.20)
        ax.set_xlim(-0.62, len(targets) - 0.38)
        ax.tick_params(labelsize=8)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
    axes[0].set_ylabel("retained attack reach\n(defended $\\div$ undefended)", fontsize=8.5)
    axes[0].set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    # Shade EVERY gate facet (there are two now: WildGuard and LlamaGuard-3), since
    # the shading is what tells the reader which side of the transform/gate split
    # each panel belongs to — the paper's whole point in this figure.
    for ax, (_, defense, _) in zip(axes, panels):
        if defense in PROBE_DEFENSES:
            ax.set_facecolor("#f6f6f6")

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

    # Only plot targets we actually have cells for, so the 70B appears once its
    # round lands and the figure still builds from the published panel alone.
    shown = [t for t in TARGETS_WITH_70B
             if any((t, d, a) in cells for d in DEFENSES for a in ("code", "surf"))]
    fig, axes = plt.subplots(1, len(shown), figsize=(3.5 * len(shown), 3.2), sharey=True)
    for ax, target in zip(axes, shown):
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
    header = "{:<9}{:<22}{:<22}{:>9}{:>7}{:>7}{:>8}{:>7}"
    print(header.format("target", "defense", "attack", "per-draw",
                        "N=1", "N=10", "N=100", "QtFS"))
    print("-" * 91)
    for target in TARGETS_WITH_70B:
        for defense in DEFENSES + ["sage_t05"] + PROBE_DEFENSES:
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
    # Explicit, not a formula: the matrix is deliberately RAGGED (SemanticSmooth was
    # never run on the 70B; the temperature ablation is a single cell), so a product
    # formula would either over- or under-count. Breakdown:
    #   P2  18  3 targets x {no_defense, sage, semantic_smooth} x {code, surf}
    #   P2   4  llama x {canonicalize, canon.+WildGuard} x {code, surf}
    #   P3   2  llama x canon.+LlamaGuard-3 x {code, surf}      (2nd gate)
    #   P3   1  llama x SAGE(T=0.5) x code                      (temperature ablation)
    #   P3   4  llama70 x {no_defense, sage} x {code, surf}     (scale)
    EXPECTED_CELLS = 31
    if len(cells) != EXPECTED_CELLS:
        missing = sorted(set(cells))
        raise SystemExit(
            f"expected {EXPECTED_CELLS} cells across campaigns {sorted(CAMPAIGNS)}, "
            f"found {len(cells)} — sync outputs/ or check the campaign tags.\n"
            f"loaded: {missing}"
        )
    os.makedirs(args.outdir, exist_ok=True)
    for path in (fig_inversion(cells, args.outdir), fig_asr_vs_n(cells, args.outdir)):
        print("wrote", path)
    if args.table:
        print()
        print_table(cells)


if __name__ == "__main__":
    main()
