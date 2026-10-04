# BPC Tetris Minimal v3.9 — Action-wave / Raw-route / Pair-rotation frozen report

Date: 2026-10-04

## Sequence

v3.3 removed the action if/switch dispatcher. An initial rare DROP failure exposed accumulated false lock probability (about 3.4%–7.5% per non-lock microstep). No new mechanism was added: repeating the same 3x3 Move/split reality matured the probabilities. Five independent world/hash pairs then reached **15,560/15,560 ticks exact**. A cyclic action-wave shift ablation produced **0/20** exact ticks.

v3.4 removed the five candidate-State bank. There is one evolving Active/Pivot/World state and action relations write directly into the same probability field. Five frozen pairs: **7,729/7,729**.

v3.5 removed the handwritten distinction "side/rotate blocked -> stay" versus "down/drop blocked -> lock". Raw micro-reality writes the action consequence into the same field.

v3.6 removed separate one-shot and DROP-persist inference variables. Every action is only a continuous carrier whose next-step lifetime is predicted by the field. Five frozen pairs: **7,729/7,729**.

v3.7 stopped directly teaching "DROP continues". External reality produces the final macro consequence; if one micro-consequence still differs from the real final state, the remaining residual teaches continuation. Five frozen pairs: **7,729/7,729**.

v3.8 removed abstract MOVE/STAY/LOCK outcome slots. Feasible motion is simply physical feasibility multiplied by the learned spatial proposal. Blocked consequences are raw channel routes: Active->Active or Active->World. Action lifetime is an Action->Action self relation. Five frozen pairs: **7,729/7,729**.

v3.9 removed pivot-specific rotation inference. Rotation is now a generic pair relation:

`Active cell × anonymous latent anchor -> destination Active cell`

No learned-rotation call to `pivot_xy()` is required and no dedicated local rotation inference grid is constructed. The latent anchor's own behavior under ROT is a normal Latent->Latent relation.

Five frozen world/hash pairs: **7,729/7,729 ticks exact**.

## Causal boundary

The current external rotation engine is not Markov from one visible frame alone. Zeroing the anonymous latent history immediately before ROT reduces visible rotation exactness from **100% to 31.88%** over 5,000 trials.

Therefore the semantic object "pivot" is not required, but some history/process state is causally necessary under this external world.

## Current compressed form

`raw visible state + external action wave -> one shared probability field -> generic spatial/pair relations -> raw-channel residual routes -> recurrent action-carrier dynamics -> fixed-point closure`

## Next wall

The anonymous history plane is still born from a supervised Spawn->latent target during curriculum construction. The next experiment should remove that target and let true ROT residual write back into all participating latent traces. No top-1 anchor search, no object/type labels.

## Verification

- C11 -Wall -Wextra -Werror: PASS
- O2/O3 representative output: byte-identical
- UBSan stderr: 0 bytes
- frozen evaluation writes: zero
