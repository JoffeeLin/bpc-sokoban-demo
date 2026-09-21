# Jev and recent Jev-like models: mechanism audit

Date: 2026-09-21. This audit separates published facts, direct source evidence,
and inference. It was performed to inform the Pure BPC AGI line, not to import a
neural model into BPC.

## Bottom line

Jev is a closed, text-input decision model. TypeSafe publicly states that it has
a new architecture, parallel sampler, and Reinforcement Learning for Calibrated
Decisions (RLCD), but does not publish weights, layer structure, source code, or
a reproducible training recipe. Therefore no public repository currently
reproduces Jev's architecture. Most “Jev-like” repositories reproduce the API
shape by reading candidate-token logits from an ordinary language model.

The one materially different open family is Laya: a bidirectional transformer
encoder plus option-marker decision head, trained for probability decisions and
then temperature-calibrated. It is closer to Jev's *task shape*, but is still an
independent neural design and not evidence about Jev's proprietary internals.

## What the official sources actually establish

- Input is text state plus independent typed questions; outputs are Choice,
  Score, or Noul probabilities, evaluated in parallel without text generation.
- Jev 1.13.0 is advertised with a 64k request context, a 32k state-plus-longest-
  question limit, and versioned model IDs.
- RLCD is described as optimizing calibrated decisions rather than generated
  prose. The public explanation does not disclose its loss, data, architecture,
  optimizer, or ablations.
- Official “jaggedness” documentation says Jev is literal, weak at counting,
  numeric precision, indirection, long irrelevant state, adversarial content,
  and structural identities across separately phrased questions. It is a fast
  bounded judgment model, not a demonstrated long-horizon general intelligence
  architecture.

Primary sources:

- [TypeSafe launch post](https://typesafe.ai/blog/introducing-system-one-models-and-jev)
- [AI primer and RLCD claim](https://docs.typesafe.ai/introduction/machine-learning-primer.md)
- [Jev 1.13 model card](https://docs.typesafe.ai/models.md)
- [Known failure modes](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md)
- [Confidence definition](https://docs.typesafe.ai/confidence.md)

## Public implementation families

| Project and inspected revision | Directly implemented mechanism | Classification |
|---|---|---|
| [SemIf](https://github.com/TheoLeeCJ/SemIf) `ca3ba65f` | Frozen Qwen3.5-4B; one forward pass; softmax over fixed answer-token logits; shared-state KV prefix branching | LM logit readout |
| [mini-jev](https://github.com/r-ms/mini-jev) `ca612198` | Frozen Qwen3-4B; reads letter logits and compares with constrained/JSON generation | LM logit readout |
| [open-alternative-jev](https://github.com/ikermoel/open-alternative-jev) `7456d370` | Hugging Face/vLLM causal model; candidate logits at marked positions; optional held-out temperature scaling | LM logit readout |
| [LitJev](https://github.com/zhengxuyu/litjev) `a54936ed` | Shared state prefill, cached question branches, Qwen vocabulary-head code logits; JSON built in Python | LM logit readout |
| [system-one](https://github.com/sgoedecke/system-one) `ebde2a2d` | Chat template ending in `choice_index:`; constrained next-token candidate measurement | LM logit readout |
| [Laya](https://github.com/NandhaKishorM/laya) `42626c34` | ModernBERT encoder, question-type embedding, marker-position option states, transformer head, scalar option scorer; proper-rule/policy-gradient/CE training; temperature calibration | Trained neural decision model |
| [system-one-open](https://github.com/mithalouni/system-one-open) `77f1f7cc` | Gemma backbone; option-letter LM-head rows; full/LoRA training with CE+Brier; held-out temperature fitting | Trained neural decision model |
| [djev-spark](https://github.com/mmastrac/djev-spark) `1444f3e9` | DiffusionGemma serving/container recipe and Jev-compatible structured endpoint | Serving/integration evidence |
| [JevBench](https://github.com/fstandhartinger/jevbench) `fd51755e` | Frozen comparative benchmark of capability, calibration, latency and cost | Benchmark only |
| [classifier.dev](https://github.com/mrmps/classifier-dev) `a68b524f` | Batches classification items into Jev calls; confidence routing and fallbacks | Integration only |

classifier.dev `jev-1.13.0` independently classified the same taxonomy: SemIf,
mini-jev, open-alternative-jev, LitJev and system-one as LM-logit interface
clones; Laya and system-one-open as specialized trained neural decision models;
the remaining tools as benchmark/integration projects. This classification was
used only as research triage and was checked against source.

## Shared engineering pattern

The ecosystem converges on a practical pattern:

1. encode a shared state once;
2. represent each question as a bounded candidate set;
3. measure all candidate states/logits without autoregressive answer generation;
4. normalize into a distribution;
5. fit calibration only on separate labelled data;
6. expose the whole distribution and let external code decide thresholds;
7. pin model, prompt, candidate ordering and revision because each changes the
   distribution.

This explains the speed and type safety of many clones without implying a new
general-intelligence mechanism. SemIf explicitly warns that its softmax values
are conditional candidate scores, not calibrated correctness probabilities.
LitJev and mini-jev make the same boundary explicit. Laya shows that real
calibration needs task-specific training and held-out temperature fitting.

## What transfers to Pure BPC

Only the task-independent measurement discipline transfers:

- one unchanged reality state feeds all anonymous action alternatives;
- every alternative returns a probability distribution directly;
- no free-text or sequential output decoder is needed;
- probability quality is tested with held-out Brier/calibration evidence;
- consistent action renaming must only permute outputs;
- model/protocol revisions, raw inputs and controls are frozen and hashed.

The following do **not** transfer: pretrained language encoders, attention
heads, option text, semantic questions, reward/policy-gradient training,
workflow decomposition, candidate descriptions, or code-written chains of
judgments. They are neural or researcher-designed cognitive structure and
violate the supplied Pure BPC theory and project constraints.

## Consequence for v0.41

The v0.41 pure medium remains a world-prediction experiment. Its four action
channels now occupy exchangeable equal physical regions and can be queried in
parallel from one state. It reports Beta probabilities and Brier residuals,
tests action-removal and rotated-action controls, and adds an exact action-
renaming equivariance test. Nothing in Jev justifies adding a semantic decision
head, reward, planner, or neural network to BPC.
