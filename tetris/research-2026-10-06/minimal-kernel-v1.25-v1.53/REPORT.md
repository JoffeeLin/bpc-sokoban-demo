# BPC Minimal Kernel v1.25–v1.53 — Scaffold Deletion Report

Date: 2026-10-06

## Evidence boundary
This batch is a mechanism/equivalence and minimal-kernel line. It is **not** promoted as a new full Tetris 8-seed checkpoint. The formally frozen full-world evidence remains separate. The purpose here is to determine which internal scaffolds can be removed without changing the represented physics, and to isolate a smaller candidate kernel for later reintegration into the Tetris evaluator.

## v1.25–v1.35: algebraic/operator reduction
- v1.25: Geometry-specific relaxation -> generic relation-constraint relaxation. 10,000/10,000 exact.
- v1.26: frame/trace storage -> unified BIT slots. 1,000,000/1,000,000 exact.
- v1.27: Action structure -> BITs at ordinary physical action-port relations. 2,000,000/2,000,000 exact.
- v1.28: screen + trace + action -> one input medium. 20,000/20,000 exact in formal reduced run.
- v1.29: separate world/action output heads -> one relation medium. 500,000/500,000 exact.
- v1.30: same Field / credit / predict equations learn both world and action destinations; training singleton-only, unseen multi-source 100,000/100,000.
- v1.31: naive zero-mean gauge removal failed numerically.
- v1.31b: physical-grid gauge removal succeeds. 20,000/20,000.
- v1.32: global zero-mean/min selector -> physical boundary gauge. 20,000/20,000.
- v1.33: relaxation damping is not a world rule; invariant experiment 10,000/10,000.
- v1.34: branch lerp -> ordinary wave superposition. 10,000,000/10,000,000.
- v1.35: product interference -> additive log-wave representation. 1,000,000/1,000,000 physical decisions, max error ~3.3e-16.

## v1.36–v1.39: one lower-level propagation primitive
- v1.36: proposal OR and compatibility interference -> one anonymous two-state mass-transfer operator. 2,000,000/2,000,000, max error ~1.1e-15.
- v1.37: branch consequence and serial interference both use the same mass-transfer primitive. 3,000,000/3,000,000.
- v1.38: explicit temporal `if pixel changed` -> reality-residual carrier driving the same transfer. 2,000,000/2,000,000, exact.
- v1.39: dedicated RELATION token type -> ordered collision of two BIT positions. 16,641 physical relations unique in tested domain; 2,000,000 migrated nested queries exact.

## v1.40–v1.45: pure QEWB relation birth
- v1.40: Beta yes/total counters -> one scalar probability with direct QEWB. World and action ports use same scalar/write/read. unseen multi-source 200,000/200,000.
- v1.41: remove 0.5 prior and centered rectifier. Unborn relation amplitude starts at 0 and grows/decays directly by residual. unseen multi-source 300,000/300,000.
- v1.42: integrated minimal kernel = BIT ports + ordered relation amplitude + QEWB + one transfer operator; world/action destinations use same mechanism. unseen multi-source 1,000,000/1,000,000.
- v1.43: remove input/output port classes. Every BIT port may be condition and consequence at the next tick. unseen multi-source 1,000,000/1,000,000.
- v1.44: dense N×N relation table -> sparse relation birth. unseen multi-source 1,000,000/1,000,000; 48 resident relations vs 576 dense capacity.
- v1.45: remove learning-rate and repeated-epoch curriculum in deterministic singleton setting. One demonstration per primitive source; unseen multi-source 1,000,000/1,000,000; 48 resident relations.

## v1.46: delete singleton curriculum naively — negative
Training frames always contained two simultaneous sources, but each source was credited against the whole next frame independently. Result: 78.58% overall; 2–4 source tests near-perfect, but accuracy collapsed as simultaneous sources increased (8-source ~21.8%).

Interpretation: natural multi-source training is not blocked by representation; the failure is causal-credit pollution. Co-occurring bystander sources must not receive the same local target credit as actual causes.

## v1.47–v1.53: natural multi-source residual and further deletion
- v1.47: counterfactual residual credit using remaining unexplained consequence. No singleton training. 300,000/300,000; true_min=1, false_max=0.
- v1.48: remove learning rate again. Full counterfactual residual directly births/kills relations. 300,000/300,000; 48 resident true relations.
- v1.49: inference propagation and learning writeback -> one conserved mass-motion primitive. 5,000,000/5,000,000 algebraic/physical checks; max error ~1.1e-16.
- v1.50: explicit relation objects `(src,dst)` -> collision-address key + amplitude. 300,000/300,000; 48 residents.
- v1.51: remove token-kind/hash wrapper. Relation address is the ordered physical pair of BIT positions. 300,000/300,000; 48 residents.
- v1.52: counterfactual helper itself is unnecessary for OR/transfer physics. One global output residual `e = reality - prediction` is written synchronously along all participating relations. 300,000/300,000; 48 residents; true_min=1, false_max=0.
- v1.53: integrated implementation where both inference and learning literally use one `move_mass()` primitive. Multi-source stream only, no singleton curriculum, no learning rate. 300,000/300,000; 48 resident true relations.

## v1.53 engineering audit
- C11 `-Wall -Wextra -Werror -pedantic`: PASS
- O2/O3 output diff: 0 bytes
- UBSan stderr: 0 bytes
- source SHA-256: `3da699c7cd1f20deccd9bae34e74699069677d5e2aa9c669e24e42cee0646914`

## Current candidate primitive set
The minimal controlled kernel now supports the following description:

`BIT physical positions`
`+ sparse ordered physical relations`
`+ one conserved mass-motion primitive`
`+ one reality residual`
`+ re-entry through time`
`-> relation birth / death / propagation`

There is no required distinction for:
- world vs action ports;
- input vs output ports;
- BIT vs RELATION token type;
- proposal vs compatibility operator;
- inference vs learning primitive;
- dense predeclared relation matrix;
- Beta counters / 0.5 prior / centered rectifier;
- singleton curriculum;
- learning-rate hyperparameter in the full-residual deterministic test;
- leave-one-out credit helper in the OR/transfer setting.

## Next experiment
Reintegrate the strongest result from v1.52/v1.53 into the real Tetris learning stream: use only the global visible prediction residual and participating relations, with no family-specific credit assignment. The acceptance criterion remains frozen visible-world exactness plus the automatic line-clearing player verification.