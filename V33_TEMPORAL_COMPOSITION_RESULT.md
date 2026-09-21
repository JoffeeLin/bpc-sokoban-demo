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
