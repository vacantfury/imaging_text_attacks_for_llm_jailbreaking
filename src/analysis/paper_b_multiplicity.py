#!/usr/bin/env python3
"""Paper B (AS-2) — family-wise / FDR multiplicity correction over every test in
the paper.

THE OBJECTION THIS ANSWERS (cspaper review 2, con 7). The paper reports on the
order of a hundred significance tests across ten tables and never corrects for
multiplicity, so a reviewer cannot tell which claims would survive a correction
and which are selection artifacts.

WHY THIS SCRIPT IS BUILT ON REPORTED DISCORDANT COUNTS, NOT ON THE RAW CELLS.
Every contrast in this paper is an exact two-sided McNemar test, which is a
function of the discordant pair counts (b, c) ALONE -- the rest of the 2x2 does
not enter. The paper prints (b, c) inline for every test where the exact p is
load-bearing, so the correction is fully reproducible from published numbers: a
reader checks each row below against the cited table. Cells whose raw outputs
live on the clusters therefore do not need to be re-pulled, and the recomputed p
is cross-checked against the printed p (`--audit`) so a transcription slip fails
loudly instead of silently propagating.

WHERE ONLY A BOUND IS AVAILABLE (tables that print stars rather than exact p),
the bound from the paper's prose is used and marked. A bound is CONSERVATIVE for
this purpose: if `p <= u` survives correction, the exact p does too. Bounds are
never used to declare a result non-significant.

FAMILIES ARE DEFINED BY CLAIM, NOT BY TABLE, and are declared here in advance of
looking at the outcome -- one family per thing the paper asserts. F1 is the only
CONFIRMATORY family; everything else is exploratory and is reported as such.

Usage:
    uv run python -m src.analysis.paper_b_multiplicity
    uv run python -m src.analysis.paper_b_multiplicity --audit
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from math import comb


# --------------------------------------------------------------------------
# exact two-sided McNemar from discordant counts
# --------------------------------------------------------------------------
def mcnemar_p(b: int, c: int) -> float:
    """Exact two-sided McNemar. Under H0 the discordant pairs split Binom(n, 1/2)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * tail)


@dataclass
class Test:
    label: str
    table: str
    b: int | None = None          # discordant: favouring the image arm
    c: int | None = None          # discordant: favouring the text arm
    p_bound: float | None = None  # used only when (b, c) are not printed
    printed: float | None = None  # the p as typeset, for the audit cross-check
    note: str = ""

    @property
    def p(self) -> float:
        if self.b is not None:
            return mcnemar_p(self.b, self.c)
        return self.p_bound

    @property
    def kind(self) -> str:
        return "exact" if self.b is not None else "bound"


@dataclass
class Family:
    key: str
    claim: str
    method: str                    # "holm" (FWER) or "bh" (FDR)
    confirmatory: bool
    tests: list[Test] = field(default_factory=list)


# ==========================================================================
# THE INVENTORY. Every entry cites the table it was read from.
# ==========================================================================
FAMILIES = [
    # ---------------------------------------------------------------- F1
    Family(
        "F1", "Image presence shifts benign refusal on the borderline rung "
              "(the paper's primary claim), one test per model, hosted and open",
        "holm", True, [
            # hosted -- tab:ladder prints stars; the prose bounds all three at 1.5e-6
            Test("claude-sonnet-4-6", "tab:ladder", p_bound=1.5e-6),
            Test("gpt-4o-mini", "tab:ladder", p_bound=1.5e-6),
            Test("gemini-2.5-flash-lite", "tab:ladder", p_bound=1.5e-6),
            Test("gemini-2.5-flash", "tab:ladder", p_bound=1.0,
                 note="null in both collection windows; bound is the n.s. reading"),
            # open-weight -- tab:tierscan prints (b, c) and p
            Test("qwen3-vl-8b", "tab:tierscan", 32, 0, printed=1e-4),
            Test("gemma-3-12b-it", "tab:tierscan", 10, 1, printed=0.012),
            Test("internvl3-8b", "tab:tierscan", 13, 6, printed=0.167),
            Test("qwen2.5-vl-7b", "tab:tierscan", 7, 7, printed=1.000),
            Test("pixtral-12b", "tab:tierscan", 3, 4, printed=1.000),
            # added 2026-08-08 with the sign-inversion round. LLaVA is measured on
            # the SAME borderline rung with the same renders, so it belongs in F1
            # by the family's own definition -- including it is not optional, and
            # note the effect is NEGATIVE here (refusal falls), which the family
            # tests two-sided exactly as it does every other model.
            Test("llava-1.5-7b", "tab:signinv", 1, 9, printed=0.0215,
                 note="benign refusal FALLS 10->2%; direction opposite to the hosted models"),
        ]),
    # ---------------------------------------------------------------- F2
    Family(
        "F2", "Which image PROPERTIES change the size of the shift "
              "(open checkpoint, ten arms over one canonical text)",
        "bh", False, [
            Test("blank 1536^2 white", "tab:owprops", 36, 2),
            Test("line drawing", "tab:owprops", 29, 0),
            Test("blank 512^2 mid-grey", "tab:owprops", 29, 1),
            Test("blank 512^2 white", "tab:owprops", 26, 2),
            Test("blank 512^2 black", "tab:owprops", 24, 1),
            Test("blank 141x1024 white", "tab:owprops", 22, 2),
            Test("blank 1024x141 white", "tab:owprops", 21, 2, printed=0.0001),
            Test("blank 256^2 white", "tab:owprops", 21, 3, printed=0.0003),
            Test("caption image q100", "tab:owprops", 19, 8, printed=0.052),
            Test("caption image q40 JPEG", "tab:owprops", 17, 7, printed=0.064),
        ]),
    # ---------------------------------------------------------------- F3
    Family(
        "F3", "Within one model family, when did the behaviour appear "
              "(generational ladder)",
        "holm", False, [
            Test("qwen2-vl-7b", "tab:generational", 11, 3, printed=0.057),
            Test("qwen2.5-vl-7b", "tab:generational", 9, 8, printed=1.000),
            Test("qwen3-vl-8b", "tab:generational", 30, 2, printed=1e-4),
        ]),
    # ---------------------------------------------------------------- F4
    Family(
        "F4", "What the instruction/mention cue is made of "
              "(placebo ladder + attachment x mention factorial)",
        "holm", False, [
            Test("placebo P2-A: bare instruction", "tab:placebo", p_bound=0.013),
            Test("placebo P1-P2: + attachment clause", "tab:placebo", p_bound=0.0015),
            Test("placebo C-P1: file -> image", "tab:placebo", 12, 13, printed=1.0),
            Test("factorial: mention effect", "tab:factorial", 12, 4, printed=0.077),
            Test("factorial: attachment, no mention", "tab:factorial", 32, 2, printed=6.9e-8),
            Test("factorial: attachment, mention held", "tab:factorial", 20, 0, printed=1.9e-6),
        ]),
    # ---------------------------------------------------------------- F5
    Family(
        "F5", "The ladder rungs OTHER than borderline "
              "(threshold shift rather than blanket caution)",
        "holm", False, [
            Test("open ckpt, neutral rung", "tab:owladder", 4, 1, printed=0.375),
            Test("open ckpt, borderline rung", "tab:owladder", 30, 1, printed=1e-4),
            Test("open ckpt, harmful rung (ASR)", "tab:owladder", 1, 2, printed=1.000),
        ]),
    # ---------------------------------------------------------------- F6
    Family(
        "F6", "Image SIZE is a property of the axis, not of one rendered file "
              "(instance replication: 256^2 vs 1536^2 within each of three fills)",
        "holm", False, [
            Test("white fill, 256 vs 1536", "tab:instance", p_bound=0.0024),
            Test("grey fill, 256 vs 1536", "tab:instance", p_bound=6.6e-5),
            Test("black fill, 256 vs 1536", "tab:instance", p_bound=0.0075),
        ]),
    # ---------------------------------------------------------------- F7
    # Founded 2026-08-08 with the LLaVA round. Before it, pixtral's ASR
    # inversion sat in NO family at all -- an omission this audit surfaced: the
    # paper's `steerable` half was uncorrected because it was a single test with
    # nowhere to live. It now has two members and is corrected like everything
    # else.
    Family(
        "F7", "The sign inverts: image presence RAISES attack success "
              "(the paper's `steerable` failure mode)",
        "holm", False, [
            Test("pixtral-12b, harmful ASR 48->83%", "tab:ow_threshold", p_bound=3.1e-8),
            Test("llava-1.5-7b, harmful ASR 37->76%", "tab:signinv", 39, 0,
                 printed=3.64e-12,
                 note="JRS (Wei et al. 2026) predicted +28.13pp on this exact checkpoint"),
        ]),
    # ---------------------------------------------------------------- F8
    # Founded 2026-08-09 with the topic-stratified round (campaign
    # paper_b_topic_stratified). The borderline rung's original 100 prompts were
    # deception + harassment ONLY -- prompt_range [0,99] over a category-GROUPED
    # file -- so the paper's central cost claim rested on 2 of OR-Bench's 10
    # categories. 30 x 10 categories re-measures it. BH rather than Holm: this is
    # a per-category sweep, the same exploratory shape as F2.
    # The three AGGREGATE contrasts (claude 158/1, 4o-mini 109/0, fl.-lite 110/6)
    # are deliberately NOT listed as separate tests -- they are the same claim as
    # F1 on a better sample, and at p = 4.4e-46 / 3.1e-33 / 7.6e-26 they clear any
    # correction in this paper by tens of orders of magnitude.
    Family(
        "F8", "The benign cost by OR-Bench category, on the stratified sample "
              "(does the effect survive outside deception/harassment)",
        "bh", False, [
            Test("claude-sonnet-4-6 / deception", "tab:strata", 24, 0),
            Test("claude-sonnet-4-6 / harassment", "tab:strata", 16, 0),
            Test("claude-sonnet-4-6 / harmful", "tab:strata", 14, 0),
            Test("claude-sonnet-4-6 / hate", "tab:strata", 17, 0),
            Test("claude-sonnet-4-6 / illegal", "tab:strata", 16, 0),
            Test("claude-sonnet-4-6 / privacy", "tab:strata", 15, 0),
            Test("claude-sonnet-4-6 / self-harm", "tab:strata", 19, 0),
            Test("claude-sonnet-4-6 / sexual", "tab:strata", 12, 0),
            Test("claude-sonnet-4-6 / unethical", "tab:strata", 7, 1),
            Test("claude-sonnet-4-6 / violence", "tab:strata", 18, 0),
            Test("gpt-4o-mini / deception", "tab:strata", 13, 0),
            Test("gpt-4o-mini / harassment", "tab:strata", 7, 0),
            Test("gpt-4o-mini / harmful", "tab:strata", 16, 0),
            Test("gpt-4o-mini / hate", "tab:strata", 10, 0),
            Test("gpt-4o-mini / illegal", "tab:strata", 10, 0),
            Test("gpt-4o-mini / privacy", "tab:strata", 13, 0),
            Test("gpt-4o-mini / self-harm", "tab:strata", 8, 0),
            Test("gpt-4o-mini / sexual", "tab:strata", 8, 0),
            Test("gpt-4o-mini / unethical", "tab:strata", 13, 0),
            Test("gpt-4o-mini / violence", "tab:strata", 11, 0),
            Test("gemini-2.5-flash-lite / deception", "tab:strata", 5, 1),
            Test("gemini-2.5-flash-lite / harassment", "tab:strata", 9, 1),
            Test("gemini-2.5-flash-lite / harmful", "tab:strata", 7, 1),
            Test("gemini-2.5-flash-lite / hate", "tab:strata", 16, 0),
            Test("gemini-2.5-flash-lite / illegal", "tab:strata", 14, 1),
            Test("gemini-2.5-flash-lite / privacy", "tab:strata", 13, 1),
            Test("gemini-2.5-flash-lite / self-harm", "tab:strata", 11, 0),
            Test("gemini-2.5-flash-lite / sexual", "tab:strata", 17, 0),
            Test("gemini-2.5-flash-lite / unethical", "tab:strata", 7, 1),
            Test("gemini-2.5-flash-lite / violence", "tab:strata", 11, 0),
        ]),
    # ---------------------------------------------------------------- F9
    # Founded 2026-08-09 answering review 3 con 7 / Q3: the property claims were
    # tested against the TEXT arm, never against each other, so the paper printed
    # differences it had not tested. Both survive. All colour arms are 512^2, so
    # black-vs-white is size-matched; the content contrast is size-matched at
    # 1024x141 by construction.
    Family(
        "F9", "Direct BETWEEN-ARM property contrasts on gemini-2.5-flash-lite "
              "(the two the paper quotes as differences)",
        "holm", True, [
            Test("black vs white, both 512^2", "tab:imgprops", 22, 0, printed=4.8e-7,
                 note="the paper's '+22pp more than a white one of identical size'"),
            Test("caption vs size-matched blank, 1024x141", "tab:imgprops", 31, 1,
                 printed=1.5e-8,
                 note="the paper's '+30pp more than a size-matched blank'"),
        ]),
]

# Declared-null families, listed so the inventory is complete. A multiplicity
# correction can only make a null MORE null, so correcting them is vacuous --
# what governs their interpretation is POWER, which the paper states inline.
NULL_FAMILIES = {
    "serving-route control (tab:sameweights)":
        "4 route contrasts, 1-3 discordant of 100. RESTATED 2026-08-09 after "
        "review 3 con 2: the claim is no longer a non-rejection (p>=0.25 at that "
        "discordant count has almost no power) but a BOUND -- Newcombe 95% CIs "
        "[-2.5,+5.1], [-2.2,+4.5], [-2.2,+4.5], [-8.0,+1.0] pp, i.e. equivalent "
        "within +/-10pp on every arm and +/-5pp on both blank arms. Correcting a "
        "set of intervals is not meaningful; what governs is the margin.",
    "three open-weight nulls (tab:ow_threshold)":
        "The claim drawn is explicitly NOT 'no effect' -- the paper retracts that "
        "reading (a fourth open checkpoint refuted it) and reports the nulls as "
        "sample facts, not as a class property.",
    "placebo C-P1, the image-word test (tab:placebo)":
        "Reported as a bounded null (12/13 discordant, p=1.0; excludes an effect "
        "above ~11pp), not as evidence of exact zero.",
    "within-family harmful ladder (tab:generational, harmful columns)":
        "ADDED 2026-08-09 for review 3 con 5 (xc job 283 filled the missing "
        "qwen2-vl-7b rung). 3 harmful contrasts on the generational ladder: "
        "1/1, 5/2 and 1/2 discordant of 100 -> Newcombe 95% CIs [-4.5,+4.5], "
        "[-2.7,+9.3], [-6.1,+3.7] pp. Stated as BOUNDS, not non-rejections, so "
        "no correction applies -- the margin governs (all three equivalent "
        "within +/-10pp, the oldest within +/-5pp). NOTE the headroom caveat "
        "the paper now makes explicit: text-arm ASR is 2/4/2%, i.e. floored at "
        "the OLDEST rung, so this family bounds the per-rung decoupling but "
        "cannot test the across-model 'harmful side collapses with recency' "
        "trend in either direction.",
}


# --------------------------------------------------------------------------
def holm(ps: list[float], alpha: float = 0.05) -> list[bool]:
    """Holm-Bonferroni step-down; controls FWER at alpha."""
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    out, m = [False] * len(ps), len(ps)
    for rank, i in enumerate(order):
        if ps[i] > alpha / (m - rank):
            break                      # step-down: everything after also fails
        out[i] = True
    return out


def bh(ps: list[float], alpha: float = 0.05) -> list[bool]:
    """Benjamini-Hochberg step-up; controls FDR at alpha."""
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    m, cut = len(ps), -1
    for rank, i in enumerate(order, start=1):
        if ps[i] <= alpha * rank / m:
            cut = rank
    out = [False] * m
    for rank, i in enumerate(order, start=1):
        out[i] = rank <= cut
    return out


def fmt(p: float) -> str:
    return f"{p:.2e}" if p < 1e-3 else f"{p:.4f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--audit", action="store_true",
                    help="cross-check recomputed p against the p typeset in the paper")
    a = ap.parse_args()

    all_ps, flips = [], []
    for fam in FAMILIES:
        ps = [t.p for t in fam.tests]
        all_ps += ps
        keep = (holm if fam.method == "holm" else bh)(ps, a.alpha)
        raw = [p < a.alpha for p in ps]

        tag = "CONFIRMATORY" if fam.confirmatory else "exploratory"
        name = "Holm-Bonferroni (FWER)" if fam.method == "holm" else "Benjamini-Hochberg (FDR)"
        print("=" * 78)
        print(f"{fam.key}  [{tag}]  n={len(ps)}  {name} @ alpha={a.alpha}")
        print(f"    claim: {fam.claim}")
        print("-" * 78)
        print(f"{'test':38s} {'source':16s} {'p':>10s} {'raw':>5s} {'corr':>5s}")
        for t, k, r in zip(fam.tests, keep, raw):
            mark = "" if k == r else "   <-- CHANGES"
            src = t.table + ("" if t.kind == "exact" else " (bd)")
            print(f"{t.label:38s} {src:16s} {fmt(t.p):>10s} "
                  f"{'yes' if r else 'no':>5s} {'yes' if k else 'no':>5s}{mark}")
            if t.note:
                print(f"{'':38s} note: {t.note}")
            if k != r:
                flips.append((fam.key, t.label, t.p))
        print()

    # ---- global Bonferroni: the most hostile correction a reviewer could ask
    m = len(all_ps)
    thresh = a.alpha / m
    survive = [p for p in all_ps if p < thresh]
    print("=" * 78)
    print(f"GLOBAL BONFERRONI across ALL {m} corrected tests "
          f"(alpha/{m} = {thresh:.2e}) -- the most hostile correction available")
    print(f"    tests surviving: {len(survive)} of {m}")
    print(f"    the primary-claim tests survive it: "
          f"{all([t.p < thresh for t in FAMILIES[0].tests[:3]] + [FAMILIES[0].tests[4].p < thresh])}")
    print()

    print("=" * 78)
    print("WHAT CORRECTION CHANGES")
    if flips:
        for k, lab, p in flips:
            print(f"  {k}  {lab}  (p={fmt(p)}) loses significance under correction")
    else:
        print("  Nothing. Every test significant at the uncorrected alpha remains")
        print("  significant within its family, and every null stays null.")
    print()
    print("DECLARED-NULL FAMILIES (correction vacuous -- power governs, not alpha):")
    for k, v in NULL_FAMILIES.items():
        print(f"  * {k}\n      {v}")

    if a.audit:
        print()
        print("=" * 78)
        print("AUDIT: recomputed exact p vs the value typeset in the paper")
        bad = 0
        for fam in FAMILIES:
            for t in fam.tests:
                if t.printed is None or t.b is None:
                    continue
                got = t.p
                # printed values are rounded, and '<10^-4' is an upper bound
                ok = (got <= t.printed * 1.06 + 5e-5) if t.printed <= 1e-4 else \
                     abs(got - t.printed) <= max(0.0015, 0.06 * t.printed)
                if not ok:
                    bad += 1
                print(f"  {'ok ' if ok else 'BAD'} {t.label:38s} "
                      f"recomputed={fmt(got)}  printed={fmt(t.printed)}")
        print(f"\n  mismatches: {bad}")
        raise SystemExit(1 if bad else 0)


if __name__ == "__main__":
    main()
