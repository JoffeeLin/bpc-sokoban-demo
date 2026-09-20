# BPC v0.16: frozen composite-interface binding

## Result

**ADOPTED for the bounded claim below.** v0.16 resolves the composite-sensor
failure retained by v0.15. The frozen non-neural controller received eight
anonymous sensor planes containing its six canonical planes plus two
displaced-XOR composites, together with six anonymous actuator slots containing
four canonical actions and two permanent-null slots. It inferred the interface
from unlabeled transitions before the unchanged direct policy acted.

Four composite interfaces, four separately sampled calibration regimes per
interface, 48 holdout worlds, and two action seeds were frozen before holdout
execution. Training, reference calibration, target calibration, and holdout
initial states were mutually disjoint. On the 2,304 joint episodes:

| Frozen condition | Joint successes | Rate |
|---|---:|---:|
| Learned sensor + actuator binding | **1,844 / 2,304** | **80.0%** |
| Oracle binding | **1,844 / 2,304** | **80.0%** |
| Learned sensors, first four actuators | 169 / 2,304 | 7.3% |
| First six sensors, learned actuators | 435 / 2,304 | 18.9% |
| First-slot identity binding | 161 / 2,304 | 7.0% |
| Fixed random binding | 125 / 2,304 | 5.4% |

All four exact sensor mappings and all four exact actuator mappings were
recovered. Every one of the 16 independently sampled sensor streams selected
the oracle basis, every permanent-null action slot was rejected, learned and
oracle results matched for every interface, seed, family, and total, and
evaluation made zero model writes. All 16 pre-registered gates passed.

## Mechanism

The new step is empirical transition-support invariance. For every proposed
canonical-to-observed sensor assignment, v0.16 projects the sets of planes that
change together. A proposal is retained only when every projected target
change signature occurs in the reference interface. This reduces each
`8P6 = 20,160` assignment space to four compatible bases without task labels,
success signals, or direction names.

Support alone leaves a four-way ambiguity. v0.16 therefore sums transition log
probabilities across four independently sampled unlabeled regimes. The same
oracle basis won in each stream separately and jointly. The pre-frozen combined
log margins ranged from `18,420.6` to `19,923.5`; the weakest individual-stream
margin was `1,707.7`. Action-conditional transition probabilities independently
recovered the four useful actuator slots and their order, with margins from
`63,546.7` to `65,345.4`.

The selected mappings only canonicalize sensor input and route the policy's
probability outputs. There is no neural network, task-family input, reward,
scalar task score, planner, search, language rule, manual label, or evaluation
learning in the binding mechanism.

`classifier.dev` (`jev-1.13.0`) routed 16 development proposals and selected
the multi-regime support-plus-probability route as the strongest candidate with
confidence `0.78`. It is absent from inference, training, frozen evaluation,
and runtime.

## Relation to the retained failure

v0.15 explicitly retained a failed attempt in which marginal, conditional, and
action-conditioned local statistics selected a displaced-XOR distractor under
mechanism-mixture shift. v0.16 does not erase that result: it changes the
mechanism, freezes new interfaces and worlds, and evaluates once. The earlier
failure remains under
[`artifacts/v15open/rejected_freeze_attempt1`](artifacts/v15open/rejected_freeze_attempt1).

## Frozen evidence

- Protocol: [`protocol_v16_composite.json`](protocol_v16_composite.json)
- Holdout: [`holdout_v16.json`](holdout_v16.json)
- Frozen runner: [`experiment_v16_composite_frozen.py`](experiment_v16_composite_frozen.py)
- Core mechanism: [`bpc_composite_binding_v16.py`](bpc_composite_binding_v16.py)
- Result: [`artifacts/v16composite/result.json`](artifacts/v16composite/result.json)
- Result SHA-256: `60a328f4b95c02ef5e1f459beabbb61981b31c0fbe25ae0c601380003c1d0638`
- Protocol SHA-256: `221dae0a8d5804a3f6b0112f1f9cab477aea5ebd02653c1d797fa7ec63669bb1`
- Holdout SHA-256: `84d976fc6e438236e4d0d8e15796dd8e3ff619a1eba5c2057872b2818c44a268`
- Video SHA-256: `908e4689c3d0214e903c489aa78693a0b84a296bbe3b4bfee534e6ffabe15888`
- GitHub release: <https://github.com/JoffeeLin/bpc-sokoban-demo/releases/tag/v16.0.0>

## Boundary

This is developer-frozen held-out synthetic evidence, not a third-party blind
result. The canonical/observed cardinalities, displaced-XOR distractor formula,
four calibration-regime schedules, transition-support rule, likelihood family,
coordinate grid, generators, terminal events, interaction budget, and canonical
policy remain supplied. It does not establish rejection of arbitrary causal
distractors, autonomous sensorimotor grounding, open-world transfer, or AGI.
