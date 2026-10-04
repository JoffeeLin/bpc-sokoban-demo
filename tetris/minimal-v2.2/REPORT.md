# BPC Tetris Minimal v2.2 — local functions to fixed-point world dynamics

## 1. Summary

The earlier formulation `416-bit frame + action -> 416-bit next frame` makes a small physical law look like a large state table.

The minimal line instead uses:

`local single-cell relation -> multi-cell probability superposition -> shared action carrier -> temporal recursion -> residual-born downstream relations -> fixed point`.

Move, collision, Hard Drop, Rotation, Lock, Spawn and Line Clear were first isolated as small experiments, then recomposed into one running world.

Frozen v2.2 matched the reference environment on **404,330 / 404,330** ticks across five independent rollout seeds, including **124,841** Lock events.

This is not an AGI claim and not a complete Tetris Guideline implementation. It is evidence that many apparently global Tetris transitions in this controlled world reduce to a small number of reusable local relations and recursive closure.

## 2. v1.8: geometry leaves the learner

Earlier inference had already removed direct target-coordinate oracles, but several training routines still computed the correct geometry internally.

v1.8 moves that geometry back into the external micro-world. The external world produces raw before/after states; learning routines only observe the experience.

Frozen results remain 100% for the integrated one-step test and the long rollout.

## 3. v1.9: remove the Line Clear top-1 selector

The old clear implementation selected the strongest full row first. v1.9 removes that discrete selector.

Every row emits the same learned carrier. All original row carriers participate; non-full rows remain below action strength. The resulting hole carriers propagate upward locally.

One through four simultaneous full rows all reached 10,000/10,000 exact. Carrier-off and reflected-carrier controls were 0%.

## 4. Rotation input-closure audit

The current simplified reference engine stores a hidden pivot/orientation state.

Exhaustive enumeration found:

- 3,053 distinct visible active masks;
- 695 masks with more than one valid next ROT frame;
- ambiguity in O/S/Z symmetric states;
- a current-visible-mask-only exact lookup ceiling of about 75.68% under the exhaustive hidden-state distribution.

Therefore current pixels alone are not a complete Markov state for this specific rotation engine.

## 5. v2.0: the real pivot is no longer an external input

Instead of feeding the hidden pivot to BPC, the model maintains its own history carrier.

It is born from learned Spawn experience, transported by the same learned movement dynamics, and used internally during rotation. During rollout the true environment pivot is never copied into the model.

5,000 episodes / 200,935 compared ticks remained 100% exact.

## 6. v2.2: remove explicit process waiting

A learned QGate previously delayed Spawn while line-clear work remained. v2.2 removes that gate entirely.

To make the test stricter, the internal relaxation deliberately uses the opposite order from the reference semantics:

`Spawn relation -> Clear relation`

All relations keep acting on the revised state until no state changes remain. A temporarily inconsistent Spawn/GameOver state is corrected by later relaxation.

Despite the deliberately wrong micro-order, the frozen final world remains exact.

## 7. Formal reproduction

Five independent seeds:

- 80,925 / 80,925
- 80,862 / 80,862
- 80,846 / 80,846
- 81,467 / 81,467
- 80,230 / 80,230

Total: **404,330 / 404,330 = 100%**.

## 8. Remaining scaffolds

The result still does not mean a pure BPC has autonomously invented Tetris.

The main remaining researcher-provided structure is that Move, Rotate, Spawn, Lock and Clear still occupy preallocated relation-media families. The latent pivot has also been allocated as a carrier plane, even though its value is no longer externally supplied.

The most important next experiment is therefore not another Tetris rule. It is to remove these named media and let a shared anonymous residual medium differentiate the functions itself.
