"""Richer benign-utility analysis for Paper C (review-6 con 5 + question 4).

Con 5: *"over-refusal alone does not capture utility loss… the broad claim that
81–92% refusal is impractical to deploy should be supported by a more complete
benign utility analysis."* Question 4 asks specifically for **paired per-example
refusal transitions**, **confidence intervals for over-refusal**, **latency**,
and helpfulness of answers that did pass.

Everything here is computed from artifacts already on disk — no target
inference, no new judging. Three things the paper currently leaves on the table
turn out to be recoverable for free:

* **The refusal judge is already 3-class.** `ORBenchEvaluator` records
  `direct_answer` / `direct_refusal` / `indirect_refusal` per example, but the
  paper collapses it to one over-refusal number. The split matters for con 5:
  an *indirect* refusal (hedged, partial, redirected) is a different utility
  loss than a flat "I can't help with that".
* **Paired transitions**, because per-example refusal flags are stored. This is
  what separates "the guard refused a benign request the pipeline would have
  answered" from "the target was going to refuse anyway" — precisely the causal
  question con 5 raises about attributing refusal to recovery exposure.
* **Cost**, from `elapsed_seconds` + `target_usage`/`defense_usage`. This also
  answers con 11 (the "single-pass" wording vs the real number of target calls).

The one thing con 5 asks for that is NOT free is helpfulness of the answers that
passed — that needs a judging pass over the stored responses. It is deliberately
left out rather than approximated.

Usage::

    python -m src.analysis.paper_c_benign_utility
"""

from __future__ import annotations

import glob
import json
import os
import re
from collections import defaultdict
from typing import Optional

from .guard_threshold import load_config, wilson

REJUDGE_BENIGN = 'outputs/autoattack_defense/rejudge/orbench_benign_hard/*'
CAMPAIGN = 'paper_c_guard_panel_benign'
TARGET = 'qwen2_5_vl_7b'

# Which prompt_transform step each benign variant came from. The paper reports
# over-refusal as avg(text, image), so both must be tracked separately.
VARIANTS = {'text': 'non_llm_baseline', 'image': 'ir_plain'}

GUARD_SHORT = {
    'wildguard': 'WildGuard', 'llama_guard_3_8b': 'LlamaGuard-3',
    'qwen3guard_gen_8b': 'Qwen3Guard', 'thinkguard': 'ThinkGuard',
    'guardreasoner_vl_7b': 'GuardReasoner', 'none': '—',
}


def _lj(path: str) -> Optional[dict]:
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except Exception:
        return None


def _stamp(name: str) -> str:
    m = re.search(r'_(\d{8})_(\d{6})_', name)
    return (m.group(1) + m.group(2)) if m else '0'


def collect_cells() -> dict:
    """(defense, guard, variant) -> {rejudge_dir, source_dir}, newest wins."""
    sel: dict[tuple[str, str, str], tuple[str, dict]] = {}
    for d in glob.glob(REJUDGE_BENIGN):
        r = _lj(os.path.join(d, 'results.json'))
        if not r:
            continue
        src = (r.get('upstream_ref') or {}).get('source_dir', '')
        s = _lj(os.path.join(src, 'results.json')) or {}
        if s.get('campaign') != CAMPAIGN or s.get('target_model') != TARGET:
            continue
        step = (s.get('upstream_ref') or {}).get('source_dir', '')
        variant = next((v for v, stem in VARIANTS.items()
                        if f'/{stem}_' in step or step.endswith('/' + stem)), None)
        if variant is None:
            continue
        guard = (s.get('defense_config') or {}).get('guard_model', 'none')
        key = (r.get('defense'), guard, variant)
        t = _stamp(os.path.basename(d))
        if key not in sel or t > sel[key][0]:
            sel[key] = (t, {'rejudge': d, 'source': src, 'source_results': s})
    return {k: v[1] for k, v in sel.items()}


def _rows(d: str) -> dict[str, dict]:
    out = {}
    with open(os.path.join(d, 'raw_results.jsonl'), encoding='utf-8') as fh:
        for line in fh:
            if line.strip():
                row = json.loads(line)
                out[row['id']] = row
    return out


def _classes(rows: dict[str, dict]) -> dict[str, int]:
    """3-class counts from the stored refusal-judge label."""
    c: dict[str, int] = defaultdict(int)
    for row in rows.values():
        label = row.get('refusal_judge_output') or (
            'direct_refusal' if row.get('refusal') else 'direct_answer')
        c[label] += 1
    return dict(c)


def main() -> int:
    cfg = load_config()
    conf = cfg['report']['wilson_confidence']
    cells = collect_cells()
    if not cells:
        print('no benign cells found')
        return 2

    # ---------------- 1. three-class breakdown + CIs ----------------
    print('=' * 96)
    print('BENIGN UTILITY — 3-class refusal breakdown (the paper reports only the '
          'collapsed over-refusal %)')
    print(f'{"defense":18}{"guard":15}{"var":6}{"n":>4}'
          f'{"answered":>10}{"direct ref":>12}{"indirect":>10}'
          f'{"over-refuse [95% CI]":>26}')
    for key in sorted(cells, key=lambda k: (k[0], k[1], k[2])):
        defense, guard, variant = key
        rows = _rows(cells[key]['rejudge'])
        n = len(rows)
        cl = _classes(rows)
        refused = sum(1 for r in rows.values() if r.get('refusal'))
        lo, hi = wilson(refused, n, conf)
        print(f'{defense:18}{GUARD_SHORT.get(guard, guard):15}{variant:6}{n:>4}'
              f'{cl.get("direct_answer", 0):>10}{cl.get("direct_refusal", 0):>12}'
              f'{cl.get("indirect_refusal", 0):>10}'
              f'{100 * refused / n:>14.0f}% [{100 * lo:.0f}-{100 * hi:.0f}]')

    # ---------------- 2. paired per-example transitions vs floor ----------------
    print()
    print('=' * 96)
    print('PAIRED TRANSITIONS vs the no-defense floor (same benign example, same '
          'variant) — this is what')
    print('separates "the defense refused something the pipeline would have '
          'answered" from "it was refused anyway".')
    print(f'{"defense":18}{"guard":15}{"var":6}'
          f'{"kept ans":>10}{"NEWLY REF":>11}{"recovered":>11}{"already ref":>12}'
          f'{"net over-refusal":>18}')
    floors = {v: cells.get(('no_defense', 'none', v)) for v in VARIANTS}
    for key in sorted(cells, key=lambda k: (k[0], k[1], k[2])):
        defense, guard, variant = key
        if defense == 'no_defense':
            continue
        floor = floors.get(variant)
        if floor is None:
            continue
        f_rows, c_rows = _rows(floor['rejudge']), _rows(cells[key]['rejudge'])
        shared = sorted(set(f_rows) & set(c_rows))
        kept = newly = recov = already = 0
        for i in shared:
            fr, cr = bool(f_rows[i].get('refusal')), bool(c_rows[i].get('refusal'))
            if not fr and not cr:
                kept += 1
            elif not fr and cr:
                newly += 1
            elif fr and not cr:
                recov += 1
            else:
                already += 1
        net = newly - recov
        print(f'{defense:18}{GUARD_SHORT.get(guard, guard):15}{variant:6}'
              f'{kept:>10}{newly:>11}{recov:>11}{already:>12}'
              f'{net:>+13} / {len(shared)}')

    # ---------------- 3. cost per accepted request ----------------
    print()
    print('=' * 96)
    print('COST — target/guard calls per benign prompt and wall-clock (answers con '
          '11: what "single-pass" costs)')
    print(f'{"defense":18}{"guard":15}{"var":6}'
          f'{"target calls/prompt":>21}{"guard calls/prompt":>20}{"elapsed s":>11}')
    for key in sorted(cells, key=lambda k: (k[0], k[1], k[2])):
        defense, guard, variant = key
        s = cells[key]['source_results']
        n = s.get('count') or 0
        tgt = ((s.get('target_usage') or {}).get('total') or {}).get('inference_count', 0)
        gd = (((s.get('defense_usage') or {}).get('guard') or {}).get('total') or {})
        gcalls = gd.get('inference_count', 0)
        el = s.get('elapsed_seconds')
        print(f'{defense:18}{GUARD_SHORT.get(guard, guard):15}{variant:6}'
              f'{(tgt / n if n else 0):>21.2f}{(gcalls / n if n else 0):>20.2f}'
              f'{(el if el is not None else float("nan")):>11.0f}')

    print()
    print('NOT computed here (needs a judging pass over the stored responses, not '
          'free): helpfulness/')
    print('correctness of the answers that PASSED. Con 5 asks for it explicitly; '
          'it is omitted rather than approximated.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
