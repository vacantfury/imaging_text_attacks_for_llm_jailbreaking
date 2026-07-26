# AI leaderboards — shared reference

*Landscape of the famous AI model leaderboards (general-purpose, not only safety) plus the research literature ABOUT leaderboards (evaluation integrity: audits, gaming attacks, ranking statistics). Purpose: (a) a lookup for which leaderboards matter and what each actually measures, (b) the grounding corpus for the evaluation-integrity direction (`future_work.md` §10). Maintenance: statuses and scores go stale within months — re-verify a row before relying on it. Links are canonical homes; exact sub-paths may drift.*

*Provenance: coarse web scan, 2026-07-26 (two parallel search sweeps). This is **NOT** a lit-review-loop product — before citing any paper below in a manuscript, run the full loop (stage BibTeX → download → verify metadata). Entries the scan could not verify are marked **(unverified)**.*

## 1. Capability leaderboards — top tier by influence

| Leaderboard | Home | Mechanism | Status (2026-07) | Integrity notes |
|---|---|---|---|---|
| LMArena (Chatbot Arena) | [lmarena.ai](https://lmarena.ai) | Crowd pairwise votes → Elo/Bradley-Terry; sub-boards (Coding, Hard Prompts, Style-Control) + spinoff arenas (WebDev, RepoChat, Video) | Active; the default launch-page number | *Leaderboard Illusion* audit (private pre-release variant testing — Meta ran 27 Llama-4 variants, published 1); Llama-4-Maverick incident; style/length vote bias (Style-Control board is their countermeasure) |
| Artificial Analysis | [artificialanalysis.ai](https://artificialanalysis.ai) | Independent re-measurement: composite Intelligence Index over ~10 evals + price/speed tracking | Active, influence rising fast | Anti-self-report by design; inherits whatever contamination/quality issues its component benchmarks have |
| SWE-bench Verified / Pro | [swebench.com](https://www.swebench.com) | Real GitHub-issue patching, pass/fail against tests; Pro = contamination-resistant successor (Scale-hosted private split) | Verified saturating (top ~96%) and being deprecated; Pro taking over | ~59% of hardest Verified failures were flawed tests (OpenAI's own audit, unverified primary source); models recall repo file paths from training up to 76% ([arXiv 2512.10218](https://arxiv.org/abs/2512.10218)) |
| Humanity's Last Exam | [lastexam.ai](https://lastexam.ai) | 2,500 PhD-level expert questions (CAIS + Scale AI) | Active; headline "hardest exam" number | ~20–30% of bio/chem answers questioned (FutureHouse analysis); an HLE-Verified re-verification effort emerged 2026 |

## 2. Capability leaderboards — second tier

| Leaderboard | Home | Mechanism | Status (2026-07) | Integrity notes |
|---|---|---|---|---|
| LiveBench | [livebench.ai](https://livebench.ai) | Monthly-refreshed objective questions (no LLM judge) | Active | Designed contamination-resistant; researcher-cited more than press-cited |
| LiveCodeBench | [livecodebench.github.io](https://livecodebench.github.io) | Post-cutoff competitive-programming problems only | Active (v6) | Different mirror sites report different leaders — reproducibility flag |
| ARC-AGI (ARC Prize) | [arcprize.org](https://arcprize.org) | Abstract-reasoning grids; v3 (2026) is interactive/agentic | Active; v2 nearing saturation, v3 new | Cross-tracker score disagreement on v3 |
| FrontierMath (Epoch AI) | [epoch.ai/frontiermath](https://epoch.ai/frontiermath) | Research-level math, expert-authored, unpublished | Active (v2, June 2026) | v1 audit found errors in 42% of problems → v2; OpenAI secretly funded it with privileged access pre-o3-launch (disclosure scandal) |
| OpenRouter rankings | [openrouter.ai/rankings](https://openrouter.ai/rankings) | Usage-based: real token share through the routing gateway | Active | Not a quality signal — measures adoption (price/availability), not capability |
| SEAL (Scale AI) | [scale.com/leaderboard](https://scale.com/leaderboard) | Private held-out evals + SEAL Showdown crowd preference | Active | Independence clouded since Meta's 49% stake in Scale (2025); Scale also hosts HLE and SWE-bench Pro's private split |
| Vals AI | [vals.ai](https://www.vals.ai) | Domain-expert benchmarks (legal, finance) | Active; growing in enterprise/procurement | Commercially positioned (sells reports/consulting) alongside its public boards |
| HELM (Stanford CRFM) | [crfm.stanford.edu/helm](https://crfm.stanford.edu/helm) | Holistic multi-metric framework; hosts MedHELM, HELM Safety, AIR-Bench | **Maintenance mode since 2026-06** (quarterly only) | Historically the "beyond one accuracy number" reference; too slow for the release pace |

## 3. Retired / superseded (cautionary tales)

- **Hugging Face Open LLM Leaderboard** — [huggingface.co/open-llm-leaderboard](https://huggingface.co/open-llm-leaderboard). Retired 2025. WAS the default open-weight reference 2023–24; killed largely by contamination/Goodhart gaming of its static suite. The canonical case of a leaderboard dying of gaming.
- **AlpacaEval 2.0** — [tatsu-lab.github.io/alpaca_eval](https://tatsu-lab.github.io/alpaca_eval/). Technically maintained, widely considered saturated/superseded.
- **GPQA Diamond / MMLU-Pro** — near-saturated at the frontier; now live mainly as components inside composite indices (Artificial Analysis), not destination leaderboards.

## 4. Safety-specific leaderboards

| Leaderboard | Home | What it is |
|---|---|---|
| HarmBench | [harmbench.org](https://www.harmbench.org) | The standard red-teaming/ASR benchmark + rubric (this repo's judge rubric builds on it); a methodology more than a live site |
| JailbreakBench | [jailbreakbench.github.io](https://jailbreakbench.github.io) | Open attack/defense robustness leaderboard on JBB-Behaviors (NeurIPS 2024 D&B) |
| AIR-Bench | [crfm.stanford.edu/helm/air-bench](https://crfm.stanford.edu/helm/air-bench/latest/) | Regulation-derived risk taxonomy (314 risks / 45 categories), HELM-hosted |
| Enkrypt AI Safety Leaderboard | [enkryptai.com](https://www.enkryptai.com) | Vendor-run continuous red-teaming of 200+ models; standard vendor conflict-of-interest caveat |
| FLI AI Safety Index | [futureoflife.org/ai-safety-index](https://futureoflife.org/ai-safety-index/) | Expert-panel GPA-style grading of LABS (not models), biannual; Summer 2026: no lab above C+ |

## 5. Research ABOUT leaderboards — evaluation-integrity literature (2024–2026)

### 5.1 Audits / critiques

- **The Leaderboard Illusion** — Singh et al. (Cohere Labs + Stanford/Princeton/UW/MIT/Ai2), **NeurIPS 2025 D&B** — [arXiv 2504.20879](https://arxiv.org/abs/2504.20879). The marquee audit: Arena's undisclosed private testing, unequal sampling, and battle-data training advantages favor big labs. LMArena published a rebuttal.
- **Who Defines "Best"?** — Jung et al., **FAccT 2026** — [arXiv 2604.21769](https://arxiv.org/abs/2604.21769). Arena's prompt mix is topic-skewed; rankings shift across slices; ships a reweighting tool.
- **Measuring what Matters** — Bean, Rocher et al. (Oxford + 41 co-authors), **NeurIPS 2025** — [arXiv 2511.04703](https://arxiv.org/abs/2511.04703). Construct-validity review of 445 LLM benchmarks.
- **Automated Benchmark Auditing (ABA)** — Wang et al. (Duke/Together AI/Stanford, Zou group) — [arXiv 2605.26079](https://arxiv.org/abs/2605.26079). Agentic auditor over 168 benchmarks; >25% of tasks flawed; filtering shifts rankings.
- **Frontier Lag** — Gringras & Salahshoor — [arXiv 2605.04135](https://arxiv.org/abs/2605.04135). Bibliometric audit: papers evaluate models far behind the frontier and over-generalize.
- **AI Cartography** — Hardy et al. — [arXiv 2605.25272](https://arxiv.org/abs/2605.25272) (venue **unverified**). Factor-analysis of Open LLM Leaderboard scoring; correlated sub-benchmarks inflate apparent precision.
- **SOTA claims position paper** — Oh — [arXiv 2605.17273](https://arxiv.org/abs/2605.17273) (venue **unverified**). >50% of top head-to-heads fail at least one "SOTA" property.
- **Benchmark Health Index** — [arXiv 2602.11674](https://arxiv.org/abs/2602.11674) (**unverified authors**). Static benchmarks lose ranking signal in <2 years on average.
- Contamination detection: systematic review at **ACL 2026 GEM** (Anthology 2026.gem-main.50); survey [arXiv 2410.18966](https://arxiv.org/abs/2410.18966); fragility under reasoning models [arXiv 2510.02386](https://arxiv.org/abs/2510.02386); watermark-based detection [arXiv 2502.17259](https://arxiv.org/abs/2502.17259). Consensus: no method reliable across contamination types.

### 5.2 Attacks / gaming

- **Vote rigging on Chatbot Arena** — **ICML 2025** — [arXiv 2501.17858](https://arxiv.org/abs/2501.17858). Hundreds of targeted votes shift rankings (model identified via watermark/classifier).
- **Adversarial manipulation of voting leaderboards** — [arXiv 2501.07493](https://arxiv.org/abs/2501.07493). ~1,000 votes suffice; >95% authorship identification; worked with Arena devs → reCAPTCHA/login mitigations.
- **Dropping a handful of preferences flips top rankings** — Huang et al., ICML 2025 MFHAIA workshop oral — [arXiv 2508.11847](https://arxiv.org/abs/2508.11847). Worst-case removal of a tiny vote fraction flips Bradley-Terry top ranks; auditing tool released.
- **Selective adversarial attacks on benchmarks** — ITMO — [arXiv 2510.13570](https://arxiv.org/abs/2510.13570). Perturb test items to degrade/boost ONE model's score.
- **Unified perturbation framework** — Oyarhoseini, Lin, Karimi — [arXiv 2605.15761](https://arxiv.org/abs/2605.15761) (ICML'26 CTB workshop). Unifies stability analysis and manipulation attacks for Bradley-Terry leaderboards.
- **Hidden measurement error in LLM pipelines** — [arXiv 2604.11581](https://arxiv.org/abs/2604.11581). Frames private-variant testing as best-of-K exploitation of pipeline noise.
- Style/judge-side exploit surfaces: LMSYS's own [style-control analysis](https://lmsys.org/blog/2024-08-28-style-control/) (length/markdown manipulate voters); self-preference bias of LLM judges [arXiv 2410.21819](https://arxiv.org/abs/2410.21819), [arXiv 2604.22891](https://arxiv.org/abs/2604.22891).
- Adjacent (agents gaming their own evals, not public leaderboards): METR's o3 RE-Bench reward-hacking finding (30% of runs); [arXiv 2606.07379](https://arxiv.org/abs/2606.07379); [arXiv 2605.02964](https://arxiv.org/abs/2605.02964).

### 5.3 Meta-evaluation statistics / fixes

- **Resolution diagnostics for paired evaluation** — [arXiv 2605.30315](https://arxiv.org/abs/2605.30315) (venue **unverified**). Many adjacent leaderboard ranks are statistically unresolved at standard power.
- **Rank intervals for leaderboards** — [arXiv 2606.08679](https://arxiv.org/abs/2606.08679) (**unverified authors**). Hierarchical conformal rank confidence intervals.
- **Low Rank for Rank** — [arXiv 2605.29395](https://arxiv.org/abs/2605.29395). Uncertainty-aware per-task ranking under sparse pairwise comparisons.
- **Beyond static leaderboards (predictive validity for agents)** — [arXiv 2606.19704](https://arxiv.org/abs/2606.19704). Adversarial-perturbation suite testing whether leaderboard scores predict held-out performance.
- Platform-side fixes: Arena's bootstrap-verified vs provisional scores + Style-Control board; decontaminated SWE successors (SWE-MERA [arXiv 2507.11059](https://arxiv.org/abs/2507.11059), SWE-rebench [arXiv 2505.20411](https://arxiv.org/abs/2505.20411)).

## 6. Crowdedness read (as of the 2026-07-26 scan — treat named gaps as race signals, not openings)

Active and accelerating (~25 papers in 18 months) but young: outside a few main-venue anchors (Leaderboard Illusion at NeurIPS D&B, vote rigging at ICML, FAccT slicing), most of the statistics sub-bucket is still arXiv/workshop-tier. No single group owns the area: Cohere Labs + academic coalition hold the marquee audit; diffuse smaller groups do the attack and statistics work; LMArena participates defensively.

- **Heavily worked:** Arena-specific audits/attacks (6–7 dedicated papers); "yet another contamination-detection survey".
- **Thinner at scan time** (each already showing entrants — re-verify before betting): forensic/defensive *detection* of rigged submissions (attack papers stop at "it's possible"); a consolidated flagship audit of SWE-bench (findings exist but scattered); an external HLE audit (already closing — FutureHouse + HLE-Verified); bridging the rank-instability statistics with the attack literature into leaderboard-design fixes (the unified-perturbation paper is the first mover).
- **Fastest-growing new wave (2026):** bibliometric/meta-science audits of evaluation *practice* itself (Frontier Lag, Benchmark Health Index, ABA).
