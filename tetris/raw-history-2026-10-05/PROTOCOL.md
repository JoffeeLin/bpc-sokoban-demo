# Raw history and symmetric physical memory — pre-run protocol

Baseline: commit c2f2d3d79a13726ff2f74fb4b28ca8d529beef46.
New cold-start experiment: no active/world split, trace input, geometry/spawn/
closure/route/life executors, role labels, goal scores or player heuristics.
Only full raw pixels, anonymous operation and actual next raw pixels train one
flat probability field. The game renderer remains outside the core.

First test two actually reachable games with identical pixels but different
next consequences. Repeat blocked operations to make any short raw window
identical. This validates the need for historical information, not preset roles.

Compare a shared local raw-history probability rule with/without symmetric
per-operation XOR accumulation of observed pixel changes. No operation gets
special semantics. Match probabilities use raw next bits; no hand role targets.
Train only executed experiences from handwritten anonymous tapes, plus the two
explicit handwritten causal histories. No fabricated teaching boards.

Before release: strict full-frame self-rollout of all five operations, old eight
seed streams and fresh indices 24–27; five new score-free play streams, seeds
20261030–20261034; frozen field bytes; action/field/memory controls; strict C11,
O2/O3 and UBSan. Separately report teacher-forced diagnosis and never count it
as self-rollout. Promotion requires every formal self-rollout step exact.

Preserve failures. Never promote background-dominated bit accuracy, fitted
causal examples or a renamed role adapter as complete Pure BPC. Fixed spatial
supports, time window, fallback and memory laws remain design assumptions.

Amendment before formal 20,000-piece training: the first local-only pilot
failed the actually executed HardDrop in both causal histories. A radius-2
support at the landing site cannot observe the distant source. The uniform
candidate now opens a whole-medium conditional support on a pixel residual,
then counts every matching observation. This applies to every operation/site,
with no drop-specific rule. It is a cache and must not be called a learned
transition program. Compile with GLOBAL_SUPPORT=0 to reproduce the rejection.
Both memory variants receive identical actual tapes/seed and causal replays.

Operation-coverage correction before final tests: the original seventeen tapes
contain no channel 2. The paired histories expose that channel only in one
shape/position. Preserve the initial 17-tape failure separately, then add six
handwritten tapes: 2224, 002224, 112224, 32224, 332224, 3332224. These are real
executed operations, not generated board labels or rules. Retrain both cold
fields on the same 20,000-piece / seed-55901 stream of all 23 tapes. All frozen
original/fresh tests are repeated. ONLY_ORIGINAL_TAPES reproduces the rejected
coverage. No model law is changed for this correction.

Final auditor note: on the first self-prediction failure, stop counting that
model's checked prefix but continue the true trajectory. This keeps the full
real episode/action/RNG stream identical between variants. Whole no-error
counts and checked-prefix counts are separate. The score-free play test keeps
predicting after errors; teacher-forced diagnostics are separately named.
