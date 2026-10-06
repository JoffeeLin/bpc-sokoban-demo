# BPC Binary World/Action Medium v1.31–v1.33 — unified temporal residual experiments

Date: 2026-10-06
Evidence class: controlled mechanism experiments. These do not yet claim full Tetris imitation; they test whether world and action relations require different internal learning laws.

## v1.31 — one temporal relation medium, naive source credit (negative)
Screen-like bits, action-port bits and history-like bits were placed in one address space. A single temporal relation `dt=+1` was used for all destinations. However, every active source was credited with the full future target vector.
Result: whole 0/100000, world 0/100000, action 6546/100000.
Conclusion: unifying the medium is not sufficient if residual responsibility is still assigned naively to every simultaneously active source.

## v1.31a — more diverse continuous stream (negative)
The same learner was given more exogenous variation in one continuous stream. The failure persisted.
Conclusion: the problem is credit assignment, not simple coverage.

## v1.32 — temporal dependence instead of per-source target labels (partial)
The learner no longer receives per-edge target labels. Each source/destination relation is estimated from the difference `P(y|x)-P(y|not x)` in the same stream.
Result: causal mean 0.161273 versus noncausal 0.001435, but exact reconstruction remained insufficient.

## v1.32b — log-odds relation wave (partial)
Probability difference was replaced by positive log-odds change so multiple independent causes do not dilute a true relation as strongly.
Result: world 98.273%, action 99.755%, whole 41.088%.
Causal mean amplitude 0.987454; noncausal 0.084035.
Conclusion: temporal dependence is present, but stream correlation still produces spurious relations.

## v1.33 — joint prediction residual with marginal relation responsibility (positive)
All active relations jointly produce each future BIT using one noisy-OR prediction law. The one global output residual is written back continuously to every participating relation according to its exact noisy-OR marginal responsibility. No source class, destination class, world head, action head, or separate action learner exists.

Training: one continuous mixed event stream.
Evaluation: 100,000 unseen multi-source combinations.

Result:
- whole event exact: 100000/100000
- world bits exact: 100000/100000
- action-port bits exact: 100000/100000
- mean causal relation amplitude: 0.998430
- mean noncausal amplitude: 0.000000

Interpretation: world and action relations can be learned by the same Field, same predictor and same residual-responsibility rule. The key requirement is correct joint responsibility, not an Action-specific learning module.

## Next scaffold target
Remove the remaining explicit temporal-role API (`now/future/dt` as named function roles) by representing time only as an ordinary relation coordinate in the same event medium.