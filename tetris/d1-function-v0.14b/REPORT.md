# BPC × Tetris v0.14b — D1 residual function accumulation

## Question

Can the real residual left unexplained by a mature first-layer function,

[
D_1 = Reality - Prediction_1,
]

accumulate into a second function wave F2 and then act with current raw reality to produce a new stage transition — without Lock, Spawn, Clear, landing-position, reward, planner or search labels?

## D1 is structured

On 20,000 frozen full-game transitions, D1 is not random noise.

| external audit only | mean norm | concentration | pair cosine | residual energy |
|---|---:|---:|---:|---:|
| Move/None | 0.21459 | 0.21089 | 0.03143 | 0.01388 |
| Rotate | 0.39565 | 0.24668 | 0.05921 | 0.04964 |
| Lock | **1.78986** | **0.33335** | **0.10724** | **0.13876** |
| Clear | **1.88791** | **0.42661** | **0.16764** | **0.21508** |
| Game Over | **1.95698** | **0.66284** | **0.43031** | 0.11322 |

Lock residual energy is about 8.3× ordinary Move/None residual energy and has higher cross-state directional concentration.

## v0.12: D1 -> F2

The first layer is frozen. D1 trains an error-writeback second function cube. At inference F2 is produced only from current reality, the first prediction P1 and F1; the true next frame is unavailable.

F2 then queries a third residual field.

Seed0 at 120k hierarchical experience:

- frame exact: 77.82% -> **83.12%**
- Rotate exact: 46.14% -> **77.51%**
- Lock exact: still 0%
- F2 zero: frame returns to 77.04%

So D1->F2 is causally useful but does not yet produce a stable stage transition.

## Function-reality compatibility wave

A task-independent continuous quantity is added: does the future propagation proposed by F1 physically fit the current raw world?

This is not a Lock label or a hand-written blocked flag. It is the continuous compatibility of all participating voxel propagation.

External audit:

| event | compatibility mean | >0.9 | <0.1 |
|---|---:|---:|---:|
| Move/None | 0.9753 | 97.75% | 2.25% |
| Rotate | 0.9821 | 98.33% | 1.67% |
| Lock | **0.0499** | 4.85% | **95.15%** |
| Clear | **0.0011** | 0% | **100%** |
| Game Over | 0.1102 | 10.10% | 89.90% |

This gives F2 a stable, non-semantic query coordinate for “the current function can continue” versus “the current function is closed by reality.”

## v0.13

Adding that compatibility wave to the F2 query improves seed0 at 120k hierarchical experience to:

- frame exact **86.20%**
- Rotate **78.92%**
- Lock 0%

At 300k seed0, Lock briefly reaches 0.33%, but multi-seed testing shows this is not stable enough to adopt.

Lock-component audit at 300k:

- locked-board exact: 26.80% -> **55.59%**
- preview exact: 0.80% -> **80.44%**
- active-plane exact: 1.50% -> **2.08%**

Further active-plane audit shows:

- old active piece cleared correctly: **95.69%**
- top new-active region exact: **1.51%**
- new active positive-bit recall: **8.09%**

So the missing relation is not “stop.” It is long-range creation of the new active state from F2 and current visible reality.

## v0.14b: anonymous block cross-field relation

No `Preview -> Spawn` rule is introduced.

The 417-bit visible state is mechanically partitioned into 27 consecutive 16-bit blocks. All blocks are anonymous and participate equally. F2 and every current block jointly address a residual relation field.

This layer is trained only by the real full next-frame error.

Current implementation applies this cross-field correction to output bits 200..415 (active plane + external visible 16-bit region); the locked board remains predicted by lower layers. This output-range choice is still an experimental scaffold and must be removed later.

### Formal results

30k cross-field experience:

| seed | frame exact | Lock exact | Cross-off Lock |
|---:|---:|---:|---:|
| 0 | **91.16%** | **43.63%** | 0% |
| 1 | 78.16% | **42.55%** | 0% |
| 2 | 80.38% | **43.01%** | 0% |
| 3 | **90.70%** | **47.34%** | 0% |

Seed0 at 60k cross-field experience:

- frame exact **90.838%**
- Lock exact **48.23%**
- Cross-off Lock **0%**

Thus the Lock gain is stable across four independent training-world seeds.

Clear remains **0%**.

## Adopted conclusion

The following causal chain now has stable positive evidence:

[
Reality -> F_1 -> Prediction_1 -> D_1 -> F_2 -> (F_2 × current reality) -> new stage prediction
]

without a Lock semantic label.

This moves full-frame Lock from 0% to roughly 42–48%.

The result supports the idea that when a mature first-order function is closed by reality, its residual can accumulate into a higher-order stage function — but the higher-order function must be re-coupled with current raw reality to produce the distant new state.

## Boundary

This is not full Tetris yet.

- Clear remains 0%.
- The layers are not yet a single fully isomorphic Cube implementation.
- v0.14b still grants the cross-field layer extra output freedom only on bits 200..415.
- The fixed 16-bit physical block size is an engineering choice.
- Total frame/rotation performance still varies across data seeds, although Lock gain is stable.

## Next experiment

Freeze v0.14b and define only:

[
D_2 = Reality - Prediction_{v0.14b}.
]

Repeat the same principle:

[
D_2 -> F_3 -> F_3 × current reality -> next residual.
]

The only acceptance criterion is whether Clear rises from 0 without adding “full row,” “delete row,” “shift down,” or other Tetris rules.
