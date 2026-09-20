# BPC v0.12: frozen three-factor direct recombination

## Result

**ADOPTED for the bounded claim below.** One non-neural BPC learner received
successful raw trajectories from three separate experience streams, without
task-family names. Terminal raw co-change exposed three anonymous factors. A
single additive evidence query then activated and recombined them on unseen
worlds that require opening a gate, pushing a box, and reaching a target.

The frozen holdout contains 48 new initial worlds—12 each for the three single
mechanisms and 12 joint worlds—with zero overlap against all 4,800 training
initial worlds. Each joint world was verified solvable normally and unsolvable
when either object movement or gate opening was disabled. Across two new action
seeds and a 64-step budget:

| Frozen joint condition | Successes | Rate |
|---|---:|---:|
| One additive BPC evidence field | **574 / 768** | **74.7%** |
| Explicit product, same learned factors | **574 / 768** | **74.7%** |
| One shared mixed-experience cube | 437 / 768 | 56.9% |
| Delete anonymous factor 0 | 474 / 768 | 61.7% |
| Delete anonymous factor 1 | 297 / 768 | 38.7% |
| Delete anonymous factor 2 | 487 / 768 | 63.4% |
| Uniform random actions | 139 / 768 | 18.1% |
| Rotate learned action meanings | 6 / 768 | 0.8% |

At 256 steps, the field completed 708/768 joint episodes. Evaluation made zero
model writes, and all 13 pre-registered gates passed.

## Mechanism

The learner discovered terminal raw co-change signatures `(1,2)`, `(1,3)`, and
`(1,4,5)`. Plane `1` was common to all terminal events and removed. The
remaining raw-plane requirements are therefore `(2)`, `(3)`, and `(4,5)`.
Single-mechanism worlds activate one factor; every joint initial state activates
all three. No task name is available to the learner or direct policy.

Each factor retains its own probability cube. Runtime inference adds their
relation log evidence and uses one pooled learned action prior, followed by one
four-action normalization. It performs no planning, search, value iteration, or
neural inference. The explicit product control has the same learned information
and matched the field exactly at the primary budget.

`classifier.dev` was used only to route candidate mechanisms and candidate
metrics during development. Low-confidence classifications were reviewed
manually. It is absent from training, inference, and frozen evaluation.

## Frozen evidence

- Protocol: [`protocol_v12_three_factor.json`](protocol_v12_three_factor.json)
- Holdout: [`holdout_v12.json`](holdout_v12.json)
- Runner: [`experiment_v12_three_factor_frozen.py`](experiment_v12_three_factor_frozen.py)
- Result: [`artifacts/v12three/result.json`](artifacts/v12three/result.json)
- Result SHA-256: `555a032676b20abfea420109eb32cfa8c4d1dad5baae0f006704be7001e56f60`
- Protocol SHA-256: `96d1e8e46b05096e9ff0e68629da5cb181e95bdb36e90c28b6eac2cda3457ec0`
- Holdout SHA-256: `cc970e8dab94b0b2fe2ff98a7a17bda5b3a4e1292e9a5cd13ab5262204adf6d2`
- Video SHA-256: `33c506d95ce1a7e53c54c2f671cc94904b3d6d27a1e568f728d9b8cc593ad183`
- GitHub release: <https://github.com/JoffeeLin/bpc-sokoban-demo/releases/tag/v12.0.0>
- X video and result thread: <https://x.com/JoffeeLin/status/2101727094967603654>

## Boundary

This supports direct recombination of three learned anonymous factors on a
bounded synthetic holdout without joint-task training. Raw channelization,
generators, binary terminal success events, the additive evidence rule, and
evaluation limits remain supplied. It does not show autonomous operator
invention, arbitrary Sokoban solving, language grounding, or AGI.
