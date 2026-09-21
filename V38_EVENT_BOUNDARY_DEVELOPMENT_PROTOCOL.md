# BPC v0.38 censored event-boundary development protocol

For every transition in each unchanged compact successful trace, the candidate
records whether another action follows. A Beta posterior estimates
`P(trace continues | old anonymous factor, anonymous changed-plane tuple)`.
At runtime that posterior mixes the unchanged state field with the existing
first-order temporal policy. Effects observed only at a separate task's terminal
step therefore reset temporal momentum probabilistically; no effect is named.

Development uses 24 independent-generator worlds at seed `238110`, excluding
training initials, the v0.33 frozen holdout, and reproducible v0.34–v0.37 suites.
Evaluation seed is `238310`, with 32 episodes per world and 48 steps. Old
retention uses generation seed `238210`, evaluation seed `238410`, 16 episodes
per world, and 128 steps.

Before results, adoption requires all of:

- at least 75% aggregate success and four successes on every world;
- at least five percentage points over the field, always-on first-order time,
  global continuation, shuffled event rows, inverted boundaries, and a fixed
  half-strength temporal mixture;
- at least ten percentage points over deletion of every old factor;
- at least thirty percentage points over uniform and rotated semantics;
- at least 95% of field success on every old family;
- exact unchanged training events/base digest, zero train-world object/mark
  overlap, and zero evaluation writes.

classifier.dev routed the censored event-boundary proposal at `0.72`
confidence and rejected semantic rules, reward networks, joint training, and
search. It is development routing only. Failure does not change gates.
