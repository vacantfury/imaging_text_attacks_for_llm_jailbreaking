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

import os
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
SEQ_ORDER = ["llama", "qwen", "gemma", "llama70"]

# Table 2's T=1.0 column, per target: (undefended, SAGE, guard baseline) coverage.
# Added 2026-08-22 after a cross-family read flagged the borrowed-strength paragraph
# for mixing this panel's numbers with the main matrix's, which reads as the paper
# contradicting itself on the SAME cell (the 70B at 22 vs 25 is the pre/post-fix
# encoder correction; the two are different rounds and must not be sequenced together).
PANEL_T1 = {
    "llama":   dict(undefended=96, sage=59, guard=9),
    "qwen":    dict(undefended=98, sage=17, guard=9),
    "gemma":   dict(undefended=97, sage=12, guard=10),
    "llama70": dict(undefended=95, sage=25, guard=None),
}
# Per-draw rates behind the accuracy-does-not-predict claim, Gemma, one round.
#
# ⚠️ These are per-draw NON-SUCCESS rates (100 - per-draw ASR), NOT block rates.
# The main paper calls them "blocks", which is loose: only a GATE terminates a
# draw with its own canned string, and SAGE (a transform defense) has none, so
# its block rate in the gate's sense is 0.00% and every refusal in its cell is
# the target's own. Recomputed 2026-08-22 from the two pinned cells:
#   SAGE  cell: ASR 0.23%, non-success 99.77%, canned-block 0.00%, 12 behaviors
#   gate  cell: ASR 4.44%, non-success 95.56%, canned-block 92.54%, 10 behaviors
# The supplement's `tab:blockrate` prints the decomposition; see its section
# "Per-draw stopping rates, and what they do and do not count."
GEMMA_BLOCK = {"sage": 99.8, "guard": 95.6}

#: Cells the two rates above are read from, and the gate's exact canned string.
#: Kept next to the constants so the recomputation below can never drift from
#: what the constants claim.
GEMMA_BLOCK_CELLS = {
    "sage": "outputs/bestofn_attack/rejudge/harmbench/"
            "gemma2_9b_it_sage_gpt-5-mini_20260808_202050_47660385",
    "guard": "outputs/bestofn_attack/rejudge/harmbench/"
             "gemma2_9b_it_guard_baseline_gpt-5-mini_20260808_201905_22267190",
}
CANNED_GUARD_REFUSAL = (
    "I cannot assist with this request because the guard model flagged it as unsafe."
)


def recompute_gemma_rates(root: str = ".") -> dict | None:
    """Non-success and canned-block rates from the stored draws.

    Returns None when the run outputs are not on this machine, so a host without
    them reports `not-run` rather than passing silently. This is the artifact-backed
    half of the claim-integrity battery; the probe list below is the
    clone-checkable half and needs no outputs.
    """
    import json

    out = {}
    for arm, rel in GEMMA_BLOCK_CELLS.items():
        path = os.path.join(root, rel, "raw_results.jsonl")
        if not os.path.exists(path):
            return None
        rows = [json.loads(line) for line in open(path)]
        if not rows:
            return None
        n = len(rows)
        succ = sum(1 for r in rows if str(r.get("asr")).lower() == "true")
        canned = sum(
            1 for r in rows if (r.get("response") or "").strip() == CANNED_GUARD_REFUSAL
        )
        behaviors: dict[str, bool] = {}
        for r in rows:
            b = str(r.get("id", "")).split("__bon")[0]
            behaviors[b] = behaviors.get(b, False) or str(r.get("asr")).lower() == "true"
        out[arm] = {
            "draws": n,
            "asr": 100 * succ / n,
            "non_success": 100 - 100 * succ / n,
            "canned_block": 100 * canned / n,
            "behaviors": sum(behaviors.values()),
        }
    return out

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

    # the borrowed-strength sequences must be ONE panel, not a mix of rounds
    # NOTE the paper uses TWO target orders by convention: the temperature NETS are
    # quoted llama/gemma/qwen/llama70 (ORDER), while target SEQUENCES run
    # llama/qwen/gemma/llama70 (SEQ_ORDER). Mixing them silently transposes numbers.
    seq_def = [PANEL_T1[t]["sage"] for t in SEQ_ORDER if PANEL_T1[t]["sage"] is not None]
    seq_und = [PANEL_T1[t]["undefended"] for t in SEQ_ORDER]
    out.append(("Table 2 defended sequence (llama/gemma/qwen/llama70)",
                "/".join(str(v) for v in seq_def), "59/17/12/25 in llama/qwen/gemma/llama70 order"))
    out.append(("Table 2 undefended sequence",
                "/".join(str(v) for v in seq_und), "96/98/97/95 in llama/qwen/gemma/llama70 order"))
    out.append(("defended spread within Table 2",
                f"{max(seq_def)/min(seq_def):.1f}x", "almost 5x"))

    # accuracy does not predict robustness: same target, same round
    out.append(("Gemma: SAGE blocks vs loses",
                f"blocks {GEMMA_BLOCK['sage']}%, loses {PANEL_T1['gemma']['sage']}",
                "blocks 99.8%, loses 12"))
    out.append(("Gemma: gate blocks vs loses",
                f"blocks {GEMMA_BLOCK['guard']}%, loses {PANEL_T1['gemma']['guard']}",
                "blocks 95.6%, loses 10"))
    out.append(("the comparison holds (higher block rate, worse coverage)",
                str(PANEL_T1["gemma"]["sage"] > PANEL_T1["gemma"]["guard"]
                    and GEMMA_BLOCK["sage"] > GEMMA_BLOCK["guard"]), "True"))

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

    # Artifact-backed half: the two Gemma rates are recomputed from stored draws
    # rather than trusted as constants. A host without the outputs says so.
    live = recompute_gemma_rates()
    print()
    if live is None:
        print("gemma per-draw rates: not-run (outputs not on this host)")
    else:
        print(f"{'gemma per-draw (from stored draws)':44s}  "
              f"{'ASR':>7s} {'non-succ':>9s} {'canned':>8s} {'behav':>6s}")
        for arm, v in live.items():
            print(f"{arm:44s}  {v['asr']:7.2f} {v['non_success']:9.2f} "
                  f"{v['canned_block']:8.2f} {v['behaviors']:6d}")
        for arm in ("sage", "guard"):
            want = GEMMA_BLOCK[arm]
            got = round(live[arm]["non_success"], 1)
            if abs(got - want) > 0.05:
                print(f"MISMATCH: {arm} non-success {got} != declared {want}")
                return 1
        if live["sage"]["canned_block"] != 0.0:
            print("MISMATCH: SAGE reported a canned block; it has no block string")
            return 1

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
        "one-panel defended sequence": r"($59$/$17$/$12$/$25$)",
        "one-panel undefended sequence": r"($96$/$98$/$97$/$95$)",
        "gemma blocks-vs-loses": r"blocks $99.8\%$",
        "gemma gate counterpart": r"blocking $95.6\%$ loses $10$",
    }
    # The supplement carries the decomposition the main paper's loose wording
    # needs; probe it only when a supplement is among the inputs.
    if "supplementary" in os.path.basename(tex_path):
        probes = {
            "blockrate non-success sage": r"$\mathbf{99.77}$",
            "blockrate non-success gate": r"$\mathbf{95.56}$",
            "blockrate canned sage":      r"$0.00$",
            "blockrate canned gate":      r"$92.54$",
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
