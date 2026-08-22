"""Rate-vs-delta unit guard across the AS-7 main paper and Supplementary Document.

The AAAI-27 AIA submission is TWO documents, because the venue gives a technical
appendix no legal in-PDF home. That split created a failure surface: the main
paper summarizes a supplementary table, and nothing disagrees when the summary is
wrong.

It happened. On 2026-08-21 one Introduction sentence carried four errors against
its own evidence, of which THIS is the mechanically catchable one:

    main paper:    "against $20$--$79$ points for unconditional attachment"
    supplementary: "raises benign refusal to $20$--$79\\%$, an inflation of
                    $+9$ to $+67$ points over the text baseline"

20-79 is a benign refusal RATE. The main paper printed it as an inflation in
POINTS. The true inflation is +9 to +67. A rate rendered as a delta is the
absolute-vs-relative confusion the house handbook rates error-tier.

WHAT THIS GUARD DELIBERATELY DOES NOT CLAIM TO CATCH. The other three errors in
that same sentence were a wrong comparator ("undefended" for "text" baseline), a
rounded-away figure (0 vs 0-1 point), and a range taken from the wrong row (9-16
for 12-16, apparently bleeding from a neighbouring "+9 to +67"). In every one of
those the numbers were PRESENT in the source; only their meaning was wrong. That
is not mechanically checkable at any reasonable cost, and a guard implying
otherwise would be the "reads green over ground it never covered" defect this
repo has already hit three times (TODO 40). Those are caught by reading the
source table against the claim, which is a duty, not a script.

So the invariant here is exactly one thing, and it is precise: if a numeric range
appears in one document carrying a POINTS unit and in the other carrying a
PERCENT unit, one of them is wrong.

Usage (exit 1 on any unexplained mismatch):
    python -m src.analysis.as7_xdoc_numbers verify
    python -m src.analysis.as7_xdoc_numbers verify --negative-control
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

LATEX_DIR = Path("paper/my_papers/as-7/aaai_2027_ai_alignment/aaai_aia_latex")
MAIN = LATEX_DIR / "paper.tex"
SUPP = LATEX_DIR / "supplementary.tex"

# Ranges that legitimately carry both units (a rate range and a delta range that
# happen to coincide). Each entry needs a reason; an empty dict is the norm.
ALLOWED: dict[str, str] = {
    # Triaged 2026-08-21. Two unrelated quantities that coincidentally share two
    # digits, both correct as written:
    #   * "still moves ASR by $2$--$3$ points (n.s.)"  -- a DELTA (the
    #     majority-vote smoother's grant inflation, the paper's null rung);
    #   * "drives attack success down to $2$--$3\%$"   -- a LEVEL.
    # Different quantities, so both units are right and no edit is warranted.
    "$2$--$3$": "delta (smoother grant inflation) vs level (attack success on code_attack); unrelated quantities",
}

# "$20$--$79$ points" / "$20$--$79$ percentage points"
AS_POINTS = re.compile(r"\$(\d+(?:\.\d+)?)\$--\$(\d+(?:\.\d+)?)\$\s*(?:percentage\s+)?points?\b")
# "$20$--$79\%$" or "$20$--$79$\%"
AS_PERCENT = re.compile(r"\$(\d+(?:\.\d+)?)\$--\$(\d+(?:\.\d+)?)(?:\\%)?\$\s*\\?%?")


def _strip_comments(text: str) -> str:
    out = []
    for line in text.split("\n"):
        i = 0
        while True:
            i = line.find("%", i)
            if i == -1:
                break
            if i == 0 or line[i - 1] != "\\":
                line = line[:i]
                break
            i += 1
        out.append(line)
    return "\n".join(out)


def _as_points(text: str) -> set[tuple[str, str]]:
    return set(AS_POINTS.findall(text))


def _as_percent(text: str) -> set[tuple[str, str]]:
    """Ranges written with a percent sign, e.g. $20$--$79\\%$."""
    found = set()
    for m in re.finditer(r"\$(\d+(?:\.\d+)?)\$--\$(\d+(?:\.\d+)?)\\%\$", text):
        found.add((m.group(1), m.group(2)))
    for m in re.finditer(r"\$(\d+(?:\.\d+)?)\$--\$(\d+(?:\.\d+)?)\$\\?%", text):
        found.add((m.group(1), m.group(2)))
    return found


def verify(negative_control: bool = False) -> int:
    main = _strip_comments(MAIN.read_text(encoding="utf-8"))
    supp = _strip_comments(SUPP.read_text(encoding="utf-8"))

    if negative_control:
        # Re-inject the real 2026-08-21 defect verbatim.
        main = main.replace(
            "against $+9$ to $+67$ points for unconditional attachment",
            "against $20$--$79$ points for unconditional attachment", 1)

    main_pts, supp_pts = _as_points(main), _as_points(supp)
    main_pct, supp_pct = _as_percent(main), _as_percent(supp)

    all_pts = main_pts | supp_pts
    all_pct = main_pct | supp_pct
    clashes = sorted(all_pts & all_pct)

    print(f"ranges written as points  : {len(all_pts)}")
    print(f"ranges written as percent : {len(all_pct)}")

    real = [c for c in clashes if f"${c[0]}$--${c[1]}$" not in ALLOWED]
    if not real:
        print("xdoc units OK -- no range is a rate in one document and a delta "
              "in the other")
        return 0

    print(f"\n!! {len(real)} range(s) carry BOTH a percent and a points unit "
          f"across the two documents. One reading is wrong:\n")
    for lo, hi in real:
        tok = f"${lo}$--${hi}$"
        where_pts = "main" if (lo, hi) in main_pts else "supplementary"
        where_pct = "main" if (lo, hi) in main_pct else "supplementary"
        print(f"  {tok}: printed as POINTS in {where_pts}, as PERCENT in {where_pct}")
        for doc, txt in (("main", main), ("supp", supp)):
            for m in re.finditer(re.escape(tok), txt):
                s = max(0, m.start() - 110)
                print(f"     [{doc}] ...{re.sub(r'[ ]+', ' ', txt[s:m.end() + 60])}...")
        print()
    return 1


def main_cli() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("verify", help="check rate-vs-delta units across the two documents")
    v.add_argument("--negative-control", action="store_true",
                   help="re-inject the real 2026-08-21 defect; the guard MUST fail")
    args = ap.parse_args()
    rc = verify(negative_control=args.negative_control)
    if args.negative_control:
        if rc == 0:
            print("\n!! NEGATIVE CONTROL FAILED: the guard did not catch the "
                  "known defect. Do not trust a green run from it.")
            return 1
        print("\nnegative control OK -- the guard catches the known defect")
        return 0
    return rc


if __name__ == "__main__":
    sys.exit(main_cli())
