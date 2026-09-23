# BPC v0.49 residual-activity carry preregistration

This development test asks whether a single task-independent physical activity
law can acquire a causal carry function from reality residuals.  The medium has
no history list, process ID, target coordinate, object rule, reward, task score,
planner or search.  Hashed physical addresses briefly remain active; only the
prediction/reality residual writes through active addresses in the same
anonymous action phase.

The delayed-closure probe presents a physical cue until its anonymous action is
first applied.  The cue then disappears, while the one-bit external boundary
remains open until the same action has accumulated an unknown number of times.
Decorations are independent of cue and fresh per world.  Training uses only
uniform random actions on lengths `3–6`; holdout uses unseen decorations and
longer lengths `7–10`.

Fixed before the first development execution:

- pilot seeds `490001` / `490101` and all their worlds are excluded;
- training seed `491010`: 800 worlds, at most 28 random steps each;
- holdout seed `491110`: 256 fresh worlds, exactly 64 per cue;
- fixed capacity: `2^18` addresses;
- interventions: zero activity readout, baseline-reflected polarity flip,
  one-action coordinate shift, activity erased after every step, and the
  same-information local medium without persistent activity;
- evaluation does not change persistent counts or write counters.

Adoption gates:

1. source hashes match; pilot, training and holdout identities are disjoint;
2. every anonymous action is between 22% and 28% of random training actions;
3. candidate closes at least 70% overall, at least 60% for every cue and at
   least 60% for every held-out length;
4. candidate beats every intervention/control by at least 30 percentage points;
5. non-port world-prediction Brier is at most 0.030 and no more than 10% worse
   than the identically experienced local medium;
6. fixed-capacity compression, zero persistent evaluation writes and unchanged
   digests pass;
7. the complete unit suite passes before execution.

A pass authorizes one independent frozen reproduction.  It would establish a
bounded cross-length carry precursor, not general Sokoban solving, cross-domain
reuse, autonomous planning, phase-three process generalization or AGI.
