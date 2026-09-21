# BPC v0.34 suffix-memory development protocol

This is a fresh development experiment, not a frozen claim. The candidate is a
hierarchical probability model over the last zero to four anonymous actions,
conditioned on active learned factor signatures. Each longer suffix backs off
to the shorter posterior with a fixed Dirichlet mass. It is multiplied by the
unchanged state field only when at least two learned factors are active; a
single active factor uses the unchanged field exactly.

The experience remains the exact v0.12 separate-task schedule at seed `123010`.
No joint object-on-mark world is used for training. Development worlds use the
independent generator at seed `234110`, excluding training initials and the
v0.33 frozen holdout. Evaluation uses seed `234310`, 24 worlds, 32 episodes per
world, and 48 steps. Old-task retention uses fresh seed `234210`, evaluation
seed `234410`, 16 episodes per world, and 128 steps.

Before looking at results, adoption requires all of:

- at least 75% aggregate success and four successes on every world;
- at least five percentage points over the field, first-order gated memory,
  rotated suffix history, and order-zero suffix counts;
- at least ten percentage points over deletion of each learned factor;
- at least thirty percentage points over uniform and rotated semantics;
- at least 95% of the field on every old family;
- exact base-model digest, zero train-world object/mark overlap, and zero
  evaluation writes.

Failure is retained and does not change these gates.
