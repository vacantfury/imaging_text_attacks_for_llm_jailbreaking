Reviewer #1
Questions
1. Summary of the paper -- not a review.
This paper investigates the vulnerability of LLM-based AI systems to a type of adversarial attack (aka jailbreaks) where a harmful natural language prompt is encoded using an abstract mathematical formalism.
2. Reason(s) to accept.
This is a very solid paper overall. See Strengths in my review below.
3. Reason(s) to reject.
I have an issue with their use of the term "semantics". See Weaknesses in my review below.
4. Detailed Review, comments, suggestions, typos
This paper investigates the vulnerability of LLM-based AI systems to a type of adversarial attack (aka jailbreaks) where a harmful natural language prompt is encoded using an abstract mathematical formalism. For example, one existing jailbreak of this kind converts a prompt into a set theory problem. Here, the authors explore 6 mathematical jailbreaks. 3 use a "helper LLM" to transform the harmful prompt, while the others uses deterministic rules that insert mathematical notation while keeping the text mainly intact (e.g. splitting the text into 6 chunks and representing them as an addition equation). Two of the LLM-based attacks are novel: they use formal logic or quantum mechanics rather than set theory. Experiments on 2 safety benchmarks (including a benchmark-standard judge and metric) cover 8 LLMs. Results show their formal logic encoding achieves a similar attack success rate than set theory encoding, outperforming it on more recent target LLMs (potentially due to a higher level of abstraction). They also show that the high success rate of these attacks relies not on simple pattern matching with mathematical notation (as in the rule-based attacks), but on the semantic reasoning capabilities of the helper model, as LLM-based methods achieve much higher success rates. They also test "repeat post-processing", which just means repeating the prompt twice (as a single input to the target LLM), which is shown not to increase success rates substantially.

I think this is a solid paper, aside from an issue I have regarding their use of the term "semantics".

Strengths:
- It addresses an increasingly important issue: AI safety, specifically the robustness of LLM guardrails against adversarial attacks (aka jailbreaks).
- Clear, well organized, and very well written.
- Somewhat novel: their formal logic encoding is new as far as I know. It is similar to set theory encoding, but uses a different mathematical formalism, and achieves similar success rates. The comparison between LLM-based and rule-based attacks is also novel according to the authors.
- Methods and experiments are technically sound as far as I can tell (but I am not an very knowledgeable on formal logic or quantum mechanics).
- Good coverage of related work.
- Code is available (in an anonymized repo). This helps reproducibility and uptake.

Weaknesses:
- I think it is inappropriate to say that the rule-based methods preserve the semantics of the harmful prompt, while the LLM-based methods transform them (e.g at the end of Section 3.1, Figure 2, beginning of Section 3, etc.). The LLM-based methods must still preserve semantics somehow, or the meaning of the encoded prompt does not align with that of the unencoded prompt, in which case the LLM response might be harfmul in some ways, but won't actually answer the original question. Some parts of the texts imply that "preserving semantics" means leaving the text largely intact while introducing math notation in it, but this would be a stretch, at least if we are using the conventional sense of "semantics" (i.e. meaning) -- and surely the semantics are not fully being preserved by these changes (although it is easier to reconstruct the unencoded prompt than it is with LLM-based methods). It could actually be argued that the LLM-based approaches are more "semantics-preserving" than the rule-based ones. I think this really needs to be cleared up.
- The inclusion of "repeat post-processing" seems like an unrelated add-on. They say that this serves as "a controlled robustness probe to test whether encoding attacks are sensitive to surface-level text augmentation." But that's just a single, trivial "augmentation", and I just don't see the point. What does it matter that mathematical encoding attacks are "robust to simple text augmentation"? Who is going to augment them?
- The study is limited to English.
- The submission didn't strictly follow the template and author instructions: appendix was supposed to be 4 pages max. The header on page 1 is different than the others: it doesn't say "Proceedings of ML Research", and it adds "DOI: O". Also, the logo on p. 1 is smaller than the others. Please make sure the paper adheres to the specified format.

Comments, suggestions, typos:
- Section 2: Put the first sentence (fragment) of each paragraph in bold (or create subsections).
- Section 2: is "Deceptive Delight" actually encoding based? How?
- Section 3.2: again, put paragraph headers in bold.
5. Recommendation
Accept -- Paper above the acceptance threshold. Solid work. Clear and sound contribution.
Reviewer #2
Questions
1. Summary of the paper -- not a review.
Tests bypasses to LLM safety filters using prompts encoded as math problems. The paper presents experiments testing various encodings across multiple models and benchmarks. The results demonstrate that semantic transformations of mathematical encodings provide higher bypass rates than strictly rule-based transformations.
2. Reason(s) to accept.
Investigates critical issue of AI safety and model alignment.
Systematically experiments across multiple models and benchmarks.
Proposes a new encoding approach and compares it against other methods.
3. Reason(s) to reject.
Some of the conclusions are derived via automatic evaluation only.
Validation/studies would help ensure the conclusions and real world applicability.
4. Detailed Review, comments, suggestions, typos
This paper provides a systematic exploration of math encoding techniques to evade safety mechanisms of language models. The comparison between experiments using LLM-based and rule-based encoding offers valuable insights into the necessity of semantic transformation when using mathematical bypasses. The extensive evaluation across models and benchmarks helps demonstrate this, though the paper would benefit from discussing possible mitigation strategies and diving deeper into the limitations of their work. A few improvements to readability can be made by expanding on some of the methodological steps.
5. Recommendation
Accept -- Paper above the acceptance threshold. Solid work. Clear and sound contribution.
Reviewer #3
Questions
1. Summary of the paper -- not a review.
The paper investigates vulnerabilities in Large Language Model (LLM) safety mechanisms by introducing jailbreak attacks based on mathematical encoding. The core idea is to transform harmful prompts into formal mathematical problems (e.g., using set theory, formal logic, or quantum-style formulations) so that the safety filters fail to recognize the underlying malicious intent.
2. Reason(s) to accept.
The topic is highly relevant to AI safety research, and the paper provides a clear technical contribution and empirical evaluation. The insight that semantic mathematical reformulation (not simple symbolic masking) is the main factor of the attack success is a meaningful contribution. However, more methodological details about the datasets, prompt generation process, and statistical analysis would further strengthen reproducibility.
3. Reason(s) to reject.
The topic is highly relevant to AI safety research, and the paper provides a clear technical contribution and empirical evaluation. The insight that semantic mathematical reformulation (not simple symbolic masking) is the main factor of the attack success is a meaningful contribution. However, more methodological details about the datasets, prompt generation process, and statistical analysis would further strengthen reproducibility.
4. Detailed Review, comments, suggestions, typos
The topic is highly relevant to AI safety research, and the paper provides a clear technical contribution and empirical evaluation. The insight that semantic mathematical reformulation (not simple symbolic masking) is the main factor of the attack success is a meaningful contribution. However, more methodological details about the datasets, prompt generation process, and statistical analysis would further strengthen reproducibility.
5. Recommendation
Weak Accept -- Borderline paper. I'm leaning towards accepting.
Reviewer #4
Questions
1. Summary of the paper -- not a review.
The paper studies jailbreak attacks that recast harmful prompts as coherent mathematical problems, using formalisms such as set theory, formal logic, and quantum mechanics. It compares LLM-based semantic encodings with rule-based mathematical formatting across eight target models and two established benchmarks, and reports that only semantically transformed mathematical encodings achieve high attack success, while rule-based formatting performs similarly to unencoded baselines. It also introduce
2. Reason(s) to accept.
The paper addresses an important safety question and evaluates it systematically across multiple model families, two established benchmarks, and both baseline and ablation-style controls. The LLM-based versus rule-based comparison is a meaningful experimental design choice, and the introduction of Formal Logic as a new encoding family is a useful extension beyond prior set-theoretic attacks. The cross-model results are practically relevant and clearly reported.
3. Reason(s) to reject.
The paper is interesting, but the contribution is more limited than it first appears. It mainly extends earlier math-based jailbreak ideas with more encoding types and broader testing. The claim that semantic transformation is the main reason for success is plausible, but not fully proven because several factors change at once. In addition, the evaluation relies only on automated attack-success scores without human checking, and the defense discussion is only preliminary.
4. Detailed Review, comments, suggestions, typos
This paper studies an important safety problem and gives a useful comparison of math-based jailbreaks across several models and two benchmarks. A clear strength is the direct comparison between LLM-based semantic encodings and rule-based mathematical formatting. The results consistently show that helper-LLM-generated encodings are much more effective than shallow rule-based ones.

The evaluation has some important limitations. Attack success is measured only with an automated judge model, without human validation. For a safety paper, this is a meaningful weakness because binary ASR does not fully show whether outputs are truly actionable, complete, or only partial jailbreaks. In addition, the proposed defense is only discussed conceptually and is not implemented or tested, so it should be framed strictly as future work.

Overall, this is an empirical paper with good benchmark coverage and a clear main comparison, but the mechanism claims should be more cautious and the limitations should be stated more clearly. The paper would be stronger with a small human evaluation, tighter controls to isolate semantic transformation, a more careful defense discussion, and analysis by harm category.
5. Recommendation
Weak Accept -- Borderline paper. I'm leaning towards accepting.


Camera-ready Instructions
The camera-ready version of your paper is due by April 20th, 2026 (AoE). Please submit your camera-ready PDF and signed permission form through CMT.

Here are the instructions for preparing and submitting your camera-ready paper:

1. The camera-ready paper should follow the PMLR template

Long papers: Maximum 12 pages for the main content (including main text, acknowledgments, and references). An optional appendix* of up to 4 additional pages may be included. The appendix must append at the end of the camera-ready PDF (starting at page 13 and up to page 16) and should not be submitted as a separate file.
Short papers: Maximum 6 pages for the main content (including main text, acknowledgments, and references). An optional appendix* of up to 2 additional pages may be included. The appendix must append at the end of the camera-ready PDF (starting at page 7 and up to page 8) and should not be submitted as a separate file.
2. One important note. PMLR does not allow videos to be submitted as supplementary material.  If you have videos, code, datasets, and other supplementary materials, please host them on your own (e.g., YouTube, Github, etc). You should provide, in the main text of your paper, a link to this material, or a link to your project website.

3.  Please sign the Publication Agreement (already sent to the corresponding author). Please rename the PDF to <CAI26_paperId_Permission>.pdf

*Authors may optionally submit a technical appendix (PDF) containing additional supporting information such as proofs of theorems that are stated in the main paper; additional information needed to reproduce experiments; further experimental results; figures and examples to illustrate technical claims; etc. The main submission may reference the appendix, but should be self contained. If proofs or other supplementary matter are an important part of the contribution, their essential elements should be included in the main paper.