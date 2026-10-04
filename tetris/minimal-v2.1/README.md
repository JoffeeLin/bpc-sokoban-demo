# BPC Tetris Minimal v2.1 — Screen + Action Only

This version removes the hidden pivot/orientation state from both the model interface and the simplified Tetris reality.

The frozen model interface is now:

```
Visible Active
+ Visible World
+ Visible Preview
+ Action
-> next visible state
```

## Formal frozen result

Across 8 independent seeds:

- one-step states: **40,000 / 40,000 exact**
- free self-reentry rollout: **312,839 / 312,839 ticks exact**
- lock events: **96,635**, no divergence
- game-over events: **8,000**, no divergence
- Left / Right / Down / Rotate / Hard Drop failures: **0**

Representative single-seed run:

- one-step: 20,000 / 20,000
- free rollout: 78,061 / 78,061
- locks: 24,180
- game overs: 2,000

## Key correction

The earlier hidden-pivot engine was not fully observable. The same visible O/S/Z geometry could correspond to different hidden pivot/orientation states, so `screen + Rotate` was not always a deterministic function.

v2.1 replaces that reality with a fully observable visible-geometry rotation rule. BPC learns rotation from exact local 7x7 raw physical patterns. A 98-bit exact local address eliminates the final ~0.1% hash-collision error.

## Interpretation

The experiment supports the simpler decomposition:

```
local relation
-> translation reuse
-> multi-cell probability superposition
-> shared action carrier
-> channel coupling
-> local propagation
-> temporal recursion
-> fixed point
```

Hard Drop is not trained as a new long-distance rule; it is repeated reuse of the learned one-step-down function until closure.

This is not a claim of AGI or a fully self-growing pure-BPC core. Move / Rotate / Spawn / Clear curricula are still researcher-separated. The next target is to make those function families emerge inside one unified residual medium.
