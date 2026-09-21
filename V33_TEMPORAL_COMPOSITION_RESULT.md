# BPC v0.33 temporal composition freeze — not adopted

## Frozen result

The factor-conditioned first-order action-transition policy is **not adopted**.
The holdout and protocol were committed before their first execution. The
evaluation then ran two fixed action seeds and repeated the complete bundle
exactly, without evaluation writes.

| Frozen condition | Successes / 768 |
|---|---:|
| Temporal policy | **378 (49.2%)** |
| State field | 303 (39.5%) |
| Order-zero action counts | 307 (40.0%) |
| Shuffled action history | 233 (30.3%) |
| Delete factor `(1,2)` | 292 (38.0%) |
| Delete factor `(1,3)` | 164 (21.4%) |
| Delete factor `(1,4,5)` | 265 (34.5%) |
| Uniform | 32 (4.2%) |
| Rotated action semantics | 3 (0.4%) |

The temporal policy improved on every required control and every held-out world
had at least four successes across the two seeds. However, it missed the fixed
75% aggregate threshold and both seeds missed 70%. Old-task retention was
243 / 256 versus 248 / 256 for the unchanged field; one push-family seed also
missed the fixed 95% retention ratio. Eleven of fourteen gates passed, so the
bounded hypothesis failed.

## What is supported

First-order action-transition probabilities learned only from separate
successful factor traces make a causal contribution on the new interaction:
shuffling history, removing history, or deleting any old factor reduces the
result. That contribution is not sufficient for reliable cross-generator
composition. No breakthrough, release, or general-intelligence claim follows.

The machine-readable evidence is
[`artifacts/v33temporal/result.json`](artifacts/v33temporal/result.json). The
frozen holdout hash is
`e49fcd4b5c754817339e8085821428577eebaf52c9f1d4884c87f597f9cc52c5`;
the result records an exact deterministic repeat and zero model writes.

## Boundary

This is developer-frozen synthetic evidence, not third-party blind evidence or
AGI. The raw channels, terminal event, factor signatures, dynamics, generators,
first-order temporal family, and direct controller are supplied. No neural
network, reward, task score, planner, runtime search, semantic model rule,
classifier runtime, or evaluation learning is used.

## v0.34 development follow-up

A hierarchical zero-to-four-action suffix model was tested once on 24 fresh
development worlds excluded from the v0.33 holdout. It reached 480 / 768
(62.5%), versus 405 for the state field, 409 for order-zero counts, and 504 for
a structurally gated first-order model. The longer suffix therefore lost to its
precommitted first-order control and also missed the unchanged 75% absolute
gate. It is not adopted. The composition gate did remove the old-skill
regression: suffix and field both reached 251 / 256 on fresh old-task worlds.
The machine-readable result is
`artifacts/v34suffix/development.json`.

## v0.35 development follow-up

A uniform latent-factor mixture multiplied each factor's raw-state posterior by
its first-order temporal posterior before marginalizing factors. On another 24
fresh excluded development worlds it reached 478 / 768 (62.2%), versus 330 for
the field, 407 for pooled temporal counts, 408 for uniform factor-temporal
mixing, and 399 for state-only mixing. However, shuffling the factor/temporal
alignment still reached 461, below the required five-point causal margin; one
world reached only 1 / 32. Old joint retention also fell to 45 / 64 versus
51 / 64 for the field. The mechanism is not adopted. Its machine-readable
result is `artifacts/v35responsibility/development.json`.

## v0.36 development follow-up

An action-run survival model learned run-length posteriors from the same compact
separate-factor success traces. It scored 261 / 768 (34.0%), below both the
field at 313 and the structurally gated first-order model at 422. Removing run
age, rotating duration rows, or shuffling factor-duration rows produced nearly
the same result, so learned duration structure was not causal under the fixed
gates. Old joint retention also fell to 49 / 64 versus 56 / 64. The mechanism
is not adopted. Its machine-readable result is
`artifacts/v36runs/development.json`.

## v0.37 development follow-up

An observable-effect model conditioned next actions on the previous anonymous
action and changed-plane tuple. It reached 428 / 768 (55.7%), only four
successes above the gated first-order model at 424 and five above the
event-erased control at 423. It therefore failed both the 75% absolute gate and
the five-point causal margin; old joint retention was 55 / 64 versus 59 / 64.
The training audit explains the weak increment: only `(1)` and `(1,3)` had
observable successor actions. Push `(1,2)` and open `(1,4,5)` effects occur at
the terminal step of their separate tasks, so no post-event action exists to
estimate. The mechanism is not adopted. Its machine-readable result is
`artifacts/v37effects/development.json`.

## v0.38 development follow-up

A Beta event-boundary posterior learned whether each anonymous raw effect had a
successor action. The counts were sharply separated: ordinary `(1)` movement
always continued, while push `(1,2)` and open `(1,4,5)` effects always ended
their separate-task traces; collect `(1,3)` contained both terminal and
continuing events. Boundary-gated control reached 439 / 768 (57.2%), versus 428
for always-on first-order time, and retained 247 / 256 old tasks versus 241 for
the field. Yet it missed the 75% gate, had one world at 2 / 32, and its 11-win
gain over always-on time missed the fixed 39-win causal margin. It is not
adopted. Its result is `artifacts/v38boundary/development.json`.

## v0.39 development follow-up

Factor-specific Beta raw-change probabilities were trained by replaying every
transition from the unchanged separate-task successful traces, then multiplied
with the event-boundary direct policy. The full product reached 415 / 768
(54.0%), versus 394 for the boundary policy, 402 for the old v7 fixed-0.24
fusion, and 409 for a shared change cube. Those 21-, 13-, and 6-win gains all
missed the fixed 39-win causal margin; one world reached only 2 / 32. Old push
retention also fell to 53 / 64 versus 56 / 64 for the field. Raw-change fusion
is not adopted. Its result is `artifacts/v39change/development.json`.

## v0.40 development follow-up

A recursive probability state tracked responsibility across the three anonymous
factors. At every step it updated factor belief with the selected action, the
observed changed-plane tuple, and the learned probability that the current
factor event continued. It reached 434 / 768 (56.5%), versus 430 for a
memoryless factor mixture and 276 for the state field. The apparent gain over
memoryless control was only four successes. Removing raw-effect updates reached
438, and shuffling factor/emission associations reached 441, so the proposed
observation update was not causal. One world remained at 0 / 32, and deleting
the `(1,2)` factor lost only twelve successes rather than the required 77.

The boundary reset itself was useful: removing it reduced success to 354. Old
task retention was 252 / 256, equal to the field total, and all evaluation
write/digest checks passed. Nevertheless, four preregistered adoption gates
failed, so the model is not frozen or published. The machine-readable result is
`artifacts/v40recursive/development.json`.
