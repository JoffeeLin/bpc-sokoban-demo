# BPC v0.35 factor-responsibility development protocol

This fresh development experiment tests a latent-factor probability mixture,
not a learned gate. For every active anonymous factor, it multiplies that
factor's raw-state action posterior by its first-order action-transition
posterior, normalizes the expert, and marginalizes experts with a uniform prior.
The unchanged additive field is multiplied only after that marginalization.
When fewer than two factors are active it returns the unchanged field exactly.

Training is the unchanged v0.12 separate-task experience at seed `123010`.
No joint object-on-mark world is used for training. Development uses 24 worlds
from the independent generator at seed `235110`, excluding training initials,
the v0.33 frozen holdout, and the reproducible v0.34 development suite.
Evaluation uses seed `235310`, 32 episodes per world, and 48 steps. Old-task
retention uses fresh seed `235210`, evaluation seed `235410`, 16 episodes per
world, and 128 steps.

Before results, adoption requires all of:

- at least 75% aggregate success and four successes on every world;
- at least five percentage points over the field, pooled equal-count temporal
  posterior, uniform factor-temporal mixture, state-only factor mixture,
  joint-only mixture, and shuffled factor/temporal alignment;
- at least ten percentage points over deletion of every learned factor;
- at least thirty percentage points over uniform and rotated semantics;
- at least 95% of field success on every old family;
- exact base/temporal digests, zero train-world object/mark overlap, and zero
  evaluation writes.

classifier.dev routed the candidate weakly (`0.27` confidence) and identified
the shuffled alignment and uniform-responsibility versions as diagnostic
controls. It is not used by the runtime, training, or evaluator. Failure is
retained and never changes these gates.
