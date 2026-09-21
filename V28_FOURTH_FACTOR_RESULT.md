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

## Boundary

This is generated development evidence, not frozen or third-party blind
evidence and not AGI. The raw channels, terminal event, dynamics, generators,
and direct probability controller are supplied. No neural network, reward,
task score, planner, runtime search, semantic model rule, classifier runtime,
or evaluation learning is used.
