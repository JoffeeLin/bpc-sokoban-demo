# BPC v0.47 aligned phase-one frozen result

Status: **PASS / FROZEN REPRODUCTION**.

The first and only authorized reproduction passed all eleven fixed gates on
fresh seeds and initial worlds disjoint from v0.41, v0.42, its frozen run,
v0.44 and v0.47 development.

- full-context novelty: 39.789%;
- overall defined-bit Brier: 0.004083;
- changed-bit Brier: 0.046462;
- unseen-changed Brier: 0.064784;
- improvement over action removal: 83.52% changed, 78.98% unseen-changed;
- improvement over action rotation: 92.39% changed, 89.66% unseen-changed;
- active addresses: 11,803 for 2,735 unique training states;
- evaluation writes: zero, with both digests unchanged;
- frozen source hashes and all 87 unit tests: pass.

Together with the development pass, this repairs the invalidated 2D
interpretation of v0.44 and establishes reproducible aligned one-step physical
prediction on the tested Sokoban-world family. It does not repair or reinstate
the old two-domain v0.44 claim; that would require a new aligned cross-domain
protocol. It also does not demonstrate a goal signal, planning, puzzle success,
cross-domain weight transfer or AGI.

The next theory-gated question is whether the same physical medium can support
a minimal one-bit external closure condition while retaining this frozen world
prediction, with zero/flip ablations and no goal-specific core.
