# BPC v0.15: frozen open-interface subset binding

## Result

**ADOPTED for the bounded claim below.** The frozen non-neural BPC controller
was trained with six canonical sensor planes and four canonical action slots.
At deployment it received eight anonymous sensor planes and six anonymous
actuator slots. Two extra sensor planes were deterministic state-keyed random
nuisances; two extra actuator slots had permanent zero effect. From unlabeled
random transitions, probability binders selected and ordered the canonical
`6 × 4` sub-interface before the unchanged v0.12 direct policy acted.

The frozen test used four eight-channel/six-slot interfaces absent from
development. Three target calibration streams changed the mechanism mixture to
`70/15/15`; the fourth was balanced. Training, reference calibration, target
calibration, and 48 holdout initial worlds were mutually disjoint. Across four
interfaces, two new action seeds, and a 64-step budget:

| Frozen condition | Joint successes | Rate |
|---|---:|---:|
| Learned sensor + actuator subsets | **1,651 / 2,304** | **71.7%** |
| Oracle canonical subsets | **1,651 / 2,304** | **71.7%** |
| Learned sensor subset, first four actuators | 3 / 2,304 | 0.1% |
| First six sensors, learned actuator subset | 282 / 2,304 | 12.2% |
| First six sensors / first four actuators | 103 / 2,304 | 4.5% |
| Fixed random six-of-eight / four-of-six subsets | 179 / 2,304 | 7.8% |

The learned binders recovered all four exact six-of-eight sensor assignments
and all four exact four-of-six actuator assignments. They rejected all eight
permanent zero-effect actuator slots and matched the oracle for every interface,
evaluation seed, task family, and total. Evaluation made zero model writes, and
all 14 pre-registered gates passed.

## Mechanism

The sensor binder evaluates all `8P6 = 20,160` canonical-to-observed injections
under equal priors. Its unlabeled probability evidence includes occupancy,
change-conditioned signed population deltas and flip counts, local
lost-bit-to-gained-bit displacement, conditional pairwise co-change, and joint
signed deltas. The actuator binder first retains the four slots with the highest
empirical probability of any raw change, then evaluates their `4! = 24`
one-to-one assignments using action-conditional raw transition probabilities.

The chosen mappings only canonicalize the policy input and route its four
probability outputs to the selected actuator slots. No direction names, entity
names, task labels, success signals, rewards, neural network, planner, search,
or evaluation learning enter binding.

The causal controls show that both subset decisions matter. Removing only the
actuator subset reduced joint success from 71.7% to 0.1%; removing only the
sensor subset reduced it to 12.2%. Fixed first-slot and random-subset controls
reached 4.5% and 7.8%.

`classifier.dev` (`jev-1.13.0`) routed 14 proposed next steps and labelled this
open-interface experiment “high value next frozen experiment” with confidence
`0.93`. It is absent from interface inference, policy training, frozen
evaluation, and runtime.

## Retained negative result

An earlier development attempt used distractor planes composed from displaced
canonical mechanisms. Marginal, conditional, and action-conditioned local
statistics still selected a composite distractor under mechanism-mixture shift.
That rejected pre-freeze protocol and its unexecuted holdout are retained under
[`artifacts/v15open/rejected_freeze_attempt1`](artifacts/v15open/rejected_freeze_attempt1).
The positive v0.15 claim is limited to state-keyed random nuisance planes; it
does **not** establish rejection of causally entangled composite sensors.

## Frozen evidence

- Protocol: [`protocol_v15_open_interface.json`](protocol_v15_open_interface.json)
- Holdout: [`holdout_v15.json`](holdout_v15.json)
- Runner: [`experiment_v15_open_interface_frozen.py`](experiment_v15_open_interface_frozen.py)
- Result: [`artifacts/v15open/result.json`](artifacts/v15open/result.json)
- Result SHA-256: `11c17bc51ca4250bae31fca4c74f2c8370148d1cc3dbb209263c9b8365d89257`
- Protocol SHA-256: `25a94071fb99093eb0812c759cfb2f348d5f7a6bf601bd9f06f342ee7aa49901`
- Holdout SHA-256: `129b686432bb7d68afc101a74ae0447aba2966b5e4789ae7c4ace2f08140874e`
- Video SHA-256: `8fa181e93cbd78f6c02ab5930fa8f2e83b22974acc5585edcd2048d248600550`
- GitHub release: <https://github.com/JoffeeLin/bpc-sokoban-demo/releases/tag/v15.0.0>

## Boundary

This is developer-frozen held-out synthetic open-interface transfer, not a
third-party blind result. Canonical and observed cardinalities, state-keyed
random nuisance synthesis, permanent-null actuator mechanism, coordinate grid,
calibration samplers, mixture schedules, interaction budget, likelihood
families, generators, terminal events, and the canonical policy remain
supplied. It does not establish causally entangled distractor rejection,
arbitrary sensorimotor grounding, autonomous operator invention, open-world
transfer, or AGI.
