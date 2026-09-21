# BPC v0.43 causal-lattice preregistration

This protocol is committed before any v0.43 model is trained or evaluated.
The unmodified v0.42 core hash must remain
`68d4c1f1e7898baf0972454c1aca93c3e6e8616b0537c55d34952059c65d35ef`.

The earlier particle lattice failed because its 3x3 support was nearly
exhausted. A generator-only pilot using discarded seeds `43001/43002` measured
58.99% unseen full contexts; no model was trained and no target error was read.
Those initial lattices are excluded from the formal experiment.

## Physical domain and fresh data

Each 8x8 byte carries a fixed barrier bit, a mobile bit and a persistent
terrain-phase bit. Four anonymous actions apply four physical directions. A
mobile bit advances simultaneously only when its target is open and the target
phase matches the action parity. The phase therefore changes the real next
state; it is not an identifier or decorative background.

- training seed `244020`: 120 unique lattices from each of three fixed
  wall/mobile/phase-density regimes, 24 uniform random actions each;
- holdout seed `244120`: 24 unique lattices from continuous density mixtures,
  four streams and 24 uniform random actions;
- formal train/holdout initials must be mutually disjoint and disjoint from the
  discarded pilot initials;
- all three physical bits in all 64 cells are scored.

## Controls and fixed gates

Controls are the same-capacity action-removed medium, rotated action, copy,
0.5, and a phase-flipped counterfactual query. Flipping bit 2 everywhere
preserves byte count and complexity but changes the causal permission signal.

Adopt this second-domain result only if every gate passes:

1. all initial-lattice disjointness checks and the fixed core hash pass;
2. at least 25% of holdout `(action, 3x3 bytes)` contexts are unseen;
3. overall defined-bit Brier is at most `0.030`;
4. changed-bit Brier is below `0.25`, copy-current and the 0.5 predictor;
5. unseen-context changed-bit Brier is at most `0.25`;
6. candidate improves on action removal and rotated action by at least 10% on
   changed and unseen-context changed bits;
7. candidate improves on phase-flipped input by at least 10% on changed and
   unseen-context changed bits;
8. capacity remains `2^20`, raw states exceed active cells divided by 64, and
   active cells are reported;
9. evaluation performs zero writes and leaves every digest unchanged;
10. the complete unit suite passes before execution.

No threshold or generator distribution will change after results. A pass,
together with the already independent v0.42 Sokoban-physics reproduction,
would establish same-core held-out physical prediction in two domains with a
causal second-domain input ablation. It would still not establish goal-directed
behavior, weight transfer or AGI.
