# BPC v0.28 fourth-factor development — non-adoption and new candidate

## Result

The proposed fourth anonymous co-change factor `(1,2,3)` is **not adopted**.
It was learned from 600 successful object-on-mark traces, but adding it reduced
the new joint-world result from the unchanged old model's 383 / 384 to
365 / 384. Deleting the new factor restored 383 / 384, and old joint-task
retention fell from 61 / 64 to 55 / 64.

| Development condition | New joint successes |
|---|---:|
| Unchanged old three-factor BPC | **383 / 384** |
| New factor deleted | **383 / 384** |
| Added fourth factor | 365 / 384 |
| Shared cube | 362 / 384 |
| Same-new-experience scratch model | 289 / 384 |
| Uniform random | 153 / 384 |
| Rotated action semantics | 0 / 384 |

Only six of nine preregistered gates passed. The full result is
`artifacts/v28fourth/development.json`.

## New candidate, not yet a result

The unchanged old model's 383 / 384 is a post-hoc candidate for stronger
zero-shot composition. Its training families never jointly contain raw object
plane 2 and mark plane 3, while the new terminal interaction changes anonymous
planes `(1,2,3)` and the worlds also require a gate and a separate collection.
This aggregate cannot be promoted from the failed v0.28 experiment. It first
needs source audit, individual old-factor deletions, old-skill retention, and a
new generator/seeds/holdout frozen before execution.

The v0.29 development audit confirmed zero object/mark overlap across 4,412
actual training initial worlds. The unchanged model repeated at 380 / 384;
deleting `(1,3)` reduced success to 297, but deleting `(1,2)` or `(1,4,5)`
only reduced it to 356 and 354. The fixed 10% margin therefore failed. This
supports a zero-shot candidate but does not yet establish causal use of all
three factors; the 160-step suite permits too much random recovery.

v0.30 used 24 fresh development worlds and a precommitted 48-step limit. The
full model scored 479 / 768, while deleting `(1,2)`, `(1,3)`, and `(1,4,5)`
reduced success to 349, 153, and 348: all three fixed causal margins passed.
However, the absolute 75% gate failed at 62.4%, and one difficult world reached
only 1 / 32. The candidate is therefore still not ready for freezing.

v0.31 tested an arithmetic mixture of the independent factor posteriors on 24
more fresh development worlds. It failed decisively: 294 / 768 versus 578 / 768
for the retained additive evidence field and 572 / 768 for the probability
product. Old joint retention also fell from 61 / 64 to 54 / 64. Arithmetic
mixing is not adopted.

v0.32 added factor-conditioned first-order action probabilities learned only
from the original separate successful traces. On 24 fresh development worlds
at 48 steps it reached 628 / 768 (81.8%), versus 566 for the unchanged state
field, 477 for shuffled action history, and 570 for order-zero action counts.
Deleting `(1,2)`, `(1,3)`, or `(1,4,5)` reduced it to 440, 308, and 509.
Old-task retention was 251 / 256 versus 252 / 256, with zero evaluation writes.
All ten development gates passed, so the mechanism is eligible for a new
independent-generator freeze; it is not yet a frozen result.

## Boundary

This is generated development evidence, not frozen or third-party blind
evidence and not AGI. The raw channels, terminal event, dynamics, generators,
and direct probability controller are supplied. No neural network, reward,
task score, planner, runtime search, semantic model rule, classifier runtime,
or evaluation learning is used.
