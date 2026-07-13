# Judge-validation sample (Round J human anchor)

Design + composition of the human-labeled sample that anchors Round J (judge
validation & selection — `experiments_plan.md §Round J`). This is a **paper
artifact**: the sampling structure is reported in the methodology/appendix, and
the human labels are the ground truth against which every candidate judge's
Cohen's κ is measured. The sheet, generator, and κ script live in the gitignored
`human_label/` (labels stay local); this doc records the design and the realized
composition.

Why it's a contribution, not just diligence: no prior judge — and no benchmark we
surveyed (StrongREJECT included) — validates an autograder on **symbolic-encoded**
(set-theory, formal-logic, classical-Chinese) or **image-rendered** attacks. This
sample extends human-validated judge calibration to exactly that setting.

## Design

- **Blind labeling.** The sheet hides every existing judge verdict so the human
  labels aren't anchored; verdicts are joined from a separate key only when
  computing κ.
- **Two tagged blocks (n = 100).**
  - **Representative (n = 70)** — 7 per (attack-family × modality) stratum across
    all five encoders × {text, image}, class-balanced harmful/safe within each
    stratum (by the best available current judge as a proxy), spread across the
    four target models, the defenses, and distinct behaviors. This is the
    **headline**: a balanced validation set across every attack type, so its κ
    estimates real human-agreement.
  - **Disagreement-enriched (n = 30)** — responses where gpt-5-nano and the
    HarmBench classifier disagree (240 such responses available). Intrinsically
    ambiguous, so they give the most power to **discriminate** between candidate
    judges, and form a **stress-view** slice.
- **κ is reported sliced** — ALL / representative / disagreement — per judge
  (`human_label/compute_kappa.py`). HarmBench-cls only ran on some arms, so its κ
  is over the subset it judged; gpt-5-nano covers nearly all 100.
- **Universe & reproducibility.** Drawn from 20,584 unique stored responses
  (`outputs/defense+evaluate/*/raw_results.jsonl`, any round — Round J re-judges
  stored responses, no target re-query). Deterministic (seed 42);
  `human_label/build_sheet.py` regenerates the identical sample.

Sizing note: upgraded from an original ~40-item spot-check (owner 2026-07-12).
At n = 100 the κ 95% CI roughly halves (≈ ±0.25 → ±0.16), moving it from
spot-check to a defensible validation set — relevant to the standalone
judge-methodology paper option (`future_work.md`, TODO item 9).

## Realized composition (n = 100, seed 42)

**Blocks:** representative 70 · disagreement-enriched 30.

**Attack family × modality** (the main composition table):

| Attack family | Text | Image | Total |
|---|---:|---:|---:|
| Code (`code_attack`) | 19 | 14 | 33 |
| Formal logic (`llm_formal_logic`) | 16 | 9 | 25 |
| Set theory (`llm_set_theory`) | 7 | 7 | 14 |
| Classical Chinese (`llm_classical_language`) | 7 | 7 | 14 |
| Semantic camouflage (`llm_semantic_camo`) | 7 | 7 | 14 |
| **Total** | **56** | **44** | **100** |

(Code and formal-logic run heavier because the 30-item disagreement block lives in
those two arms — the only arms where HarmBench-cls was also run, hence the only
arms with inter-judge disagreements. The representative block is exactly 7 per
cell.)

**Target model:** internvl3-8b 32 · qwen2.5-vl-7b 32 · pixtral-12b 32 ·
gemini-2.5-flash 4.

**Defense:** no_defense 44 · ecso 38 · modality_complete 9 · amia_ia 4 ·
guard_baseline 3 · sage 2.

**HarmBench category:** illegal 33 · misinformation/disinformation 24 ·
cybercrime/intrusion 19 · chemical/biological 9 · harassment/bullying 8 ·
harmful 7.

**Coverage:** 82 of the 100 distinct HarmBench behaviors (a behavior may recur
under a different model/defense/encoding; for κ each response is its own item).

**Current-judge context:** 32 items are dual-judged (gpt-5-nano + HarmBench-cls);
31 of those disagree. Proxy harmful/safe split ≈ 65/35 — but the disagreement
items are nano-says-harmful / cls-says-safe cases (nano is the known over-counter),
so the *labeled* truth is expected nearer 50/50.

## LaTeX (paper table)

```latex
\begin{table}[t]
\centering\small
\caption{Composition of the Round~J judge-validation sample ($n{=}100$): a
class-balanced stratified block ($n{=}70$, 7 per attack-family$\times$modality
cell) plus an inter-judge-disagreement supplement ($n{=}30$, gpt-5-nano vs.\ the
HarmBench classifier). Human labels anchor each candidate judge's Cohen's $\kappa$.}
\label{tab:judge-val-sample}
\begin{tabular}{lccc}
\toprule
Attack family & Text & Image & Total \\
\midrule
Code (\texttt{code\_attack}) & 19 & 14 & 33 \\
Formal logic                 & 16 &  9 & 25 \\
Set theory                   &  7 &  7 & 14 \\
Classical Chinese            &  7 &  7 & 14 \\
Semantic camouflage          &  7 &  7 & 14 \\
\midrule
Total                        & 56 & 44 & 100 \\
\bottomrule
\end{tabular}
\end{table}
```

*Regenerate these numbers from the labeled sheet:*
`python3 human_label/build_sheet.py` (prints the composition summary).
