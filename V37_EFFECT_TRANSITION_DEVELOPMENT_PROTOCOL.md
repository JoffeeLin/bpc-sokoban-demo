# BPC v0.37 observable-effect transition development protocol

The candidate learns Dirichlet next-action counts conditioned on three anonymous
variables from the unchanged separate successful traces: old factor signature,
previous action, and the tuple of raw planes changed by that action. The effect
is retained for one following decision. Unseen effect rows back off to the
already tested first-order action transition. No plane is named and no joint
object-on-mark world is used for training.

Development uses 24 independent-generator worlds at seed `237110`, excluding
all training initials, the v0.33 frozen holdout, and reproducible v0.34–v0.36
development suites. Evaluation seed is `237310`, with 32 episodes per world and
48 steps. Old retention uses generation seed `237210`, evaluation seed `237410`,
16 episodes per world, and 128 steps.

Before results, adoption requires all of:

- at least 75% aggregate success and four successes on every world;
- at least five percentage points over the field, gated first-order action
  transition, event-only transition, erased-event transition, shuffled-event
  rows, and rotated next-action columns;
- at least ten percentage points over deletion of every old factor;
- at least thirty percentage points over uniform and rotated semantics;
- at least 95% of field success on every old family;
- exact base event counts, zero train-world object/mark overlap, and zero
  evaluation writes.

classifier.dev routed the full observable-effect proposal as a candidate at
`0.56` confidence and rejected semantic phases, planning, and joint training.
It is development routing only. Failure is retained without changing gates.
