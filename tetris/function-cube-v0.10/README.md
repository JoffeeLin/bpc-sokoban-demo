# BPC Tetris Function-Cube v0.10

This experiment directly tests the **voxel-product-function** hypothesis:

```
raw local reality
  -> Cube-1 accumulates a function
  -> Cube-1 terminal function wave
  -> queries Cube-2
  -> Cube-2 + current raw reality
  -> next reality
```

Cube-2 never receives an action ID. It only receives the continuous function wave produced by Cube-1 and raw local physical state.

Formal frozen results:

- random 10x20 terrain, random 7 tetrominoes, random four-direction rigid step/collision: **20000/20000 exact**
- four independent random-terrain Hard-Drop seeds: **4 x 5000/5000 exact**
- 10000-state complex-terrain Hard Drop: **10000/10000 exact final state and exact stopping depth**
- no Hard-Drop examples are trained
- function-wave zero / phase flip / coordinate shift: **0%**
- forced-open or reflected shared carrier: **0%**

The formally adopted version is reality-only: Cube-2 is trained from raw before-state + Cube-1 function wave + real after-state. An earlier development version that directly constructed the displacement target is retained only as a negative audit and is not the formal evidence.

See REPORT.md.
