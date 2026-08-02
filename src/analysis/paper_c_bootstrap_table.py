"""Review-20 con 2/Q2 — the full per-configuration joint bootstrap table.

The paper summarizes the frontier emptiness as "bootstrap P<0.5 for all 30
configurations"; the reviewer objects that a thresholded summary resembling a
p-value hides the actual distribution. This emits the per-configuration joint
probabilities themselves, one row per (target, guard, condition):

  P(ASR<=40)                 marginal, the abstract's ASR bound alone
  P(ASR<=40 & OR<=70)        the emptiness claim at its LOOSEST over-refusal
                             bound (joint P is monotone in the OR bound, so
                             this upper-bounds every tighter bound's P)
  P(ASR<=50 & OR<=50)        the relaxed corner where exactly one config
                             crosses (LlamaGuard-3 +rg on Qwen)

Reuses review-19's bootstrap vectors verbatim (same seed, same N=10^4, same
r1-pinned cells) so the numbers agree with the published summary statement.
No new runs, no API, no cluster.

Usage:  .venv/bin/python -m src.analysis.paper_c_bootstrap_table
"""

from __future__ import annotations

import numpy as np

from src.analysis.paper_c_review19 import SEED, TARGETS, two_axes_and_bootstrap

GUARD_TEX = {
    "wildguard": "WildGuard",
    "llama_guard_3_8b": "LlamaGuard-3",
    "qwen3guard_gen_8b": "Qwen3Guard",
    "thinkguard": "ThinkGuard",
    "guardreasoner_vl_7b": "GuardReasoner",
}
COND_TEX = {"gb": r"\emph{gb}", "mc": r"\textsc{mc}", "rg": r"$+$\textsc{rg}"}
TARGET_TEX = {"qwen2_5_vl_7b": "Qwen2.5-VL-7B", "internvl3_8b": "InternVL3-8B"}


def fmt_p(p: float) -> str:
    if p < 0.001:
        return "$<.001$"
    return f"${p:.2f}$".replace("0.", ".")


def main() -> None:
    rng = np.random.default_rng(SEED)
    n_rows = 0
    for target in TARGETS:
        rows = two_axes_and_bootstrap(target, rng)
        print(f"\n% ---- {TARGET_TEX[target]} ----")
        for r in rows:
            a, v = r["_asr_b"], r["_ref_b"]
            pm40 = float(np.mean(a <= 40))
            pj40 = float(np.mean((a <= 40) & (v <= 70)))
            pj50 = float(np.mean((a <= 50) & (v <= 50)))
            n_rows += 1
            print(
                f"{GUARD_TEX[r['guard']]:>14} & {COND_TEX[r['cond']]:>12} & "
                f"{r['asr']:.0f} & {r['ref']:.0f} & "
                f"{fmt_p(pm40)} & {fmt_p(pj40)} & {fmt_p(pj50)} \\\\"
                f"   % asr CI [{r['asr_lo']:.0f},{r['asr_hi']:.0f}]"
            )
    print(f"\n% {n_rows} configurations total")


if __name__ == "__main__":
    main()
