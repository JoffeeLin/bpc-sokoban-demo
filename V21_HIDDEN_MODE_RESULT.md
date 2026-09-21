# BPC v0.21 hidden actuator regimes — frozen non-adoption

## Question

Can the frozen non-neural BPC controller infer two unlabeled stochastic
actuator regimes and their Markov switching law, then use only ephemeral
Bayesian filtering on disjoint worlds behind anonymous sensors, D4 frames, and
unknown delays?

## Frozen result

The result is **FAIL / NON-ADOPTED**. The online controller succeeded in
1,453 / 1,536 episodes (94.6%), near the hidden-mode oracle's 1,474 / 1,536,
and above the stationary memoryless control's 1,388 / 1,536. Those aggregate
numbers do not override the preregistered per-interface gates.

| Interface | Online | Oracle | Memoryless | Shuffled | Wrong lag |
|---|---:|---:|---:|---:|---:|
| 0 | 489 / 512 | 493 | 451 | 442 | 461 |
| 1 | 488 / 512 | 495 | 470 | 421 | 473 |
| 2 | 476 / 512 | 486 | 467 | 436 | 467 |

On complex joint worlds, online filtering scored 331 / 384 versus 295 / 384
for memoryless control. Interface 2 nevertheless tied memoryless and wrong-lag
controls at 104 / 128, so the required 5% causal margin failed there. The
overall 3% memoryless margin also failed on interface 2. Model writes were zero
and the model digest remained unchanged.

The frozen protocol is `protocol_v21_hidden.json`; its SHA-256 is
`9646b93d969c76da8e14a67e395d3b25819855bd3a9b7eaebf034a0e4c2b53ff`.
The holdout is `holdout_v21.json`; its SHA-256 is
`db980ea933da617e1dedc0f8768aff66244aab8414ac254e28079bcd48ca4511`.
The full result is `artifacts/v21hidden/result.json`.

## Retained failures

- Development attempt 1 collapsed hidden modes before lag inference and chose
  lag 4 instead of 1 on one interface.
- Attempt 2 repaired lag inference but missed the causal control margins.
- Attempt 3 recovered channels, transitions, and filtering but long-horizon
  simple tasks diluted the causal effect.
- The first frozen execution stopped before reading the holdout because native
  tuples were compared with JSON arrays. Its exact protocol, holdout, sources,
  and failure note are retained. Re-freezing changed only the verifier source
  hash; the holdout hash stayed identical.
- v0.22 development censored canonical no-change emissions. It failed its own
  preregistered development gates and was not frozen.
- v0.23 used the posterior MAP mode for direct action selection. It matched the
  factorized posterior average on the failed interface's complex worlds and was
  not frozen.
- v0.24 replaced factorized effect likelihoods with a single empirical joint
  raw-effect category. It improved the failed interface from 55 to 57 complex
  successes out of 64, below the preregistered four-success margin, and was not
  frozen.
- v0.25 used that same joint categorical emission consistently in Baum-Welch
  fitting and online filtering. Parameter recovery improved, but the failed
  interface gained only one complex success over the factorized model and one
  other interface failed its shuffled-channel margin. It was not frozen.
- v0.26 conditioned the joint emission on raw relational change probabilities
  learned by `RelationalBPC`, sharing observations across all D4 transforms.
  It recovered the hidden parameters accurately, but interface 2 gained only
  two complex successes over v0.25 and interface 0 regressed by one success
  overall. It failed the fixed development gates and was not frozen.
- v0.27 propagated hidden-mode belief through the actuator delay and replaced
  a sampled task action only with a no-less-probable action carrying more
  mode/raw-change mutual information. Active probing lost to its matched random
  probe on all three interfaces; on interface 2 it scored 241 / 256 versus 252
  / 256, and 51 / 64 versus 60 / 64 on complex worlds. This rejects immediate
  binary-change information as the cause of the random probe improvement.

## Boundary

This is developer-frozen synthetic evidence, not third-party blind evidence
and not AGI. The two-state Markov family, D4 family, lag range, sensor schema,
sufficient statistics, terminal events, and Bayesian recursion are supplied.
No neural network, reward, planner, runtime search, hidden label, classifier
runtime, or evaluation learning is used. classifier.dev only routed candidate
development ideas and did not participate in model inference or evaluation.
