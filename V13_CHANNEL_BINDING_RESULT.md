# BPC v0.13: frozen anonymous sensor-interface binding

## Result

**ADOPTED for the bounded claim below.** A frozen non-neural BPC controller was
trained only on the canonical six-plane sensor order. At deployment, a separate
probability binder observed unlabeled random transitions from a permuted sensor
interface. It inferred the canonical-to-observed assignment, canonicalized the
incoming bits, and passed them to the unchanged v0.12 direct policy.

The frozen test used four channel derangements never used in development. Three
target calibration streams changed the family mixture to `70/15/15`; the fourth
was balanced. Training, reference calibration, target calibration, and 48
holdout initial worlds were mutually disjoint. Across four interfaces, two new
action seeds, and a 64-step budget:

| Frozen condition | Joint successes | Rate |
|---|---:|---:|
| Learned transition-probability binding | **1,884 / 2,304** | **81.8%** |
| Oracle inverse permutation | **1,884 / 2,304** | **81.8%** |
| Static occupancy + spatial likelihood | 1,529 / 2,304 | 66.4% |
| Occupancy-count likelihood only | 1,489 / 2,304 | 64.6% |
| Fixed random bindings | 369 / 2,304 | 16.0% |
| Identity / no binding | 288 / 2,304 | 12.5% |

The learned binder recovered all four exact six-channel assignments. It matched
the oracle condition for every interface, action seed, task family, and total.
Evaluation made zero model writes, and all 12 pre-registered gates passed.

## Mechanism

For each anonymous raw plane, the binder stores Dirichlet/Beta counts for bit
occupancy, signed population change, changed-cell count, and pairwise co-change.
It evaluates all `6! = 720` one-to-one assignments under equal priors and selects
the maximum posterior assignment. No entity names, task labels, success signals,
policy rewards, neural network, or search enter this binding step.

The strongest frozen mechanism result is not “more features help.” The full
variant, which also included absolute spatial occupancy, failed one open-heavy
interface while the transition-only binder remained exact. Static and count-only
controls each failed two shifted interfaces. This isolates temporal co-change as
necessary for the tested distribution shifts.

`classifier.dev` routed candidate next experiments during development and
favored sensor rebinding over merely enlarging maps or adding hard-coded factors.
It is absent from calibration inference, BPC training, evaluation, and runtime.

## Frozen evidence

- Protocol: [`protocol_v13_channel_binding.json`](protocol_v13_channel_binding.json)
- Holdout: [`holdout_v13.json`](holdout_v13.json)
- Runner: [`experiment_v13_channel_binding_frozen.py`](experiment_v13_channel_binding_frozen.py)
- Result: [`artifacts/v13binding/result.json`](artifacts/v13binding/result.json)
- Result SHA-256: `f0cdffb8c6e7908d0bf4904222f50112806092094dba97e9e3e0da672d5e1501`
- Protocol SHA-256: `b5c473d702c53b4ea985fe32d27f2894ed44716a1cd8502129724d05cf059f59`
- Holdout SHA-256: `165bb72e5f8151e5d0c907f4da4aac18c0e9392a8db2b8aa3d005e966f3a9eb2`
- Video SHA-256: `a01f611d7e18aeef52a88dfd05f48b7cbc697bdbaa456ee347ce73d5680a738f`
- GitHub release: <https://github.com/JoffeeLin/bpc-sokoban-demo/releases/tag/v13.0.0>
- X video post: <https://x.com/JoffeeLin/status/2101735002530808037>

## Boundary

This supports sensor-order transfer within one supplied six-plane interface and
one synthetic environment family. The channel count, reference sampler, target
mixture schedules, interaction budget, probability families, generators,
terminal events, and canonical policy remain supplied. It does not establish
arbitrary sensor grounding, autonomous task discovery, language understanding,
or AGI.
