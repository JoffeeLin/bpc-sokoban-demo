# BPC × Tetris v0.19 — Time-Triangle Function Cube

## Hypothesis

For real frames X1, X2, ..., older two-dimensional cube slices participate in more future consequences:

```
L1 -> predict X2 -> residual writes L1
L1+L2 -> predict X3 -> residual writes L1,L2
L1+L2+L3 -> predict X4 -> residual writes L1,L2,L3
...
```

No Lock / Spawn / Clear / GameOver label is used for learning.

## Strongest reproducible candidate

A finite Z=6 temporal cube was trained on complete Tetris trajectories. Each historical slice is queried by the physical frame that occupied it plus the anonymous action-function wave. Prediction at depth k uses all slices 1..k, and real residual writes to all participating old slices.

### 3-seed result, 12k temporal windows

| seed | triangle | last-only | Z-shuffle | no-old-writeback | Lock |
|---:|---:|---:|---:|---:|---:|
| 0 | 71.542% | 45.812% | 64.625% | 53.188% | 0% |
| 1 | 70.688% | 45.417% | 64.438% | 56.458% | 0% |
| 2 | 63.375% | 30.979% | 58.604% | 51.750% | 0% |
| mean | **68.535%** | **40.736%** | **62.556%** | **53.799%** | **0%** |

This supports three causal effects:

1. multiple historical slices are better than only the latest slice;
2. preserving Z order is better than deterministic Z permutation;
3. allowing later residuals to write old participating slices is better than preventing old-slice writeback.

## Depth audit

Seed 0:

| k | triangle | last-only | Z-shuffle |
|---:|---:|---:|---:|
| 1 | 76.917% | 76.917% | 76.917% |
| 2 | 73.667% | 58.750% | 68.500% |
| 3 | 69.333% | 30.583% | 67.667% |
| 4 | 70.250% | 31.083% | 57.917% |
| 5 | 69.250% | 33.083% | 66.000% |
| 6 | 67.250% | 41.167% | 50.000% |

The advantage appears only after multiple slices exist, so it is genuinely temporal rather than a one-step capacity effect.

## Layer deletion at k=6

- full: 67.250%
- remove L1: 57.000%
- remove L2: 63.583%
- remove L3: 68.000%
- remove L4: 66.917%
- remove L5: 66.917%
- remove L6: 54.083%

The newest slice is most important, but the oldest slice also has a large causal contribution. Middle slices already show some interference.

## More depth is not automatically better

Z=12:
- triangle 66.028%
- last-only 40.431%
- Z-shuffle 64.431%
- Lock 0%

Thus adding time depth without better function compression eventually adds interference.

## Negative implementations

Dense continuous projection slices and raw 417-bit outer-product slices were also tested. Dense writeback either saturated or barely changed the baseline after rescaling. A nested ordered-prefix query on top of the DirectFit predictor improved frame accuracy only from 77.750% to about 78.23%, while its causal ablations barely degraded, so it was not promoted.

## Conclusion

v0.19 partially supports the idea that the third dimension can carry temporal function accumulation:

- old slices acquire future-predictive value;
- ordering matters;
- old-slice residual writeback matters;
- earliest and latest slices both carry causal information.

But it does not yet support the stronger statement that a plain stack of 2-D layers is sufficient for complete Tetris process closure. Lock, Clear and GameOver remain 0% in the cleanest candidate.

The next experiment should keep the same time triangle but let each slice's **future-effect relation state itself recursively evolve**, instead of representing a slice as an independent hash table or dense raw-frame map.
