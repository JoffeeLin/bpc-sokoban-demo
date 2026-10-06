# BPC Binary World-Fit v1.29–v1.30 — world/action medium symmetry

Date: 2026-10-06
Evidence class: controlled mechanism experiment; not a claim that Tetris operation learning is already solved.

## v1.29 — remove world-output vs action-output heads
A generic relation operator was tested with mixed destination addresses: 300 screen addresses plus 5 action-port addresses. The old implementation used separate screen/action output arrays; the new implementation wrote all destinations into one medium.
Result: 500,000/500,000 random mixed relation graphs exact.
Conclusion: an action port does not require a policy/output head. It can be an ordinary destination address in the same relation medium.

## v1.30 — same Field and same residual writer learn world and action relations
A single probability field stored source->destination relations. Destination addresses mixed ordinary world bits and action-port bits; the learner did not receive a destination class. The same `credit()` and `predict()` equations handled both.
Training contained only singleton screen-source demonstrations. Evaluation used previously unseen multi-source combinations.
Result: 100,000/100,000 exact combined world+action outputs.
Conclusion: no separate action-learning module is required by the mechanism. This is a controlled proof of architectural symmetry, not yet a full Tetris imitation result.

## Implication
The candidate pure interface can treat:
- visible screen bits,
- temporal/history bits,
- external operation bits,
- predicted future screen bits,
- predicted future operation bits
as addresses in one relation medium. Different physical I/O devices may remain outside the kernel; their internal processing law need not differ.