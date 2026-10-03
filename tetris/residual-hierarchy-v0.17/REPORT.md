# BPC Tetris Residual Hierarchy v0.17

## Main result

The experiment keeps complete 10x20 Tetris trajectories as the only learning stream. The model is never given Lock, Spawn, Clear, or GameOver labels for learning.

The successful hierarchy is:

```
complete reality
-> first function / predictor
-> unexplained residual D1
-> error-writeback produces F2
-> F2 queries Cube3
-> remaining residual D2
-> all anonymous 16-bit physical blocks participate in another writeback field
```

### Why this matters

The first-layer real residual is strongly structured. External audit of RMS residual:

| event | RMS residual |
|---|---:|
| Move | 0.0170 |
| Rotate | 0.0501 |
| Lock | 0.1456 |
| Clear | 0.2128 |

A hash-based D1 wave did not become causally necessary. Replacing it with a continuous physical query wave preserved the stage-transition difference.

The learned 64-D F2 wave then showed:

| event | mean F2 norm |
|---|---:|
| Move | 0.245 |
| Rotate | 0.255 |
| Lock | 0.586 |
| Clear | 0.634 |

Using F2 to query the next cube improved a representative full-frame result from 74.11% to 79.17%. F2-zero reduced the result to 67.34%. Lock board exact rose from 25.47% to 47.18%, and Lock preview exact from 0.80% to 58.45%, though complete Lock was still 0%.

## D2 breakthrough

The remaining residual after Cube3 is D2. No Spawn rule and no explicit Preview routing were added.

The first 416 visible bits were divided into 26 fixed anonymous 16-bit physical blocks. All blocks participate in D2 writeback. Which physical block is useful is determined only by repeated residual consistency.

Representative D2 curve:

| D2 experience | complete Lock |
|---:|---:|
| 20k | 19.05% |
| 40k | 23.97% |
| 60k | 20.97% |

The decline at 60k is retained as a negative result: unlimited writeback begins to cause interference.

## Frozen 3-seed reproduction

| seed | pre-D2 frame | D2 frame | Lock full | Lock board | Lock active | Lock preview | F2-zero Lock |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 80.167% | 81.167% | 13.48% | 35.22% | 18.70% | 46.96% | 0% |
| 1 | 80.933% | 81.367% | 18.78% | 36.24% | 27.95% | 46.29% | 0% |
| 2 | 77.467% | 78.233% | 19.65% | 34.50% | 27.07% | 46.72% | 0% |
| mean | 79.522% | 80.256% | 17.303% | 35.32% | 24.573% | 46.657% | 0% |

This is the first Direct-Fit experiment in this line where complete Lock next-frame accuracy rises stably above 0 without a Lock/Spawn rule.

## Boundary

This is not complete Tetris fitting:
- total full-frame accuracy is about 80%, not 100%;
- Lock full is only about 17.3% mean;
- Clear and Game Over have no positive complete-frame evidence;
- the continuous query-wave form and fixed 16-bit D2 block scale are still researcher-supplied physical scaffolds;
- D2 begins to interfere after extended writeback.

The next theoretical problem is not to add a Clear rule. It is to make residual functions acquire task-independent birth, maturity, decay, reuse, merge, and death so that new function layers do not simply accumulate forever.
