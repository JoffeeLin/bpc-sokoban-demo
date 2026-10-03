# BPC Tetris Minimal v0.6

This line deliberately restarts Tetris from the smallest physical relation:

`3x3 raw occupancy + anonymous action -> next raw occupancy`.

It does not train tetromino IDs, x/y, landing positions, collision labels, Hard Drop, or a full-frame Tetris transition table.

## Frozen results

- 3x3 single-cell training -> 5x5 / 10x10 / 10x20 single-cell motion: **100%**
- Same single-cell function -> unseen 2x2, I-piece, and all 7 tetrominoes at random rotations/positions: **100%**
- Action-blind ablation: ~25.85%; fragment-address shift: 0%
- 3x3 single-cell + obstacle training -> 10x20 single-cell collision: **100%**
- Shared action wave -> unseen 7-tetromino rigid collision: **10000/10000**
- Forced-open shared carrier: 50.76%; reflected carrier: 0%
- No Hard-Drop training. Recursive application of learned one-step-down function on random 10x20 terrain: **10000/10000 exact final landing**, exact step count **10000/10000**
- Carrier-off recursive control: **0/10000**

Main correction: Hard Drop is not a new long-distance function here. It is a learned one-step function recursively reused until a fixed point.

See REPORT.md and the C sources in this directory.
