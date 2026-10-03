# BPC Tetris Function-Cube v0.10

## Hypothesis

Instead of asking an engineer-designed query wave to directly retrieve a next state, let one BPC accumulate a reusable function and use its terminal state itself as the query wave of another BPC.

```
Reality -> Cube-1 -> Function wave ΦF -> Cube-2 query + current reality -> next reality
```

Cube-2 is not given action IDs, tetromino IDs, x/y, collision labels, landing positions, Hard-Drop targets, search, planner, or reward.

## Cube-1

Cube-1 observes only 3x3 single-cell physical transitions under anonymous external action channels. Its local Beta residual history produces a continuous 9-dimensional future-effect function wave.

The function wave is not decoded to LEFT / RIGHT / DOWN / UP before it enters Cube-2.

## Cube-2

Cube-2 receives:

- the continuous Cube-1 function wave;
- current raw local occupancy;
- current raw local obstacle occupancy.

Its motion relation field is learned only from raw 3x3 before-state + function wave + real after-state.

Its obstacle relation is a continuous signed relation field:

[
FunctionWave 	imes RawRelativeObstacleWave ightarrow action participation
]

No action index exists in Cube-2.

Multiple cells participating in the same anonymous action form a shared continuous carrier; the carrier continuously mixes moved-state and persistent-state waves. Hard Drop is never trained and is only repeated re-entry of the learned downward function until a fixed point.

## Important negative / correction sequence

### Development v0.1

A first two-cube implementation reached 100%, but audit found that Cube-2's training target displacement kernel was constructed directly from the environment direction table. This leaked function structure and is **not** accepted as formal evidence.

### Reality-only v0.4

After deleting that target leakage, Cube-2 learned only from raw before/after reality. With the same general architecture:

- random rigid step/collision: 72.34%
- random-terrain Hard Drop: about 2–3%

### v0.7: query-coordinate alignment

The remaining collision training used absolute 3x3 obstacle coordinates while inference queried obstacle positions relative to the moving cell. The same physical relation therefore occupied different query coordinates.

Only aligning the query coordinate system, without increasing cube capacity or adding Tetris rules, changed the result to:

- random step: about 90.9%
- Hard Drop: 86–88% across independent worlds

This directly demonstrates the importance of query-wave design.

### v0.8 negative result

Forcing boundary-stop experiences into the same obstacle relation reduced performance. Same external outcome (“stop”) does not imply that two conditions should be forcibly merged into one internal function wave.

### v0.10 adopted result

The probability-category gate was replaced by a continuous signed relation field in Cube-2. Cube-1's entire function wave and all present raw obstacle-relative components participate continuously. There is no top-1 direction choice.

Training remains reality-only.

## Formal frozen results

Random 10x20 terrain, seven tetrominoes, random rotations, random four-direction actions:

- normal: **20000/20000 exact**
- Cube-1 function wave zero: **0/20000**
- Cube-1 function wave coordinate shift: **0/20000**

No Hard-Drop examples are trained.

Four independent complex-terrain seeds:

- seed 0: **5000/5000**
- seed 1: **5000/5000**
- seed 2: **5000/5000**
- seed 3: **5000/5000**

Independent 10000-state audit:

- empty terrain: **10000/10000**, true mean depth = model mean depth = 15.82
- complex random terrain: **10000/10000**, true mean depth = model mean depth = 9.83

Ablations on complex terrain:

- forced-open carrier: **0/10000**
- reflected carrier: **0/10000**
- function-wave coordinate shift: **0/10000**
- function-wave phase flip: **0/10000**
- function-wave zero: **0/10000**

## What this supports

The experiment directly supports:

[
Reality 	o Cube_1 	o Phi_F 	o Query(Cube_2) 	o NewReality
]

and shows that, under nearly the same capacity, changing the query-wave coordinate relation can move generalization from failure to full success.

## What this does not prove

This is not yet full Tetris. Strictly closed on this Function-Cube line:

- translation;
- rigid multi-cell motion;
- obstacle/boundary collision;
- shared-action closure;
- unseen-length Hard Drop recursion.

Still to test with the same principle:

- rotation;
- active-to-locked transition;
- preview-to-spawn;
- line clear;
- game over;
- coexistence of all functions in one long-lived medium.

The next step should keep the same two-cube principle and test Rotation Minimal rather than return to whole-frame memorization.
