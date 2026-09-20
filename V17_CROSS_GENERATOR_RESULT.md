# BPC v0.17: frozen cross-generator variable-interface transfer

## Result

**ADOPTED for the bounded claim below.** The non-neural BPC controller was
trained only on the original square-map generator. Frozen deployment used a
separately implemented rectangular-map sampler, state encoder, transition
function, shortest-path verifier, and causal-necessity checks. At the same
time, deployment widened the anonymous interface from the canonical `6 × 4`
schema to 9–12 sensor planes and 5–8 actuator slots.

The extra sensors used composite formula families `3/4/5`, held out after
development used only `0/1/2`. Extra actuators were not null: they changed
extra sensor planes while leaving the canonical world state unchanged. The
binder received only unlabeled transitions and the frozen direct policy did
not adapt during evaluation.

Four interfaces, four calibration streams per interface, 48 holdout worlds,
and two action seeds were frozen before holdout execution. Training,
calibration, and holdout initial states were disjoint. On 2,304 joint episodes:

| Frozen condition | Joint successes | Rate |
|---|---:|---:|
| Learned sensor + action binding | **1,879 / 2,304** | **81.6%** |
| Oracle binding | **1,879 / 2,304** | **81.6%** |
| Learned sensors, first four actions | 83 / 2,304 | 3.6% |
| First six sensors, learned actions | 780 / 2,304 | 33.9% |
| First-slot identity binding | 227 / 2,304 | 9.9% |
| Fixed random binding | 309 / 2,304 | 13.4% |

All four sensor mappings and all four actuator mappings were exact. Every one
of the 16 independently sampled calibration streams selected the oracle sensor
basis. Learned and oracle results matched for every interface, evaluation seed,
task family, and total. Evaluation made zero model writes, and all 16
pre-registered gates passed.

## Mechanism

v0.17 uses a two-stage structural filter before probability selection:

1. Project each target transition's anonymous change set through a candidate
   mapping and require the complete reference change alphabet to be preserved.
2. For every anonymous plane pair, learn both conditional event alphabets
   `P(B | A=1)` and `P(A | B=1)`. Require both supports to be preserved. The
   shifting all-zero base rate is omitted.

This reduced the four frozen assignment spaces as follows:

| Observed sensors | Initial assignments | Change support | Relation support |
|---:|---:|---:|---:|
| 9 | 60,480 | 16 | 4 |
| 10 | 151,200 | 8 | 4 |
| 11 | 332,640 | 24 | 4 |
| 12 | 665,280 | 24 | 4 |

Marginal, transition, and bidirectional conditional probabilities across four
unlabeled regimes selected the oracle from the four remaining bases. Combined
sensor log margins ranged from `10,216.1` to `12,204.4`; the weakest individual
stream margin was `1,060.7`. Action-conditional probabilities independently
selected the useful actuator slots with margins from `28,742.4` to `45,566.1`.

No entity, task, direction, formula, or generator name enters these inference
functions. They use no neural network, reward, scalar task score, planner,
search, language rule, manual label, or evaluation-time learning.

`classifier.dev` (`jev-1.13.0`) routed 16 development proposals. It selected
cross-generator transfer as the strongest proposal with confidence `0.73` and
held-out distractor-family transfer second with `0.66`. The classifier is
absent from model training, binding, frozen evaluation, and runtime.

## Retained failures

The successful result does not replace the failed development history:

- one-way change-support inclusion admitted a constant composite plane and
  produced a wrong 9-channel binding;
- complete change support passed development but left an exact zero-margin tie
  on the first held-out formula interface;
- raw same-cell joint frequency broke that tie but failed independent-stream
  invariance under a collect-heavy mixture;
- conditional co-presence probability recovered the mapping, but the first
  frozen protocol exceeded its pre-registered compatible-count ceiling and was
  not executed on holdout;
- relation-support filtering was then developed, and the final protocol used
  entirely new `173xxx` calibration/evaluation seeds, interfaces, and holdout.

The raw records and the unexecuted earlier protocol are retained under
[`artifacts/v17crossgen`](artifacts/v17crossgen).

## Frozen evidence

- Protocol: [`protocol_v17_cross_generator.json`](protocol_v17_cross_generator.json)
- Holdout: [`holdout_v17.json`](holdout_v17.json)
- Frozen runner: [`experiment_v17_cross_generator_frozen.py`](experiment_v17_cross_generator_frozen.py)
- Core mechanism: [`bpc_cross_generator_v17.py`](bpc_cross_generator_v17.py)
- Result: [`artifacts/v17crossgen/result.json`](artifacts/v17crossgen/result.json)
- Result SHA-256: `50c29661e79fa4283a350404719b847d90293131eeffbd1dd9f84f9ce561cacc`
- Protocol SHA-256: `f74ea144b096c35f338fedb2425ebeff526e9e6f9d2e6dce1968de621a2fd95d`
- Holdout SHA-256: `b9667d9b97129b18f0a116ae23efe9ae2d70b96a72c438d7b247019f9ec6285f`
- Video SHA-256: `f9408380e62847899cec925a5dee16a3675bd80fa46a94bd1197dae5a758d222`
- GitHub release: <https://github.com/JoffeeLin/bpc-sokoban-demo/releases/tag/v17.0.0>

## Boundary

This is developer-frozen held-out synthetic evidence, not a third-party blind
result. Canonical semantics, six raw planes, four canonical actions, maximum
7×7 canvas, distractor-family code, structural filters, probability families,
calibration schedules, both generators, terminal events, and the direct policy
remain supplied. The second implementation changes map-shape distribution and
code path but intentionally preserves the same task ontology. This does not
establish transfer to arbitrary simulators, autonomous representation invention,
open-world grounding, or AGI.
