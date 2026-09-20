# BPC v0.14: frozen joint sensor and actuator binding

## Result

**ADOPTED for the bounded claim below.** The frozen non-neural BPC controller
was trained only with the canonical six-plane sensor order and four canonical
action slots. At deployment, two probability binders observed unlabeled random
transitions from a simultaneously permuted sensor and actuator interface. They
recovered both inverse assignments before the unchanged v0.12 direct policy
acted.

The frozen test used four sensor derangements and four actuator derangements
that were absent from development. Three target calibration streams changed the
mechanism mixture to `70/15/15`; the fourth was balanced. Training, reference
calibration, target calibration, and 48 holdout initial worlds were mutually
disjoint. Across four interfaces, two new action seeds, and a 64-step budget:

| Frozen condition | Joint successes | Rate |
|---|---:|---:|
| Learned sensor + actuator binding | **1,509 / 2,304** | **65.5%** |
| Oracle inverse permutations | **1,509 / 2,304** | **65.5%** |
| Learned sensor, identity actuator | 79 / 2,304 | 3.4% |
| Identity sensor, learned actuator | 297 / 2,304 | 12.9% |
| Identity / no binding | 222 / 2,304 | 9.6% |
| Fixed random sensor + actuator bindings | 144 / 2,304 | 6.2% |

The learned binders recovered all four exact six-channel assignments and all
four exact four-action assignments. They matched the oracle for every
interface, evaluation seed, task family, and total. Evaluation made zero model
writes, and all 13 pre-registered gates passed.

## Mechanism

The sensor binder is unchanged from v0.13: equal-prior assignment likelihoods
over anonymous plane occupancy, signed population change, changed-cell count,
and pairwise co-change recover a canonical-to-observed channel permutation.

After canonicalizing those planes, the new actuator binder stores
action-conditional categorical counts for per-plane signed population change,
flip count, local lost-bit-to-gained-bit displacement, and total raw change. It
evaluates all `4! = 24` one-to-one action assignments under equal priors. The
chosen mapping only translates the unchanged policy's four probability outputs
to the anonymous actuator slots. No direction names, entity names, task labels,
success signals, rewards, neural network, planner, search, or evaluation
learning enter either binding step.

The causal controls show that neither half is decorative. Removing only the
actuator binding reduced joint success from 65.5% to 3.4%; removing only the
sensor binding reduced it to 12.9%. Identity and fixed-random bindings reached
9.6% and 6.2%. Thus the frozen result supports simultaneous input/output
interface transfer within this supplied synthetic interface family.

`classifier.dev` routed candidate mechanisms during development and favored
generic action-conditional bit-displacement statistics plus sequential sensor
then actuator inference. It is absent from both binders, BPC policy training,
frozen evaluation, and runtime.

## Frozen evidence

- Protocol: [`protocol_v14_joint_binding.json`](protocol_v14_joint_binding.json)
- Holdout: [`holdout_v14.json`](holdout_v14.json)
- Runner: [`experiment_v14_joint_binding_frozen.py`](experiment_v14_joint_binding_frozen.py)
- Result: [`artifacts/v14joint/result.json`](artifacts/v14joint/result.json)
- Result SHA-256: `09969b204af9a7b005b2fd7b06d63cceea59a3e9619c46bcc80f45b62b9d88b2`
- Protocol SHA-256: `a34dbe7fbb045e7fc7853287319371e29c5f1978de57381799403ada9b4dc424`
- Holdout SHA-256: `d9c54f64a4c208915bd0fb9d88fd1d09aebdb2973c9103d0ef40926da90ef896`
- Video SHA-256: `d086d3c422fdb45121b420f8ddc0efd6017a65833e731ec9e0ac1fb84ee8c5c7`
- GitHub release: <https://github.com/JoffeeLin/bpc-sokoban-demo/releases/tag/v14.0.0>

## Boundary

This is developer-frozen held-out synthetic bidirectional-interface transfer,
not a third-party blind result. Sensor/action cardinalities, coordinate grid,
calibration samplers, mixture schedules, interaction budget, likelihood
families, generators, terminal events, and the canonical policy remain
supplied. It does not establish arbitrary sensorimotor grounding, autonomous
operator invention, open-world transfer, or AGI.
