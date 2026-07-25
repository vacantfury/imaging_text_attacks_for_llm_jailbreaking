"""Con-7 component ablation: guard-alone vs recover-only vs recover+decode.

Review-7 con 7 asks for the recover/decode split across ALL eleven attacks and
BOTH targets, reported as per-attack mean AND ensemble. The shipped Table 2 gave
six image attacks, one target, mean only.

The eleven-attack recover-only column is assembled, not fully measured, and the
missing half is an IDENTITY rather than an approximation. For a text-delivered
attack screened by a TEXT-ONLY guard (WildGuard here), recover-only and
guard-alone hand the guard the same string:

    guard_baseline.py:76      guard sees  p.encoded
    modality_complete.py:297  recover runs only `if is_multimodal`
    modality_complete.py:319  union = p.encoded   (non-multimodal)

and with decode_text=false there is no decode step; both then query the target
with the original input. So the five text chains' recover-only cells ARE their
guard-alone cells, and only the six image chains need measuring per target.
This would NOT hold for the multimodal GuardReasoner-VL, which sees the image.

Checksums against the published Table 2 (Qwen, six image attacks, gpt-5-mini)
run automatically: recover-only mean 2.0, recover+decode mean 10.7.

Usage::

    python -m src.analysis.paper_c_no_decode_ablation
"""

from __future__ import annotations

import glob
import json
import os
import re

CHAINS = ['llm_set_theory', 'llm_formal_logic', 'llm_classical_language',
          'non_llm_cipher', 'code_attack',
          'ir_figstep', 'ir_fc_flowchart', 'ir_low_contrast', 'ir_occluded',
          'ir_mm_typo', 'ir_distraction_grid']
TEXT_CHAINS = CHAINS[:5]
IMAGE_CHAINS = CHAINS[5:]

GUARD = 'wildguard'
JUDGE = 'gpt-5-mini'

# (gb/mc campaign, recover-only campaign) per target.
TARGETS = {
    'qwen2_5_vl_7b': ('paper_c_guard_panel', 'paper_c_no_decode_n100'),
    'internvl3_8b':  ('paper_c_gen2_internvl3', 'paper_c_no_decode_internvl3'),
}

# Published Table 2 values, six IMAGE attacks only, Qwen/WildGuard/gpt-5-mini.
CHECKSUM_QWEN_IMAGE = {'ro': 2.0, 'mc': 10.7}

REJUDGE_GLOB = 'outputs/autoattack_defense/rejudge/harmbench/*'


def _ts(name: str) -> str:
    m = re.search(r'_(\d{8})_(\d{6})_', name)
    return (m.group(1) + m.group(2)) if m else '0'


def _load(path: str):
    try:
        with open(path) as fh:
            return json.load(fh)
    except Exception:
        return None


def _flags(d: str) -> dict:
    """Per-prompt jailbreak flags for one cell: {prompt_id: bool}."""
    out = {}
    with open(os.path.join(d, 'raw_results.jsonl')) as fh:
        for line in fh:
            if line.strip():
                row = json.loads(line)
                out[row['id']] = bool(row.get('asr'))
    return out


def collect() -> dict:
    """(target, cond, chain) -> newest rejudge dir, cond in {gb, mc, ro}."""
    cells: dict = {}
    for d in glob.glob(REJUDGE_GLOB):
        r = _load(os.path.join(d, 'results.json'))
        if not r or r.get('asr') is None or r.get('judge_model') != JUDGE:
            continue
        target = r.get('target_model')
        if target not in TARGETS:
            continue
        panel_camp, ro_camp = TARGETS[target]
        src = (r.get('upstream_ref') or {}).get('source_dir', '')
        enc = r.get('encoding')
        chain = enc if enc in CHAINS else next(
            (c for c in CHAINS if f'_{c}_' in src), None)
        if chain is None:
            continue
        s = _load(os.path.join(src, 'results.json')) or {}
        dc = s.get('defense_config') or {}
        guard, camp = dc.get('guard_model'), s.get('campaign')
        if guard != GUARD:
            continue
        defense, dtext = r.get('defense'), dc.get('decode_text')
        # `reguard_original` marks the +rg condition, which lives in the SAME
        # campaign as mc on InternVL3 (11 mc cells + 11 +rg cells, identical in
        # every other config field). Without this exclusion a newest-wins rule
        # silently mixes the two and mc reads 58% instead of the published 63%.
        if dc.get('reguard_original'):
            continue
        if defense == 'guard_baseline' and camp == panel_camp:
            cond = 'gb'
        elif defense == 'modality_complete' and camp == panel_camp and dtext is True:
            cond = 'mc'
        elif defense == 'modality_complete' and camp == ro_camp and dtext is False:
            cond = 'ro'
        elif defense == 'modality_complete' and camp == ro_camp and dtext is True:
            # The matched within-campaign mc: same run, same six image chains as
            # the recover-only cells. This is what the published six-attack
            # Table 2 compares against, and it is what the checksum checks.
            cond = 'mc_matched'
        else:
            continue
        key = (target, cond, chain)
        t = _ts(os.path.basename(d))
        if key not in cells or t > cells[key][0]:
            cells[key] = (t, d)
    return cells


def score(cells: dict, target: str, cond: str, chains: list) -> tuple:
    """(ensemble ASR, per-attack mean, n_attacks, n_behaviors, missing)."""
    union: dict = {}
    per, missing = [], []
    for c in chains:
        # The identity above: a text chain's recover-only cell IS its gb cell.
        key = (target, 'gb' if (cond == 'ro' and c in TEXT_CHAINS) else cond, c)
        if key not in cells:
            missing.append(c)
            continue
        m = _flags(cells[key][1])
        per.append(100.0 * sum(m.values()) / len(m))
        for i, f in m.items():
            union[i] = union.get(i, False) or f
    ens = 100.0 * sum(union.values()) / len(union) if union else float('nan')
    mean = sum(per) / len(per) if per else float('nan')
    return ens, mean, len(per), len(union), missing


def main() -> None:
    cells = collect()

    print("=== CHECKSUM vs published Table 2 (Qwen, 6 IMAGE attacks) ===")
    ok = True
    for cond, recorded in CHECKSUM_QWEN_IMAGE.items():
        # mc is checked in its MATCHED form (same campaign as the recover-only
        # cells) --- that is the comparison the published table makes.
        _, mean, n, _, miss = score(cells, 'qwen2_5_vl_7b',
                                    'mc_matched' if cond == 'mc' else cond,
                                    IMAGE_CHAINS)
        bad = not (mean == mean and abs(mean - recorded) <= 0.6)
        ok &= not bad
        print(f"  {cond:3} image-only mean={mean:5.1f}  recorded={recorded:5.1f}"
              f"  ({n}/6 attacks){'  <-- MISMATCH' if bad else ''}"
              f"{'  missing=' + ','.join(miss) if miss else ''}")
    print("CHECKSUM", "PASS" if ok else "FAIL")

    print("\n=== CON 7: eleven-attack ablation, both targets (WildGuard, gpt-5-mini) ===")
    print(f"  {'target':16} {'config':26} {'mean ASR':>9} {'ensemble':>9}  coverage")
    rows = {}
    for target in TARGETS:
        for cond, label in [('gb', 'guard alone (raw input)'),
                            ('ro', 'recover only (no decode)'),
                            ('mc', 'recover + decode (mc)')]:
            ens, mean, n, nid, miss = score(cells, target, cond, CHAINS)
            rows[(target, cond)] = (mean, ens)
            note = f"{n}/11 attacks, {nid} behaviors"
            if miss:
                note += "  MISSING: " + ",".join(miss)
            print(f"  {target:16} {label:26} {mean:8.1f}% {ens:8.1f}%  {note}")

    print("\n=== LaTeX rows (harm side of tab:ablation) ===")
    for cond, label in [('gb', 'guard alone (raw input)'),
                        ('ro', 'recover only (no decode)'),
                        ('mc', 'recover $+$ decode (mc)')]:
        cs = []
        for target in TARGETS:
            mean, ens = rows[(target, cond)]
            cs += [f"{mean:.1f}", f"{ens:.0f}"]
        print(f"  {label:28} & " + " & ".join(cs) + r" \\")


if __name__ == "__main__":
    main()
