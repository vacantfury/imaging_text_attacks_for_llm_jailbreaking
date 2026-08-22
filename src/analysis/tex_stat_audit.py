"""Audit a paper's LaTeX source for internal statistical consistency.

Every paired-binary result in these papers is reported as some subset of
(rate_before, rate_after, delta, discordant b/c, p). Those five quantities are
massively over-determined: for n paired prompts,

    delta == rate_after - rate_before == (b - c) / n        and
    p     == exact two-sided McNemar(b, c)   [a function of b and c ALONE]

so any transcription slip, stale number, or copy-paste between rows breaks an
identity. This module recomputes all of them from the .tex and reports every
row that fails.

WHY THIS EXISTS. cspaper review 4 of AS-2 opened with the claim that the
attachment x mention table was internally inconsistent -- that its discordant
counts could not produce its stated deltas or p-values -- and rated the paper
down on it. The table was in fact exact to the digit; the reviewer, reading a
two-column PDF linearly, had joined a count from the neighbouring table's row.
But "we checked and it's fine" is worth nothing asserted; it is worth something
mechanised. Running this over the source turns a reviewer's arithmetic
challenge into a check anyone can re-run, and catches the real version of that
defect on the day it is introduced rather than in a review.

Deliberately NOT a claim about correctness of the underlying data: it proves the
numbers printed in the paper are mutually consistent and that the p-values match
their counts. A cell measured from the wrong output dir is consistent nonsense,
and only provenance checks catch that.

    python -m src.analysis.tex_stat_audit paper/my_papers/as-2/.../paper.tex
    python -m src.analysis.tex_stat_audit <tex> --n 100 --verbose
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from math import comb

# Rows whose "a/b" token is not a discordant-count pair (dates, ratios, ranges).
_NOT_COUNTS = re.compile(r"\b(?:19|20)\d\d\b|\d{2}/\d{2}\b")
# "8/10 cells show ..." -- a tally of units, not a pair of discordant counts.
_TALLY = re.compile(r"\s+(?:cells?|models?|arms?|rows?|runs?|jobs?|conditions?"
                    r"|contrasts?|checkpoints?|pairs? of)\b")


def mcnemar_exact(b: int, c: int) -> float:
    """Exact two-sided McNemar: binomial sign test on the discordant pairs."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2**n)


_FONT_MACROS = ("mathbf", "textbf", "emph", "texttt", "text", "bm")


def _unwrap(s: str) -> str:
    """Drop font macros, keeping their argument -- brace-aware, so that
    \\mathbf{<10^{-4}} unwraps to <10^{-4} rather than being left intact.
    A naive [^{}]* regex silently skips exactly the nested cases, which is how
    a p-value column goes unchecked while the audit still reports success."""
    for macro in _FONT_MACROS:
        needle = "\\" + macro + "{"
        while (i := s.find(needle)) != -1:
            j, depth = i + len(needle), 1
            while j < len(s) and depth:
                depth += (s[j] == "{") - (s[j] == "}")
                j += 1
            if depth:  # unbalanced -- leave alone rather than corrupt
                break
            s = s[:i] + s[i + len(needle):j - 1] + s[j:]
    return s


def _clean(s: str) -> str:
    """Strip the LaTeX that sits between a reader and a digit."""
    s = re.sub(r"(?<!\\)%.*$", "", s)
    s = s.replace(r"\phantom{0}", "").replace(r"\ ", " ")
    s = _unwrap(s)
    s = s.replace(r"\,", "").replace(r"\!", "").replace(r"\;", "")
    s = s.replace(r"{\times}", "x").replace(r"\times", "x")
    s = s.replace("$", "").replace(r"\%", "%")
    return s


def _num(cell: str) -> float | None:
    m = re.fullmatch(r"\s*([+-]?\d+(?:\.\d+)?)\s*%?\s*", cell)
    return float(m.group(1)) if m else None


def _pval(cell: str) -> tuple[str, float | None, bool] | None:
    """Return (raw, value, is_upper_bound) for a p-value cell, else None."""
    t = cell.strip().lstrip("p=").strip()
    m = re.fullmatch(r"<\s*10\^\{?-(\d+)\}?", t)
    if m:
        return t, 10 ** -int(m.group(1)), True
    m = re.fullmatch(r"([\d.]+)\s*x\s*10\^\{?(-\d+)\}?", t)
    if m:
        return t, float(m.group(1)) * 10 ** int(m.group(2)), False
    m = re.fullmatch(r"(\d+(?:\.\d+)?)", t)
    if m and float(m.group(1)) <= 1.0:
        return t, float(m.group(1)), False
    if t in {"n.s.", "---", ""}:
        return t, None, False
    return None


@dataclass
class Finding:
    line: int
    kind: str
    detail: str
    context: str


@dataclass
class Row:
    line: int
    b: int
    c: int
    delta: float | None = None
    before: float | None = None
    after: float | None = None
    p_raw: str | None = None
    p_val: float | None = None
    p_bound: bool = False
    n: int | None = None          # per-row denominator; None -> the global default
    context: str = ""
    findings: list[Finding] = field(default_factory=list)


def _audit_n_marks(text: str) -> list[tuple[int, int]]:
    """Line numbers where a `% AUDIT-N: <int>` marker changes the denominator."""
    out = []
    for i, raw in enumerate(text.split("\n"), start=1):
        # Allow a trailing "% why" note after the number: a marker that
        # cannot carry its own justification will be written without one,
        # and an unexplained denominator override is the thing most likely
        # to be wrong later.
        m = re.match(r"\s*%\s*AUDIT-N:\s*(\d+)\s*(?:%.*)?$", raw)
        if m:
            out.append((i, int(m.group(1))))
    return out


def _n_at(marks: list[tuple[int, int]], line_no: int) -> int | None:
    cur = None
    for ln, val in marks:
        if ln <= line_no:
            cur = val
    return cur


def _rows_from_tex(text: str, default_n: int) -> list[Row]:
    """Extract every row/phrase carrying a discordant b/c pair."""
    rows: list[Row] = []
    # Segment the document the way a RESULT is bounded, not the way the file
    # happens to wrap: tabular rows end at \\, prose runs to the paragraph
    # break. Splitting per source line strands a result from the p-value that
    # wrapped onto the next line, and the audit then silently skips it.
    # ⚠️ MIXED-n PAPERS. This audit was written when every paired table in the
    # paper shared one denominator, and a single global -n was therefore safe.
    # It stopped being safe the moment a table ran on a different sample (the
    # 240-prompt held-out realistic-image round, 2026-08-22): every row in it
    # was flagged INCONSISTENT against n=100, which is a FALSE POSITIVE, and the
    # symmetric danger is worse -- a wrong global n can make a genuinely broken
    # row look fine. A table may therefore declare its own denominator with a
    # line `% AUDIT-N: <int>` anywhere before its rows; it applies until the
    # next such marker. Absent any marker the global default is used exactly as
    # before, so existing invocations are unaffected.
    n_marks = _audit_n_marks(text)

    doc = "\n".join(_clean(raw) for raw in text.split("\n"))
    line_at = [1]
    for ch in doc:
        line_at.append(line_at[-1] + (ch == "\n"))

    bounds = [0] + [m.end() for m in re.finditer(r"\\\\|\n[ \t]*\n", doc)] + [len(doc)]
    chunks: list[tuple[int, str]] = []
    for start, end in zip(bounds, bounds[1:]):
        # Drop the trailing row terminator: left on, it fuses to the last cell
        # and that cell's p-value stops parsing -- a silent loss of coverage.
        seg = re.sub(r"\\\\\s*$", "", doc[start:end])
        if seg.strip():
            chunks.append((start, seg))

    # Discordant counts appear in two shapes: packed ("32/2") and as separate
    # headed columns ("gained"/"lost"). The second is the clearer way to print
    # them, so the audit must follow the paper there rather than lose coverage
    # on any table that adopts it.
    gain_lost: tuple[int, int] | None = None
    for seg_start, chunk in chunks:
        cells_hdr = [x.strip().lower() for x in chunk.split("&")]
        if r"\begin{tabular}" in chunk or r"\end{tabular}" in chunk:
            gain_lost = None
        # A header row is short cells across several columns. Without the length
        # and column-count guards a CAPTION explaining the words "gained" and
        # "lost" is taken for a header, and every later result silently drops out.
        hdr = [i for i, x in enumerate(cells_hdr) if len(x) <= 12]
        g = [i for i in hdr if "gained" in cells_hdr[i]]
        l = [i for i in hdr if "lost" in cells_hdr[i]]
        if len(cells_hdr) >= 3 and g and l:
            gain_lost = (g[0], l[0])
            continue
        if gain_lost and len(cells_hdr) > max(gain_lost):
            cells = [x.strip() for x in chunk.split("&")]
            b, c = _num(cells[gain_lost[0]]), _num(cells[gain_lost[1]])
            if b is not None and c is not None:
                m = re.search(re.escape(cells[gain_lost[0]].strip()), chunk)
                _emit_row(rows, line_at[seg_start + (m.start() if m else 0)], n_marks,
                          chunk, m or re.match(r"", chunk), int(b), int(c),
                          skip_cols=gain_lost)
                continue
        if _NOT_COUNTS.search(chunk):
            continue
        # "a/b" is only a discordant pair if it CAN be one: a+b cannot exceed the
        # paired sample, and "83/100" is a rate. Papers write both forms in
        # adjacent columns, so this guard is what stops the audit inventing
        # findings out of rate cells.
        # No whitespace around the slash: these papers write discordant counts
        # tight ("32/0") and two-metric rate columns spaced ("68 / 29"). Both
        # otherwise satisfy a+b <= n, so the spacing is the only thing that
        # separates them.
        # ⚠️ THE ADMISSION GATE MUST USE THE ROW'S OWN n, NOT THE GLOBAL DEFAULT.
        # Bounding a+b by `default_n` silently DROPS every row of any table whose
        # sample is larger than the default -- the row is never parsed, so it is
        # not even reported as unchecked, which is strictly worse than a false
        # positive (found 2026-08-22: a 300-prompt table with counts 111/6 and
        # 176/1 was invisible, as was tab:strata before it). The per-table
        # `% AUDIT-N:` marker already exists; it just has to reach this filter.
        found = []
        for m in re.finditer(r"(?<![\d.])(\d{1,3})/(\d{1,3})(?![\d.])", chunk):
            n_here = _n_at(n_marks, line_at[seg_start + m.start()]) or default_n
            if (int(m.group(1)) + int(m.group(2)) <= n_here
                    and int(m.group(2)) != n_here
                    and not _TALLY.match(chunk[m.end():])):
                found.append(m)
        # Prose narrates counts too ("37 prompts flipping toward harm against 4
        # away"); those carry headline claims, so match them as well.
        prose = [(m, int(m.group(1)), int(m.group(2))) for m in re.finditer(
            r"(\d{1,3})\s+prompts?\s+\w+[^.;]{0,45}?against\s+(\d{1,3})", chunk)]
        prose += [(m, int(m.group(2)), 0) for m in re.finditer(
            r"of\s+(\d{1,3})\s+discordant\s+prompts?,\s*(\d{1,3})\s+gained"
            r"[^.;]{0,60}?none\s+lost", chunk)]
        for m, b, c in [(m, int(m.group(1)), int(m.group(2))) for m in found] + prose:
            _emit_row(rows, line_at[seg_start + m.start()], n_marks, chunk, m, b, c)
    return rows


def _emit_row(rows: list[Row], line_no: int, n_marks: list, chunk: str, 
              m: re.Match, b: int, c: int,
              skip_cols: tuple[int, ...] = ()) -> None:
    """Build one Row, reading delta/p from a WINDOW around THIS result only.

    Scanning the whole chunk pairs one result's counts with a neighbouring
    result's p-value whenever a paragraph reports several contrasts -- which is
    the same class of confusion that produced the review complaint this module
    answers, so the tool must not commit it.
    """
    row = Row(line=line_no, b=b, c=c, n=_n_at(n_marks, line_no),
              context=chunk.strip()[:150])
    window = chunk[max(0, m.start() - 90):m.end() + 130]
    cells = [x.strip() for x in chunk.split("&")]

    if len(cells) > 1:  # tabular row: columns are unambiguous, read positionally
        # A count column is not a rate column: leaving gained/lost in the scan
        # makes "32" and "2" look like a 32%->2% rate pair.
        nums = [(_num(x), x) for i, x in enumerate(cells) if i not in skip_cols]
        # A rate is an INTEGER percentage cell. Requiring integrality keeps a
        # p-value column (0.052) from being read as a 5.2% rate.
        rates = [v for v, cell in nums
                 if v is not None and 0 <= v <= 100 and v == int(v)
                 and "." not in cell and cell.strip()[:1] not in "+-"]
        signed = [v for v, x in nums if v is not None and x.strip()[:1] in "+-"]
        if len(signed) == 1:
            row.delta = signed[0]
        if len(rates) >= 2:
            row.before, row.after = rates[0], rates[1]
        elif len(rates) == 1:
            row.after = rates[0]
        for x in cells:
            pv = _pval(x)
            if pv and x.strip() not in {"---", ""}:
                row.p_raw, row.p_val, row.p_bound = pv

    # inline form:  +30 (32/2, p=6.9x10^{-8}). The delta must sit IMMEDIATELY
    # before the parenthesis, else "llava-1.5-7b's -8pp (1/9" matches the -1
    # inside the model name.
    inline = re.search(
        r"(?:^|[\s,;:{(])([+-]\d+)\s*(?:pp)?\s*\(\s*" + str(b) + r"\s*/\s*"
        + str(c) + r"\s*,\s*p\s*=\s*([^)]+)\)", chunk)
    if inline:
        row.delta = float(inline.group(1))
        if pv := _pval(inline.group(2)):
            row.p_raw, row.p_val, row.p_bound = pv
    else:
        if row.delta is None:
            dm = re.search(r"(?:^|[\s,;:{(])([+-]\d+)\s*(?:pp|%)", window)
            if dm:
                row.delta = float(dm.group(1))
        if row.p_raw is None:
            pm = re.search(r"p\s*=\s*([\d.]+(?:\s*x\s*10\^\{?-?\d+\}?)?)", window)
            if pm and (pv := _pval(pm.group(1))):
                row.p_raw, row.p_val, row.p_bound = pv
    rows.append(row)


def _p_matches(raw: str, exact: float) -> bool:
    """Compare a recomputed p against the paper's DISPLAYED precision.

    Papers print rounded p-values, so an exact-equality test manufactures
    failures (6.604e-05 is a correct rendering of a stated 0.0001) while a loose
    relative tolerance would wave through a genuinely wrong digit. Match the
    precision actually shown instead.
    """
    raw = raw.strip()
    # Half-a-displayed-unit, NOT round(): Python rounds half to even, so an
    # exact 0.125 shown as 0.13 (half up, as papers write it) would be called a
    # mismatch. The displayed value need only be A valid rounding of the exact.
    m = re.fullmatch(r"([\d.]+)\s*x\s*10\^\{?(-?\d+)\}?", raw)
    if m:  # scientific: tolerance is half a unit in the mantissa's last place
        mant, expo = m.group(1), int(m.group(2))
        decimals = len(mant.split(".")[1]) if "." in mant else 0
        return abs(exact - float(mant) * 10**expo) <= 0.5 * 10 ** (-decimals + expo) + 1e-300
    m = re.fullmatch(r"(\d*)\.(\d+)", raw)
    if m:  # decimal: tolerance is half a unit in the last printed place
        return abs(exact - float(raw)) <= 0.5 * 10 ** -len(m.group(2)) + 1e-12
    return abs(exact - float(raw)) < 1e-12


def audit(path: str, default_n: int, tol_rel: float = 0.06) -> list[Row]:
    text = open(path).read()
    rows = _rows_from_tex(text, default_n)
    for r in rows:
        exact = mcnemar_exact(r.b, r.c)
        # 1. delta vs discordant counts
        n_row = r.n or default_n
        if r.delta is not None:
            implied = (r.b - r.c) / n_row * 100
            # Tables print Delta at one decimal, so compare at the printed
            # precision rather than exactly; an exact test would flag every
            # correctly-rounded row on a denominator that is not a power of ten.
            if abs(implied - r.delta) > 0.05 + 1e-9:
                r.findings.append(Finding(
                    r.line, "delta-vs-counts",
                    f"stated Delta={r.delta:+g}pp but {r.b}/{r.c} on n={n_row} "
                    f"implies {implied:+g}pp", r.context))
        # 2. delta vs the two rates
        if r.delta is not None and r.before is not None and r.after is not None:
            if abs((r.after - r.before) - r.delta) > 1e-9:
                r.findings.append(Finding(
                    r.line, "delta-vs-rates",
                    f"stated Delta={r.delta:+g}pp but rates {r.before:g}->{r.after:g} "
                    f"give {r.after - r.before:+g}pp", r.context))
        # 3. p vs discordant counts
        if r.p_val is not None:
            if r.p_bound:
                if not exact < r.p_val:
                    r.findings.append(Finding(
                        r.line, "p-vs-counts",
                        f"stated p{r.p_raw} but exact McNemar({r.b},{r.c})="
                        f"{exact:.4g}", r.context))
            elif not _p_matches(r.p_raw, exact):
                r.findings.append(Finding(
                    r.line, "p-vs-counts",
                    f"stated p={r.p_raw} but exact McNemar({r.b},{r.c})="
                    f"{exact:.4g}", r.context))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("tex")
    ap.add_argument("--n", type=int, default=100,
                    help="paired sample size assumed for delta<->count checks")
    ap.add_argument("--verbose", action="store_true",
                    help="print every parsed row, not only the failures")
    args = ap.parse_args()

    rows = audit(args.tex, args.n)
    bad = [r for r in rows if r.findings]

    if args.verbose:
        print(f"{'line':>5}  {'b/c':>7}  {'Delta':>6}  {'rates':>10}  "
              f"{'p stated':>12}  {'p exact':>10}")
        for r in rows:
            rates = (f"{r.before:g}->{r.after:g}"
                     if r.before is not None and r.after is not None else "")
            print(f"{r.line:>5}  {f'{r.b}/{r.c}':>7}  "
                  f"{(f'{r.delta:+g}' if r.delta is not None else ''):>6}  "
                  f"{rates:>10}  {(r.p_raw or ''):>12}  "
                  f"{mcnemar_exact(r.b, r.c):>10.4g}")
        print()

    # Coverage must be LOUD: a row whose p-value or delta could not be parsed is
    # a row this audit did not check, and silence there reads as a pass.
    print(f"{len(rows)} paired-result rows parsed from {args.tex} (n={args.n})")
    no_p = [r for r in rows if r.p_val is None]
    no_d = [r for r in rows if r.delta is None]
    print(f"  checked p vs counts:     {len(rows) - len(no_p)}/{len(rows)}"
          + (f"   UNCHECKED lines {[r.line for r in no_p]}" if no_p else ""))
    print(f"  checked Delta vs counts: {len(rows) - len(no_d)}/{len(rows)}"
          + (f"   UNCHECKED lines {[r.line for r in no_d]}" if no_d else ""))
    if not bad:
        print("CONSISTENT: every stated Delta matches its discordant counts and "
              "its rate pair, and every p-value matches an exact two-sided "
              "McNemar on those counts.")
        return 0
    print(f"\n{len(bad)} INCONSISTENT row(s):\n")
    for r in bad:
        for f in r.findings:
            print(f"  line {f.line}  [{f.kind}]  {f.detail}")
            print(f"      {f.context}\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
