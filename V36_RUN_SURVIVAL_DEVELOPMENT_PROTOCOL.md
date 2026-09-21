# BPC v0.36 action-run survival development protocol

The candidate learns empirical run-length counts for anonymous actions inside
the unchanged compact successful traces of each old factor. At runtime, while
multiple learned factors are active, the posterior survival probability of the
current action supplies a direct continuation probability; otherwise the
unchanged field acts. There is no option search, goal score, joint-task
training, semantic rule, or collision termination rule.

Training is the unchanged v0.12 schedule at seed `123010`. Development uses 24
worlds from the independent generator at seed `236110`, excluding all training
initials, the v0.33 frozen holdout, and reproducible v0.34/v0.35 development
suites. Evaluation seed is `236310`, with 32 episodes per world and 48 steps.
Old retention uses generation seed `236210`, evaluation seed `236410`, 16
episodes per world, and 128 steps.

Before results, adoption requires all of:

- at least 75% aggregate success and four successes on every world;
- at least five percentage points over the field, structurally gated first-
  order action transitions, age-free survival, rotated action-duration rows,
  and shuffled factor-duration rows;
- at least ten percentage points over deletion of every old factor;
- at least thirty percentage points over uniform and rotated semantics;
- at least 95% of field success on every old family;
- exact base digest, zero train-world object/mark overlap, and zero evaluation
  writes.

classifier.dev routed learned run survival as a high-value direct BPC mechanism
at `0.88` confidence. It is development routing only and never enters the
model. Failure is retained without changing thresholds.
