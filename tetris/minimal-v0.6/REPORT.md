# BPC Tetris Minimal v0.6 — 9-grid function closure

## Why restart

The earlier experiment asked BPC to directly learn a 416-bit full-frame transition. That makes a tiny spatial law look like a huge state table.

The new hypothesis is simpler: if a single occupied cell in a 3x3 neighborhood can learn an anonymous directional transition, Tetris translation should be the same function reused over many cells and positions. Hard Drop should then be repeated application of the one-step-down function until the state reaches a fixed point.

## v0.1 — over-engineered multi-stencil negative result

Center / horizontal / vertical / full-3x3 stencils were mixed. The model learned source clearing but did not reliably activate the destination. Whole-frame exact was 0%.

This was an important negative result: coarse multi-scale context was unnecessary and diluted the sparse relation.

## v0.2 — one 3x3 local wave

Only a full 3x3 local state plus anonymous action was retained.

Training occurred only in a 3x3 single-cell world. Frozen transfer to 5x5, 10x10 and 10x20 was 100%. Action removal fell to about 24.6%; address displacement fell to 0%.

However a whole 3x3 pattern hash could not compose unseen multi-cell shapes.

## v0.3 — fragment waves and probability superposition

Each occupied cell independently contributes a relation wave indexed only by anonymous action and relative physical offset. Multiple relation waves combine with continuous noisy-OR probability propagation; there is no top-1 routing.

Only 3x3 single-cell experience is trained.

After just one epoch (140 local writes):

- 3x3 single cell: 100%
- 5x5 unseen scale: 100%
- 10x10 unseen scale: 100%
- 10x20 unseen scale: 100%
- four separated cells: 100%
- unseen 2x2 four-cell shape: 100%
- unseen I-piece: 100%
- all seven standard tetrominoes, random rotations and positions: 10000/10000
- action blind: 25.85%
- relation-fragment shift: 0%

Therefore a tetromino translation does not require a tetromino object module. It is parallel reuse of the same single-cell physical function.

## v0.4 — collision is also local

A second raw binary plane is added as static environment occupancy. The frozen movement function acts first. Only the unexplained reality residual writes an anonymous second-order local relation.

Training still uses only 3x3 single entity + single obstacle experiences.

Frozen 10x20 single-entity collision is 100%. Removing/flipping/shifting the second-order relation returns to ~50%.

A previously unseen rigid 2x2 shape with one blocked cell is only ~50%: the clear half works, but a local blocked cell does not yet stop the other cells.

This isolates the remaining relation: a local incompatibility must affect every cell participating in the same anonymous action.

## v0.5 — shared action wave

Each occupied cell emits the learned probability that its destination can continue to be occupied. All cells participating in one anonymous action remain continuous and form one shared carrier:

`C = product(p_i)`

The next field is continuous interference between translated and persistent state:

`P(next) = C * moved_wave + (1-C) * persistence_wave`

There is no tetromino type, object ID, collision label, blocked flag, or hand-coded `if(any blocked)`.

Training remains only 3x3 single entity + obstacle.

Frozen 10x20 tests across seven tetrominoes, random rotations and random one-cell blockers:

- normal shared wave: 10000/10000
- blocked subset: 100%
- clear subset: 100%
- mean blocked carrier: 0.000
- mean clear carrier: 0.989
- forced-open carrier: 50.76%
- reflected carrier: 0%

This demonstrates that rigid consistency can be produced by shared continuous action participation rather than a Tetris-specific object rule.

## v0.6 — Hard Drop is recursive closure, not a new function

No Hard Drop example is ever trained.

The already learned one-step-down function is simply re-entered:

`X -> F_down(X) -> F_down(F_down(X)) -> ...`

until a fixed point:

`F_down(X*) = X*`.

A useful diagnostic appeared: one epoch is sufficient for 100% discrete one-step output, but the internal learned destination probability is only about 0.929. Multiplying four such probabilities weakens the shared carrier and can create recursive ghost state. Repeating the same 3x3 experience to 30 epochs changes no discrete function but matures the probability state enough for stable recursion.

With random seven-tetromino starts and random lower-board terrain:

- exact final landing: 10000/10000
- exact stopping-step count: 10000/10000
- true mean depth: 10.88
- model mean depth: 10.88
- shared carrier removed: 0/10000

So the earlier interpretation of Hard Drop as a special long-distance mapping was wrong for this environment.

A better statement is:

`Hard Drop = repeated reuse of a learned one-step function until physical closure.`

## Theory correction

For basic Tetris motion, the useful hierarchy is much smaller than the earlier full-frame model:

`single local relation -> multi-cell probability superposition -> shared action wave -> temporal recursion`.

This is consistent with the BPC function-compression goal: small experience produces a reusable process whose spatial extent and recursion depth do not require new position-specific functions.

## Still unresolved

This does not claim full Tetris is solved. Remaining experiments should stay minimal:

1. rotation as a local function;
2. active-to-locked phase change after the shared action reaches closure;
3. visible preview to new active spawn;
4. row deletion / downward shift;
5. finally, whether all of these can coexist in one unchanged minimal medium.

The next experiment should be Rotation Minimal, not a return to large full-frame Tetris fitting.
