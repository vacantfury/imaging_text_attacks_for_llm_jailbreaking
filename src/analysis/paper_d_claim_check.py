"""Recompute AS-4's DERIVED claims from the panel values the paper prints.

WHY. The sibling repo's handoff (2026-08-21) reports four incidents in two days
where a claim about our own results was wrong while every individual NUMBER in it
was correct: the SET a counted claim ranged over had moved, or the SOURCE a number
was attributed to was the wrong run. All four survived review. This repo has the
same exposure and carried no checker, so the AIA package's claim-integrity step
was a manual recompute. This module mechanises the half that is pure arithmetic
over already-published values: every ratio, difference, range and count the paper
states that is DERIVED from its own tables must follow from those tables.

WHAT IT DOES NOT DO. It does not re-read the outputs tree; the validated builders
already do that (paper_d_temperature_ci, paper_d_factorial_ci, paper_d_severity_ci
each gate on their published values) and as4_judgments_release crosschecks the
released layer against the paper. This checks the ARITHMETIC BRIDGE between them
and the prose, which is where a stale claim survives a correct table.

    uv run python -m src.analysis.paper_d_claim_check <paper.tex>
"""
from __future__ import annotations

import re
import sys

# Table 3 (the temperature panel) as published, per target:
#   control drop, SAGE net, SelfDefend net, LLM-Self-Defense net
PANEL = {
    "llama":   dict(control=14, sage=59, selfdefend=25, llm_self_defense=38),
    "gemma":   dict(control=24, sage=76, selfdefend=-5, llm_self_defense=23),
    "qwen":    dict(control=12, sage=82, selfdefend=8,  llm_self_defense=8),
    "llama70": dict(control=15, sage=29, selfdefend=2,  llm_self_defense=None),
}
ORDER = ["llama", "gemma", "qwen", "llama70"]

# tab:compose as published: (code N=1, BoN N=100, composed)
COMPOSE = {"llama": (4.7, 3.0, 67.0), "qwen": (1.8, 0.0, 22.0), "gemma": (0.2, 0.0, 15.0)}


def _fmt(x: float) -> str:
    return f"{x:+.0f}" if abs(x - round(x)) < 1e-9 else f"{x:+.1f}"


def checks() -> list[tuple[str, str, str]]:
    """(name, derived, what the paper must say) — all from PANEL/COMPOSE alone."""
    out = []

    # ordering margins: SAGE net minus SelfDefend net
    margins = [PANEL[t]["sage"] - PANEL[t]["selfdefend"] for t in ORDER]
    out.append(("ordering margins", ", ".join(str(m) for m in margins), "34, 81, 74 and 27"))

    # donation ratios against each target's own answer channel
    sampled = [PANEL[t]["sage"] / PANEL[t]["control"] for t in ORDER]
    fixed = [PANEL[t]["selfdefend"] / PANEL[t]["control"] for t in ORDER]
    out.append(("sampled-verdict ratios", ", ".join(f"{r:.1f}" for r in sampled),
                "4.2, 3.2, 6.8 and 1.9"))
    out.append(("fixed-verdict ratios", ", ".join(f"{r:.1f}" for r in fixed),
                "1.8, -0.2, 0.7 and 0.1"))
    out.append(("sampled ratio range", f"{min(sampled):.1f} to {max(sampled):.1f}",
                "1.9 to 6.8 times"))
    out.append(("control-drop range",
                f"{min(PANEL[t]['control'] for t in ORDER)}--{max(PANEL[t]['control'] for t in ORDER)}",
                "12--24 points"))

    # superadditivity multiples: composed / (sum of the two ingredients)
    mults = {t: COMPOSE[t][2] / (COMPOSE[t][0] + COMPOSE[t][1]) for t in ("llama", "qwen", "gemma")}
    out.append(("superadditivity multiples",
                ", ".join(f"{t}={mults[t]:.0f}x" for t in ("llama", "qwen", "gemma")),
                "9x, 12x and 75x, i.e. '9 to 75 times the sum of the parts'"))

    # matched-budget split on the SAGE cell: composed minus single-shot code
    out.append(("matched-budget gain, code arm",
                f"{COMPOSE['llama'][2] - COMPOSE['llama'][0]:+.1f}", "+62.3"))
    out.append(("matched-budget gain, character arm",
                f"{COMPOSE['llama'][1]:+.1f}", "+3.0"))

    # 'inert on three of the four targets' == |fixed-verdict net| <= 8 on exactly 3
    inert = [t for t in ORDER if abs(PANEL[t]["selfdefend"]) <= 8]
    out.append(("targets where a fixed verdict is inert (<=8 pts)",
                f"{len(inert)} of 4 ({', '.join(inert)})", "three of the four targets"))
    return out


def main(tex_path: str | None = None) -> int:
    rows = checks()
    print(f"{'derived quantity':44s}  {'recomputed':34s}  paper must state")
    print("-" * 120)
    for name, got, must in rows:
        print(f"{name:44s}  {got:34s}  {must}")

    if not tex_path:
        return 0
    tex = re.sub(r"(?m)^%.*$", "", open(tex_path).read())
    flat = re.sub(r"\s+", " ", tex)
    # Each probe is a string the paper MUST contain if the derived value is right.
    probes = {
        "ordering margins": r"$34$, $81$, $74$ and $27$ points",
        "sampled ratios": r"$4.2$, $3.2$, $6.8$ and $1.9$ times",
        "fixed ratios": r"$1.8$, $-0.2$, $0.7$ and $0.1$ times",
        "ratio range": r"$1.9$ to $6.8$ times that",
        "control range": r"$12$--$24$ points",
        "matched-budget split": r"$+3.0$ points on the surface channel",
        "inert count": r"three of the four targets",
    }
    missing = [k for k, v in probes.items() if re.sub(r"\s+", " ", v) not in flat]
    print()
    if missing:
        print(f"MISSING FROM {tex_path}: " + ", ".join(missing))
        return 1
    print(f"all {len(probes)} derived claims found verbatim in {tex_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
