# BPC v0.40 recursive factor-belief development preregistration

This development experiment is fixed before its first execution. It asks
whether a recursively updated probability distribution over the already learned
anonymous factors improves cross-generator composition. It is not frozen or
blind evidence.

## Fixed mechanism and experience

- Reuse the exact v0.12 separate-task experience schedule at seed `123010`.
- Learn no joint-world examples, reward, value, task score, semantic phase,
  planner, search procedure, neural network, or language rule.
- For each successful separate trace, retain the existing spatial field,
  first-order action probabilities, and censored event-boundary probabilities.
- Additionally estimate a Dirichlet probability of each raw changed-plane tuple
  conditioned on the learned anonymous factor signature and action.
- At runtime, recursively update factor belief by the chosen-action likelihood,
  then by the observed raw-change likelihood. The learned event-boundary
  probability mixes the posterior with a uniform belief over factors still
  present in the next raw observation.
- Evaluation performs zero persistent writes.

## Fixed development data

- Generator seed: `240110`; action seed: `240310`.
- 24 unseen joint worlds, 32 episodes per world, 48 steps per episode.
- Exclude training worlds, the v0.33 frozen worlds, and all development suites
  generated with seeds `234110` through `239110`.
- Old-family retention: seed `240210`, four worlds per family, 16 episodes,
  128 steps, action seed `240410`.

## Fixed controls and adoption gates

Controls are the state field, memoryless uniform factor belief, no chosen-action
update, no raw-effect update, no event-boundary reset, shuffled factor/emission
association, hard-MAP belief, uniform actions, rotated action semantics, and
each single-factor deletion.

Adopt for a new independent freeze only if all conditions hold: at least 75%
aggregate success; every world has at least four successes; the candidate beats
the field and every same-information non-deletion control by at least five
percentage points; it beats each factor deletion by at least ten points; it
beats uniform and rotated semantics by at least thirty points; every old family
retains at least 95% of the unchanged field; training events match the frozen
schedule; training object/mark overlap is zero; and evaluation writes and model
digests remain unchanged.

classifier.dev `jev-1.13.0` was used only to route the development candidate and
controls. It is absent from training, runtime, and evaluation. Publication is
forbidden on a development-only result; a full pass only authorizes a separately
committed independent frozen v0.41 test.
