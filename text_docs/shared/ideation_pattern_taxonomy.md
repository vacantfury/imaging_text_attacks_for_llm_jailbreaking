# Ideation-Pattern Taxonomy (harvested reference)

**Source:** Microsoft ResearchStudio-Idea / `idea_spark` skill (MIT-licensed), induced from a corpus of 1,947 ICLR/ICML/NeurIPS submissions (2021–2025). Reference clone (gitignored): `other_repos/ResearchStudio/ResearchStudio-Idea/skills/idea_spark/references/`.

**What this is:** a distilled, self-contained copy of the reusable intellectual content — the 15 ideation patterns, the C00–C30 sub-pattern index, the empirical anti-patterns, the design principles, and the quality-gate methodology. We keep the *taxonomy and gates* (the ideas), not the unsupervised orchestration scaffolding (validators, mergers, byte-identical kill-switch fields) — those exist to run the skill end-to-end without a human, a different design point from our owner-collaborative `research-workflow`.

**How to use it:** as a diagnostic vocabulary during the **ideate / idea-check** stage — a checklist of moves to consider per identified gap, and a set of failure modes to audit a candidate against. Patterns are *diagnostic labels judged per-gap*, never verbatim generative templates (see design principle 1).

---

## 1. The 15 ideation patterns

| Pattern | Definition | Operational signature | When to apply |
|---|---|---|---|
| **Audit & Pivot an Assumption** | Find the load-bearing implicit assumption behind a result/defense, then relax it (extend the guarantee) or violate it (exploit / counterexample) | assumption → relax/violate → re-derive or demonstrate | A result's strength or a system's safety hinges on an assumption real settings weaken or an adversary can violate |
| **Substitute the Operator/Representation** | Replace a costly operator/representation with a cheaper surrogate that provably preserves the essential property | expensive operator → cheaper surrogate → prove property preserved | A cost/complexity bottleneck traces to an operator that can be cheaply approximated without losing what matters |
| **Liberate a Fixed Generative Component** | Treat a conventionally-fixed piece of an iterative/staged pipeline as a free design variable and redesign it | fixed component → treat as free variable → redesign for quality/efficiency | An iterative/generative pipeline inherits a default that was never the real constraint |
| **Design a Confound-Isolating Diagnostic** | Build an eval instrument that holds a confound fixed or independently varies it | confound → controlled instances → true property vs. artifact | Reported performance may reflect a shortcut/confound rather than the intended capability |
| **Unify Heterogeneous Inputs into One Space** | Map heterogeneous modalities/tasks into one shared representation/objective, subsuming bespoke pipelines | heterogeneous inputs → shared space → one uniform model | Multiple modalities/tasks run separate bespoke pipelines a shared substrate could replace |
| **Reframe as a Solvable Object** | Recast an intractable problem as a well-studied object (selection, optimization, game, relabeling) | intractable problem → recast → apply existing machinery | The native formulation is intractable but isomorphic to a class with mature solvers |
| **Manufacture the Supervisory Signal** | Derive training signal from the model itself when ground truth is absent | missing labels → signal from model's own outputs/uncertainty → train on it | Labels are scarce but the model/a generator can produce a usable proxy |
| **Encode Structure by Construction** | Bake a known invariant (symmetry, topology, physical law) into the model so it holds by construction | known invariant → encode into operator/representation → guaranteed | The problem carries a known symmetry/topology/law a generic model would relearn from data |
| **Prove Equivalence to Unify** | Show algebraically that distinct procedures/objectives are the same, collapsing stages or unifying heuristics | distinct procedures → prove algebraic equivalence → collapse/unify | Two procedures or a heuristic family look different but may optimize the same thing |
| **Decompose for Differentiated Treatment** | Partition a resource into components with differing properties, treat each differently | heterogeneous resource → partition → tailored treatment per part | Uniform treatment is suboptimal because components differ systematically *(see anti-pattern §3)* |
| **Decompose and Delegate to Solvers** | Split a task and route sub-problems to the best-suited (symbolic/external or learned) solver | monolithic task → decompose → route via structured intermediates | Part of a task is better handled by a sound external/symbolic solver than end-to-end learning |
| **Relax Discrete Search to Continuous** | Convert combinatorial structural search into a differentiable/amortized form | discrete search → relax to differentiable/amortized → joint optimization | The design space is combinatorial and exhaustive/nested search is prohibitive |
| **Adapt by Conditioning, Not Retraining** | Express new tasks as conditioning (in-context, retrieval, unified format) instead of parameter updates | new task → express as conditioning → solve at inference | Need broad generalization but per-task training is costly/infeasible |
| **Characterize a Limit, Then Surpass It** | Formalize a method class's exact expressivity/distinguishability limit, then build an operator that provably exceeds it | limit → formalize as separation criterion → augmented operator exceeds it | An established method class plateaus and a structural limit can be pinpointed |
| **Design a Property-Targeting Pretext Objective** | Construct a label-free objective whose minimization forces one specific structural property into the representation | target property → label-free objective unique to it → train representation | Generic self-supervised objectives fail to capture the specific attribute downstream needs |

## 2. Sub-pattern index (C00–C30, ≤10-word gloss)

Sub-patterns are HDBSCAN clusters over the same corpus — more specific tactical moves under each parent. Use them to sharpen a chosen pattern into a concrete mechanism.

- **Reframe as Solvable Object** — C00 recast attribution/transparency as measurable estimator problems · C21 recast RL/control as supervised sequence modeling via manufactured labels · C27 recast intractability as multi-agent games/equilibria
- **Audit & Pivot an Assumption** — C01 relocate a security signal to an overlooked locus · C05 swap distributional identifiability assumption for structural/geometric one · C11 pivot a selection/acquisition rule's criterion or precondition · C19 replace convenience regularity conditions in statistical certificates · C28 pivot a structural assumption in distributed/federated protocols · C29 pivot the regularity assumption behind convergence/regret guarantees
- **Prove Equivalence to Unify** — C06 prove probabilistic objectives algebraically equivalent, collapse pipeline stages
- **Decompose for Differentiated Treatment** — C04 compress artifacts by exploiting heterogeneous component importance
- **Substitute the Operator/Representation** — C09 route sensitive input through a low-sensitivity intermediate object · C12 relocate/swap a structural slot in staged architectures · C14 replace dense attention with property-preserving sub-quadratic surrogate · C30 substitute training-dynamics' curvature object with cheaper spectral surrogate
- **Encode Structure by Construction** — C13 encode relational connectivity topology as the prior · C16 build operators exactly commuting with a symmetry group · C20 encode the forward corruption process, invert it for recovery
- **Characterize a Limit, Then Surpass It** — C10 reinject a discarded structural object into a local iterative procedure
- **Manufacture the Supervisory Signal** — C07 use a trained model's own internal-state readouts as signal · C08 drive generators to synthesize filtered out-of-support training instances · C26 manufacture comparative/preference rewards from non-human sources
- **Design a Property-Targeting Pretext Objective** — C17 reshape contrastive pairing geometry to target one property
- **Design a Confound-Isolating Diagnostic** — C02 build evaluation instances that block/vary one confound axis
- **Unify into Shared Representation** — C18 manufacture a missing substrate so a mature recipe transfers
- **Adapt by Conditioning** — C03 express heterogeneous tasks as one conditioning schema, no retraining
- **Liberate a Fixed Generative Component** — C15 re-choose the geometric representation a 3D pipeline uses · C23 re-specify a frozen component of a diffusion/flow chain · C24 treat a generative backbone's conditioning interface as free variable
- **Decompose and Delegate to Solvers** — C25 emit machine-checkable artifacts, route to sound external solvers
- **Relax Discrete Search to Continuous** — C22 reify hand-engineered design choices as a searchable space

## 3. Anti-patterns (audit-only — never used to bias generation)

Empirically reject-favored compositions (n≥30, ≥12pp below the 58.4% corpus baseline). Consulted only when auditing a formed candidate, never during generation (design principle 5). All three involve `Decompose for Differentiated Treatment`:

- **Differentiated-Treatment + Manufacture-Signal** (worst, ~32% oral-pass): "made-up groups + made-up labels" — two stacked un-derived heuristics that can't be tested independently.
- **Differentiated-Treatment + Encode-Structure** (highest volume, n=93, ~45%): unclear whether the prior or the decomposition is doing the work.
- **Operator-Substitution + Differentiated-Treatment** (~46%): the operator's expressivity gain is conflated with the cross-group differentiation gain.

Each can survive audit only with a specific ablation that isolates which component does the work. Watch-list near-miss: Differentiated-Treatment + Reframe-as-Solvable-Object (~47%, n=95).

## 4. The 7 design principles

1. Patterns are **diagnostic vocabulary judged per-gap** — not classification labels, not verbatim generative templates (avoids convergence to corpus-incremental work).
2. Novelty comes from **multi-gap coverage + saturation-aware pattern selection**, not from which pattern "sounds" novel.
3. Both a **theory leg and an engineering leg** are expected, but the audit is signature-agnostic — any Oral-shape (theorem, scaling law, empirical reveal, surgical fix) can score full marks.
4. **Falsification must be mechanism-aware** (see §5).
5. The anti-pattern table is **empirical negative knowledge consulted only at audit time**, never during generation.
6. **Cheap kills before expensive expansion** — collision/scoop retrieval runs *before* the full write-up.
7. The audit **judges and flags; it never silently modifies** the candidate — revision is a separate, explicitly-authorized step.

## 5. Quality-gate methodology (the transferable gates)

- **Falsification-prediction structure.** Every candidate's falsification plan must name: (a) the minimal experiment, (b) which metric moves and in which direction, and (c) one named *load-bearing variable* plus a *negative control on it whose predicted effect is measured on the downstream outcome metric* — not on the variable's own value. A control that merely drives the variable to zero tests a definition, not a mechanism. Without this, "the metric moved" stays consistent with confounds (calibration, data shift) — historically the corpus's dominant reject signal.
- **Collision/scoop gate (dual-channel).** A **signature-terms** search over a ~10-month window (mechanism-specific wording from the candidate) catches recent same-mechanism work; an **alias-terms** search over a ~48-month window (a parametric-knowledge guess at what an *adjacent subfield* would call the same mechanism) catches older same-mechanism work published under different vocabulary — a purely lexical blind spot no window-widening alone fixes. Hits are relevance-truncated by lexical overlap with each channel's own terms.
- **Implementability audit.** A fresh, skeptical "implementing engineer" persona (a *separate* call from the method's author — same anti-self-answering rationale as the adversarial audit) rewrites each terse method step into something buildable. Explicitly barred from judging compute/wall-clock feasibility (that's a separate check), so an expensive-but-fully-specified step is a valid pass.
- **Adversarial separation.** The context that generated an idea must not be the context that audits it — the writer of a logic bug tends to rubber-stamp it. Run generation and audit in isolated contexts (subagents).

---

## 6. Where this plugs into our `research-workflow`

Mapping to our 13-stage workflow (see the global `research-workflow` skill). This section is the integration note; actual skill edits are tracked separately and gated on owner approval.

- **Ideate / idea-check (S0–S1):** use §1–§2 as the ideation vocabulary; apply §5's falsification structure, dual-channel collision gate, and adversarial separation as idea-check gates; audit formed candidates against §3.
- **Ground / literature (S4):** the alias-channel search and the "phrase one query in *solution* vocabulary" tip strengthen prior-art coverage (see the `scoop-check` novelty verifier and `lit-review-loop`).
- **Not adopted:** the unsupervised orchestration scaffolding (deterministic JSON validators, patch-only mergers, byte-identical kill-switch enforcement, the `next`-loop state navigator) — these serve headless end-to-end runs; our workflow is owner-collaborative and gets adversarial separation naturally via subagents and the cspaper external check.
