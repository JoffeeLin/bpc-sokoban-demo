# BPC v0.41 pure residual-medium development result

Status: **FAIL / NON-ADOPTED**. The preregistration was commit `f81cb33` and
the first complete run used it unchanged. This is a development result, not a
frozen reproduction, goal-directed behavior, or evidence of AGI.

## Fixed run

- training: seed `241010`, 8,640 transitions, 357 initial worlds;
- holdout: seed `241110`, 24 disjoint joint-physics worlds and 2,304
  transitions;
- model: one fixed `2^20`-cell Beta residual medium;
- evaluation: zero writes; candidate and control digests unchanged;
- test state before execution: 67/67 unit tests passed.

## Evidence

| Probability residual (Brier; lower is better) | Candidate | No action | Rotated action | Copy | 0.5 |
|---|---:|---:|---:|---:|---:|
| all defined bits | 0.008387 | 0.011234 | 0.009112 | 0.004318 | 0.250000 |
| changed bits | 0.248038 | 0.290895 | 0.337486 | 1.000000 | 0.250000 |
| unseen-context changed bits | 0.285724 | 0.312750 | 0.368265 | 1.000000 | 0.250000 |

There were 2,935 changed-bit cases and 1,543 unseen-context changed-bit cases.
The holdout local-context novelty rate was 39.60%. On changed bits the
candidate improved over the no-action control by 14.73% and over rotated action
by 26.50%. On unseen-context changed bits those improvements were 8.64% and
22.41%, respectively.

Eight of nine fixed gates passed. The failed gate required at least 10%
relative improvement over *both* action controls on unseen-context changed
bits. The no-action comparison reached only 8.64%. This threshold is not
changed after observing the result.

The aggregate copy baseline wins because only 0.43% of evaluated bits change;
that class imbalance is why changed-bit evidence was preregistered separately.
More importantly, the candidate is only marginally better than 0.5 on all
changed bits and worse than 0.5 on unseen-context changed bits. Thus v0.41
contains measurable action information but does not yet provide a sufficiently
general calibrated physical transition law.

## Decision

Do not adopt, freeze, publish as a breakthrough, or proceed to goal behavior.
Retain the raw JSON at `artifacts/v41pure/development.json`. A later candidate
must use a new preregistered development seed and must improve the physical
generalization mechanism rather than weaken this gate or reuse evaluation
observations as training.
