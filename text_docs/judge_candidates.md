# Open-weight judge-model candidates — merged landscape (2026-07-12)

Companion to `experiments_plan.md` §0 JUDGE METHODOLOGY + Round J, and `literature_review.md` §7.5. Built from three parallel landscape searches (Western open LLMs · Chinese-lab open LLMs · purpose-built safety judges), 2026-07-12. **All capability/refusal numbers are vendor/author self-reported unless a paper is cited — the Round-J human-κ bake-off is the arbiter; this doc only narrows the pool.**

## Cross-cutting findings
- **Usability (does the judge refuse?) is solvable on the open side** — there exist models *built* to not refuse: purpose-built classifiers are refusal-immune by construction, and several general models ship an explicit permissive posture (see Category B).
- **No paper has quantitatively measured judges *under-counting* encoded/rendered harm** (per-judge × per-encoding × human labels) — our Round-J is novel ground (→ `future_work.md` §9). Adjacent: judges over-flag on *tone* (Confusion-is-the-Final-Barrier, 2508.16347), miss obfuscated responses qualitatively (CodeChameleon 2402.16717, Emoji-Attack 2411.01077), and a **decode-then-judge** defense already exists (DecipherGuard, 2509.16870 — kin to our recover+decode amplifier).
- **Capability drives judge recall** (not size alone) — bigger/stronger candidates arguably best for buried encoded harm, and our cluster can serve them.

## Serveability reference (NURC, bf16 ≈ 2GB/param; MoE = TOTAL params resident)
1 GPU (≤~65GB) · 2–4 GPU · **full 8×H200 node ≈ 1.1TB** (fits ≤~600–700B fp8) · **>1 node / API-only** (giant MoEs: DeepSeek-V4-Pro 1.6T, GLM-5.x ~750B, Kimi-K2 1T). Judge pass is DECOUPLED (no targets running) → a whole node can serve one judge.

---

## Category A — Purpose-built safety judges (REFUSAL-IMMUNE by construction)
*Emit a verdict; refusal isn't in their output space. Best as the "floor" + fast/cheap arms + reasoning guards. Several already wired in `llm_model.py`.*

| Model | Base / size | Serve | Multimodal? | Multiling/zh? | Note |
|---|---|---|---|---|---|
| **HarmBench-cls** ✅wired | Llama-2-13B | 1 GPU | no | no | canonical floor; structurally OVER-flags (P0.835/R0.974) → safe pairing if worried about misses |
| **GuardReasoner / -VL / -Omni** ✅VL wired | Llama-3.x / Qwen2.5-VL | 1 GPU | VL: yes | via base | reasoning trace; beats GPT-4o+CoT; -VL can judge the rendered image directly |
| **WildGuard** ✅wired | Mistral-7B | 1 GPU | no | weak | strongest all-round text guard (F1 94.7) |
| **Llama-Guard-4** ✅wired | 12B (Llama-4 pruned) | 1 GPU | **yes** (multi-image) | yes | only natively multimodal + multilingual major-lab guard |
| **Qwen3Guard-Gen** (0.6/4/8B) | Qwen3 | 1 GPU | no | **119 langs incl. zh/Cantonese** | top recall of 14 open guards (2605.28830); unified judge precedent (2601.19487) — best for classical-Chinese arm |
| **ShieldLM** (7B) | InternLM2 / Baichuan2 | 1 GPU | no | **bilingual zh/en** | ~93% jailbreak acc; customizable via NL rules (2402.16444) |
| **PolyGuard** | undisclosed | 1 GPU | no | **17 langs incl. zh** | largest multilingual guard corpus (2504.04377) |
| **ThinkGuard** | Llama-Guard-3-8B + critique | 1 GPU | no | — | +27% macro-F1 vs LlamaGuard3 (2502.13458) |
| **ShieldGemma / -2** | Gemma-2 / -3 | 1 GPU | -2: image-only | en-only | per-category P(harm) |
| **NVIDIA AEGIS** (permissive/defensive) | Llama-Guard PEFT | 1 GPU | no | — | ships a **permissive vs defensive dial** |
| **MD-Judge** (SALAD) | Mistral-7B | 1 GPU | no | — | QA-pair, jailbreak-focused |
| **SORRY-Bench / StrongREJECT judges** | Mistral-7B / Gemma-2B | 1 GPU | no | SORRY: zh mutation set | published κ; no chat persona → no refusal failure |
| others | — | — | — | — | Granite-Guardian, Aegis1, DuoGuard, DynaGuard, Opir, CHILLGuard(zh, v.new), Qwen3Guard-Stream, gpt-oss-safeguard (below) |

## Category B — General models BUILT to be steerable / not refuse (the usability-safe judges)
*These directly answer the "many API judges refuse to judge" problem.*

| Model | Params | Serve | Why usable | Evidence |
|---|---|---|---|---|
| **Nous Hermes 4 / 4.3** | 70B / 405B / 36B | 2×A100 → node | "neutral alignment" — follows system prompt, no baked-in refusals **by design** | Hermes tech reports 2408.11857 / 2508.18255; RefusalBench 74.6% |
| **Cohere Command-A / -Vision** | 111B dense | 4×A100 | explicit **CONTEXTUAL vs STRICT** safety-mode dial; Vision can judge the image | 2504.00698 (CC-BY-NC, research OK) |
| **gpt-oss-safeguard** (20/120B) | MoE, Apache | 1×A100 (MXFP4) | built for policy-driven classification | OpenAI 2025-10; **but worst F1 in one indep. bench (2605.28830) — pilot first** |
| **Kimi K2.5 / K2-Thinking** | 1T/32B MoE | 8×H200 | **lowest documented CBRNE/general-harm refusal** of the survey; native multimodal | indep. eval 2604.03121 |
| **DeepSeek-V3.2 / R1-0528** | 671B/37B MoE | 8×H200 | comparatively permissive/inconsistent general-harm refusal; **direct ASR-judge precedent** | 2603.17368 (as judge), 2506.18543 |
| **Mistral / Mixtral family** | up to 675B MoE | 1×A100 → node | documented lighter-touch safety tuning; used as "minimal-alignment" baselines | Mistral-Large-3 Apache 2.0 |

## Category C — Capable general open models by serveability (need a steer/usability check)
- **1 GPU:** Qwen3-32B, QwQ-32B, Qwen3.6-27B, GLM-Z1-32B, Gemma-4-31B, Seed-OSS-36B, Phi-4(-reasoning), Reka-Flash-3-21B, Magistral-Small-24B, OLMo-3-32B-Think, gpt-oss-120b (MXFP4), Granite-4-30B, ERNIE-4.5-21B-A3B, Hunyuan-A13B.
- **2–4 GPU:** Llama-3.3-70B ⭐(JailbreakBench's official judge, >90% human agr., 2404.01318), Nemotron-Super-49B, GLM-4.5-Air (~1×H200), Command-A-111B, DeepSeek-V4-Flash (2–4×H200), MiniMax-M2, Hunyuan-A13B.
- **Full 8×H200 node:** Qwen3-235B-A22B, DeepSeek-V3/R1/V3.1/V3.2 (671B), GLM-4.5/4.6, Kimi-K2.x, Mistral-Large-3 (fp8), Llama-4-Maverick, Nemotron-3-Ultra (fp8), ERNIE-4.5-300B (fp8), Step-3, MiniMax-M1, Arcee-Trinity-Large, Jamba-1.7-Large.
- **Too big / API-only:** DeepSeek-V4-Pro (1.6T), GLM-5/5.1/5.2 (~750B, tight), Kimi-K2 (1T — fits 8×H200 but heavy), Qwen3-Max/3.7 (proprietary), Grok-open (base only, no instruct).

---

## Shortlist — the recommended Round-J bake-off pool (diverse across role + family + usability)
1. **HarmBench-cls** (wired) — refusal-immune FLOOR (documents the under-count).
2. **GuardReasoner-VL** (wired) — reasoning guard; can judge the rendered image directly.
3. **Qwen3Guard-Gen-8B** — multilingual guard for the **classical-Chinese** arm.
4. **Llama-3.3-70B-Instruct** — literature-validated general judge (JailbreakBench official).
5. **Nous Hermes 4-70B** or **Command-A (CONTEXTUAL)** — the usability-safe steerable general judge.
6. **A capable large open model** (Qwen3-235B / DeepSeek-V3.2 / GLM-4.5-Air / gpt-oss-120b) — capability arm for buried encoded harm; DeepSeek-V3.2 has a judge precedent, GLM/Qwen best on Chinese.

**DECIDED POOL (2026-07-12) — expanded for a cheap, broad screening bake-off.** Screening a candidate = ~40 judge calls (nearly free); only the winning TWO re-judge the full headline cells. So the pool is broad, spanning capability × type × multilingual × modality; the final panel stays two.
- **Open (downloading — see `cluster_models.md`):** already-served `harmbench-cls` / `wildguard` / `llama-guard-4` / `guardreasoner-vl` / `llama-3.1-8b` / `llama-3.3-70b`, plus new pulls `qwen3guard-gen-8b` · `shieldlm-7b` · `md-judge-v0.1` · `thinkguard` · `hermes-4-70b` · `command-a` · `glm-4.5-air`. Capability-ceiling (Qwen3-235B / DeepSeek-V3.2, 8×H200) deferred to Phase 2.
- **API arm — CHEAP TIER ONLY (owner 2026-07-12; strong/expensive flagships dropped — expensive AND prone to refuse; capability ceiling lives on the open large models):** `gpt-5-nano` (incumbent) · `gpt-5-mini` · `gemini-2.5-flash-lite` · `gemini-3.1-flash-lite` · `deepseek-v4-flash` · `glm-4.7-flashx` (· `grok-4.3` optional). DeepSeek/Z.AI cheap tiers double as *permissive* candidates; top-up only if one makes the final two. No download (API-only).

## Avoid as a *permissive* judge (documented conservative/heavy safety-RL)
Baichuan2 (200K red-team, DPO+PPO), MiniMax-M2 (~100% jailbreak resistance in indep. red-team), openPangu-7B (explicit refusal-training), gpt-oss base (over-conservative — but gpt-oss-*safeguard* is the classifier variant). Also: Snowflake-Arctic (weak general), DBRX/Yi/iFlytek (dated).

## Load-bearing caveats
- **No candidate has a *published* refusal rate for the judge task specifically** (rate content it didn't generate) — usability must be screened in Round-J step 0.
- **No candidate has a classical-Chinese-specific benchmark** — verify each on our `llm_classical_language` arm directly.
- Model IDs/specs above past the Jan-2026 cutoff are web-sourced (Gemma-4, Mistral-Large-3, Nemotron-3-Ultra, gpt-oss-safeguard, DeepSeek-V4, GLM-5.x, Kimi-K2.5 all verified real via HF; "Llama 5" is an SEO hallucination — does not exist).
