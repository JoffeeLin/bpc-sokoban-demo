# BPC v0.19: frozen end-to-end temporal gauge transfer

## Result

**ADOPTED for the bounded claim below.** The frozen non-neural BPC controller
now receives a spatially transformed, delayed observation and issues an action
that may execute only after a separate delay. Sensor and actuator interfaces
are simultaneously widened and anonymously permuted. Calibration contains
only observations, issued actuator slots, and next observations.

Sensor delay `s` and actuator delay `a` are observationally non-identifiable
separately: the transition visible at time `t` was caused by the issued action
at `t-(s+a)`. All decompositions with the same total lag `L=s+a` generate the
same observation sequence under the same initial state and issued actions.
v0.19 therefore claims and learns only `L`, not `s` or `a`.

Four interfaces, four independent calibration streams per interface, 48
holdout worlds, and two action seeds were frozen before execution. Training,
calibration, and holdout initial states were disjoint. Across 9,216 episodes
per condition:

| Frozen condition | Successes | Rate |
|---|---:|---:|
| Learned temporal + D4 gauge average | **8,552 / 9,216** | **92.8%** |
| Oracle channel, frame, and action binding | 8,532 / 9,216 | 92.6% |
| Maximum-probability single spatial gauge | 8,534 / 9,216 | 92.6% |
| Assume zero end-to-end lag | 1,182 / 9,216 | 12.8% |
| Align to history one step after the true lag | 1,145 / 9,216 | 12.4% |
| Fixed random channel/frame/action binding | 1,809 / 9,216 | 19.6% |

The 20-episode difference between temporal averaging and oracle is sampling
variation under separately routed but equivalently valid gauge probabilities;
it is not evidence that learned binding is better than the oracle.

Every interface passed separately:

| Physical delays `(sensor, actuator)` | Total lag | Temporal | Oracle | Zero lag | Shifted | Random |
|---:|---:|---:|---:|---:|---:|---:|
| `(0, 2)` | 2 | 2,133 | 2,136 | 404 | 303 | 752 |
| `(1, 1)` | 2 | 2,164 | 2,144 | 144 | 208 | 754 |
| `(0, 4)` | 4 | 2,125 | 2,118 | 380 | 380 | 303 |
| `(2, 2)` | 4 | 2,130 | 2,134 | 254 | 254 | 0 |

All four total lags and all 16 per-stream lags were exact. All **32/32**
learned temporal-spatial gauge/action pairs matched the evaluator-only physical
equivalence relation; all **128/128** per-stream pairs agreed. All 14
pre-registered gates passed. Evaluation made zero writes and preserved the
model digest.

## Mechanism

For each supplied total-lag candidate `L ∈ {0,1,2,3,4}`, v0.19:

1. aligns each observed transition with the issued action from `L` steps ago,
   respecting episode boundaries;
2. for every D4 transform, learns action-conditional raw transition
   probabilities for all one-to-one useful actuator injections;
3. marginalizes all D4/action hypotheses to obtain the probability evidence
   for `L` and selects the most probable total lag;
4. retains the best actuator injection separately in all eight observationally
   equivalent spatial gauges; and
5. averages their observed-slot action probabilities during direct control.

The zero-lag and one-step-shifted controls use exactly the same observations,
issued actions, candidate transforms, and probability family. Their large
drop isolates the causal importance of temporal alignment. No task, entity,
direction, formula, goal, or physical delay decomposition enters inference.

`classifier.dev` (`jev-1.13.0`) batch-routed 14 next-frontier proposals. It
ranked joint sensor/actuator latency highest at confidence `0.82`. Formal
analysis then narrowed the claim to the identifiable sum; the classifier is
absent from BPC training, binding, frozen evaluation, and runtime.

## Rejected claim

The experiment does **not** recover sensor latency and actuator latency
separately. A unit-level counterexample verifies that `(s,a)=(0,4)`, `(1,3)`,
`(2,2)`, `(3,1)`, and `(4,0)` produce identical observation traces when the
initial state and issued actions match. Reporting separate recovery would be
unsupported. The model also receives an experimenter-supplied finite lag
candidate family; it does not invent a temporal representation.

## Frozen evidence

- Protocol: [`protocol_v19_temporal.json`](protocol_v19_temporal.json)
- Holdout: [`holdout_v19.json`](holdout_v19.json)
- Frozen runner: [`experiment_v19_temporal_frozen.py`](experiment_v19_temporal_frozen.py)
- Core mechanism: [`bpc_temporal_interface_v19.py`](bpc_temporal_interface_v19.py)
- Result: [`artifacts/v19temporal/result.json`](artifacts/v19temporal/result.json)
- Video: [12 frozen delayed-control traces](https://github.com/JoffeeLin/bpc-sokoban-demo/releases/download/v19.0.0/bpc_temporal_gauge_v19_12_unseen_worlds.mp4)
- Release: [v19.0.0](https://github.com/JoffeeLin/bpc-sokoban-demo/releases/tag/v19.0.0)
- Result SHA-256: `7bdc7143cf92d7d9808250b69a15f42668b90fe31f9f89b80f7575ff1e44f7a1`
- Protocol SHA-256: `a619b1a723fa15ee97fe3ddfb7b1e24708bc28a82c9363cb4fa4565c1fd5a257`
- Holdout SHA-256: `6c9c1826b9bfe5f545fbab3e7b22fb32041915596926fb386d6076ffa93f02b4`
- Video SHA-256: `e34fc3210534852c4d096595bf3b8df8a7c7a7acc6b53cbfd7e9a6c0c7ae564f`
- Poster SHA-256: `7984271d582371b96be9e1f3b2122d046db47083986f4c503fe6227317fadc35`

## Boundary

This is developer-frozen held-out synthetic evidence, not a third-party blind
result. Lag candidates `0–4`, canonical semantics, six raw planes, four
actions, maximum 7×7 canvas, D4 family, nuisance formulas, structural
statistics, calibration schedules, generators, terminal events, and direct
policy remain supplied. This does not establish arbitrary temporal reasoning,
long-horizon memory, latent-state inference, autonomous representation
invention, open-world grounding, or AGI.
