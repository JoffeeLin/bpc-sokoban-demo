# BPC Tetris Reintegration v1.67–v1.70 — Global Residual Diagnostics

Date: 2026-10-06

## Goal
Reintegrate the minimal v1.54–v1.66 residual kernel into real Tetris-visible transitions without restoring Geometry / Collision / Spawn / Closure family observers.

This batch is diagnostic and is **not** promoted as a full Tetris checkpoint.

## Environment slice
- external reference Tetris reality only;
- black/white 10x20 occupancy;
- previous visible frame + current visible frame + external operation;
- non-Lock transitions only, so the first reintegration isolates movement/rotation/collision geometry before downstream Lock/Spawn/LineClear;
- BPC kernel never reads `active`, `world`, piece type, pivot, rotation phase or Tetris labels.

## v1.67 — pairwise global residual only
Input medium: previous frame + current frame + operation port.
One sparse relation store receives only the global next-visible residual.

Short diagnostic:
- train transitions: 2,500;
- evaluation: 400;
- whole-board exact: 0/400;
- per-pixel accuracy: **72.69125%**;
- positive relations: 2,339;
- stored cells: 53,209.

Interpretation: one global residual learns substantial persistence/statistical world structure, but first-order relations cannot uniquely express action-conditioned moving-instance dynamics.

## v1.68 — anonymous temporal/action collision source
Each currently visible BIT collides with:
- its previous-frame BIT state;
- the external operation-port BIT.

The resulting higher-order source has no Move/Rotate/Collision label and is credited by the same global screen residual.

Result:
- train: 7,000;
- eval: 1,000;
- whole-board exact: 0/1,000;
- per-pixel accuracy: **90.719%**;
- stored relations/cells: 68,711.

Interpretation: generic temporal + operation collision is strongly useful and improves pixel prediction by ~18 points over v1.67, but does not close the whole board.

## v1.69 — whole-neighborhood context identity (negative)
The 8-neighbor local pattern was collapsed into one context identity before colliding with temporal/action information.

Result:
- train: 10,000;
- eval: 1,000;
- whole-board exact: 0/1,000;
- per-pixel accuracy: **69.744%**;
- stored cells: 488,890.

Conclusion: packaging local structure into a template-like identity destroys reuse and explodes relation count. This route is rejected.

## v1.70 — superposed one-hop local relation waves
Instead of a neighborhood template, every occupied one-hop relation participates independently and collides with the temporal/action source.

Result:
- train: 10,000;
- eval: 1,000;
- whole-board exact: 0/1,000;
- per-pixel accuracy: **86.1815%**;
- stored cells: 254,032.

This is purer than v1.69 and confirms local relation waves carry useful information, but positive noisy-OR consequences alone cannot express the full conditional move/death physics.

## Scientific conclusion
The failure does **not** support restoring family-specific Geometry observers. Instead it narrows the missing primitive:

`temporal wave × operation wave × local relation wave`
`-> higher-order relation-of-relation`
`-> both positive and reverse mass transfer on visible consequence bits`
`-> one global reality residual`

Tetris requires a context to be able not only to create a destination BIT but also to suppress/release mass at the source. A positive-only OR relation layer cannot represent this when a visible pixel may be either persistent world or a moving process instance under different contexts.

## Next experiment
Extend the minimal one-mass kernel with a generic two-direction mass relation (toward BIT-on or BIT-off) driven by the same global residual, then repeat v1.68. This must remain an anonymous physical relation primitive, not a Tetris-specific movement/death module.