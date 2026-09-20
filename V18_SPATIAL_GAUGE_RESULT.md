# BPC v0.18: frozen spatial gauge-class transfer

## Result

**ADOPTED for the bounded claim below.** The frozen non-neural BPC controller
was trained only on its canonical square-frame interface. Deployment used an
independent rectangular-map generator while changing four things together:
sensor-plane placement, actuator-slot placement, nuisance formulas, and a full
D4 rotation/reflection of the observed field.

Absolute orientation is not identifiable here. If actuator slots are anonymous,
every spatial transform can be exactly compensated by a corresponding action
permutation. v0.18 therefore learns the best actuator injection separately in
all eight D4 gauges from unlabeled transitions, queries the same frozen BPC
field in each paired gauge, maps every probability back to observed actuator
slots, and averages the eight distributions. It never selects a gauge using
task success.

Four interfaces, four calibration streams per interface, 48 holdout worlds,
and two action seeds were frozen before execution. Training, calibration, and
holdout initial states were disjoint. Across 9,216 episodes per condition:

| Frozen condition | Successes | Rate |
|---|---:|---:|
| Learned eight-gauge probability average | **8,339 / 9,216** | **90.5%** |
| Oracle sensor, spatial, and action binding | 8,367 / 9,216 | 90.8% |
| Maximum-likelihood single gauge | 8,243 / 9,216 | 89.4% |
| Cyclically mismatched gauge-action pairs | 5,253 / 9,216 | 57.0% |
| Learned channels/actions, no spatial restoration | 4,170 / 9,216 | 45.2% |
| Fixed random channel/frame/action binding | 900 / 9,216 | 9.8% |

Every interface passed separately:

| Interface | Gauge average | Oracle | Shuffled pairs | No spatial | Random |
|---:|---:|---:|---:|---:|---:|
| 1 | 2,076 | 2,093 | 1,350 | 1,282 | 467 |
| 2 | 2,093 | 2,079 | 1,354 | 940 | 164 |
| 3 | 2,094 | 2,102 | 1,271 | 1,382 | 91 |
| 4 | 2,076 | 2,093 | 1,278 | 566 | 178 |

All four sensor mappings and all useful actuator-slot sets were recovered.
All **32/32** learned gauge-action pairs matched the evaluator-only physical
equivalence relation, and all **128/128** mappings learned from individual
calibration streams agreed. All 12 pre-registered gates passed. Evaluation
made zero writes and preserved the model digest.

## Mechanism

For every candidate D4 transform `g`, v0.18:

1. canonicalizes the six useful planes selected by v0.17's anonymous relation
   binder;
2. applies the inverse of `g` to the entire 7×7 field;
3. learns `P(raw transition | canonical action → observed actuator slot)` for
   every one-to-one four-action injection;
4. retains the maximum-probability injection inside that gauge; and
5. at direct-control time, averages the eight observed-slot probability
   distributions with equal prior weight.

The shuffled-pair control contains exactly the same eight transforms and eight
learned action mappings, but cyclically assigns each mapping to the wrong
transform. Its large drop from 8,339 to 5,253 isolates the causal importance of
the learned pairing rather than the component inventory. No entity, task,
direction, formula, or generator name enters the inference functions.

`classifier.dev` (`jev-1.13.0`) batch-routed 12 proposed validation controls.
It was used only to identify potentially missing controls. High-confidence
rejections included selecting a transform by held-out success, regenerating a
holdout after seeing a control, using classifier confidence as an action
probability, and claiming absolute-transform recovery. It is absent from BPC
training, binding, frozen evaluation, and runtime.

## Retained failures

The adopted result does not replace the failed development history:

- maximum joint likelihood selected the wrong absolute D4 number on two of
  three development interfaces, although all selected frame/action pairs were
  behaviorally gauge-equivalent;
- adding absolute per-cell occupancy priors failed 0/3 because square-to-
  rectangular generator shift changed padding and position statistics;
- the corrected experiment explicitly treats absolute frame identity as
  unidentifiable and tests the complete equivalence class instead.

Raw records are retained in [`artifacts/v18spatial`](artifacts/v18spatial).

## Frozen evidence

- Protocol: [`protocol_v18_spatial.json`](protocol_v18_spatial.json)
- Holdout: [`holdout_v18.json`](holdout_v18.json)
- Frozen runner: [`experiment_v18_spatial_frozen.py`](experiment_v18_spatial_frozen.py)
- Core mechanism: [`bpc_spatial_interface_v18.py`](bpc_spatial_interface_v18.py)
- Result: [`artifacts/v18spatial/result.json`](artifacts/v18spatial/result.json)
- Result SHA-256: `f59b80e81c392dc690c58ee9c291c75028a1d5b223d009dcab0453a855bca6d6`
- Protocol SHA-256: `dc4a9e3759d9fd530cb591a984ddcf46886454326e2c26cd4340fadb44b6eeea`
- Holdout SHA-256: `363501478d3d9ce7f03bf3ea888dd7e353c31942589d78ee472444dc4b19f781`
- Video SHA-256: `60655219bd6933acc6f71d0137eac10b503cdb778f1c04966501a0c079965436`
- GitHub release: <https://github.com/JoffeeLin/bpc-sokoban-demo/releases/tag/v18.0.0>

## Boundary

This is developer-frozen held-out synthetic evidence, not a third-party blind
result. Canonical semantics, six raw planes, four actions, maximum 7×7 canvas,
D4 candidate family, nuisance formulas, structural statistics, calibration
schedules, both generators, terminal events, and direct policy remain supplied.
The second generator changes map-shape distribution and code path but preserves
the ontology. This does not establish arbitrary visual grounding, autonomous
representation invention, open-world reasoning, or AGI.
