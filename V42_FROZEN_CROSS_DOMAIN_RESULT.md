# v0.42 frozen reproduction and cross-domain result

Status: **OVERALL FAIL / RETAINED**. This was the first execution of commit
`9c1956f`. The core hash was
`68d4c1f1e7898baf0972454c1aca93c3e6e8616b0537c55d34952059c65d35ef`.
No gate is changed and the frozen run is not repeated.

## Track A — independent Sokoban physics: PASS

All 10 gates passed on initial worlds excluded from every v0.41/v0.42
development world.

| Brier residual | Candidate | No action | Rotated action | Copy | 0.5 |
|---|---:|---:|---:|---:|---:|
| all defined bits | 0.006277 | 0.010798 | 0.009559 | 0.004059 | 0.250000 |
| changed bits | 0.140609 | 0.290635 | 0.542659 | 1.000000 | 0.250000 |
| unseen-context changed bits | 0.195181 | 0.311011 | 0.508614 | 1.000000 | 0.250000 |

Novel contexts were 42.57%. On unseen-context changed bits the candidate
improved over action removal by 37.24% and action rotation by 61.63%. Evaluation
made zero writes and left digests unchanged. This independently reproduces the
v0.42 development mechanism for held-out Sokoban transition prediction.

## Track B — particle lattice: FAIL on novelty gate

Nine of ten gates passed.

| Brier residual | Candidate | No action | Rotated action | Copy | 0.5 |
|---|---:|---:|---:|---:|---:|
| all defined bits | 0.012654 | 0.054227 | 0.056440 | 0.053691 | 0.250000 |
| changed bits | 0.034340 | 0.246528 | 0.428535 | 1.000000 | 0.250000 |
| unseen-context changed bits | 0.063386 | 0.249559 | 0.343276 | 1.000000 | 0.250000 |

The candidate strongly outperformed every action control, but only 2.91% of
holdout local contexts were unseen, below the fixed 10% requirement. The
excellent errors therefore demonstrate interpolation over the generated
lattice distribution, not the preregistered amount of unseen-context physical
composition.

## Decision

The combined milestone is non-adopted because both tracks had to pass. Retain
the successful independent Sokoban reproduction as bounded evidence, but do
not claim cross-domain generalization, goal behavior, or AGI and do not publish
this as a breakthrough. A later version must create genuinely more diverse
cross-domain contexts *before* execution; it cannot reuse this frozen result or
lower the novelty gate.
