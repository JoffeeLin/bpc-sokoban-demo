# BPC v0.49 residual-activity frozen result

Status: **PASS on the first and only frozen execution**.

v0.49 adds one task-independent physical law to the fixed-capacity BPC medium:
hashed addresses remain briefly active, decay continuously, and permit later
prediction/reality residuals to write through addresses in the same anonymous
action phase.  There is no history list, memory slot, process ID, target
coordinate, reward, task score, planner or search.

Training consisted only of uniform random actions on delayed-closure processes
of lengths `3–6`.  The frozen evaluation used new decorations and unseen longer
lengths `7–10`.

| Frozen condition | Closed / 256 | Rate |
|---|---:|---:|
| residual activity | **232** | **90.63%** |
| zero activity readout | 60 | 23.44% |
| baseline-reflected activity polarity | 82 | 32.03% |
| activity coordinates shifted one action | 58 | 22.66% |
| activity erased after every step | 60 | 23.44% |
| same-experience local medium | 52 | 20.31% |

Every cue orientation passed at 87.5% or higher; every unseen length passed at
86.11% or higher.  Non-port world-prediction Brier was 0.00480 versus 0.00456
for the local medium.  Evaluation made zero persistent writes and left both
digests unchanged.  All preregistered gates passed.

This supports the bounded causal interpretation that residual-born activity
carried an anonymous condition after its physical cue disappeared.  It does
not yet satisfy the full third-stage claim: the probe is not Sokoban, the
process family is supplied, a second domain has not reproduced the dynamics,
and there is no evidence of autonomous planning or AGI.

Machine-readable evidence:
[`artifacts/v49activity/frozen.json`](artifacts/v49activity/frozen.json).
