# BPC Binary World-Fit v0.18–v0.20

Date: 2026-10-05
Goal: fit the complete controlled Tetris world from a black/white visible screen plus an external operation input, while removing researcher-provided Active/World semantics and moving screen/operation information toward one probability medium.

## v0.18 — binary screen + self-born temporal trace

External visible input is one binary frame:
- 10x20 board occupancy is one black/white plane (`Active OR World`);
- Preview is a visible 4x4 binary region placed at a fixed side-screen location;
- GameOver is one visible binary pixel.

No Active/World label is supplied at the external interface.

### Information-closure audit
A constructive counterexample produces:

`same black/white screen + same action -> different next black/white screen`

when different occupied subsets are the moving process. Result:

`SINGLE_FRAME_ALIAS same_input=1 same_next=0`

Therefore a single static black/white frame is not, in general, a Markov state for this world.

### Anonymous temporal trace
The missing process identity is born from temporal change rather than a semantic label. At episode birth, the trace seed is simply:

`newly appeared board bit = current_screen_bit AND NOT previous_screen_bit`

The trace is then carried forward by the learned world dynamics.

8-seed binary-screen rollout:

`312,839 / 312,839 = 100%`

Causal controls:
- `TRACE_OFF`: 3/203 = 1.477833%
- `TRACE_SHIFT`: 0/200 = 0%

Interpretation: the necessary distinction is process/history information, not an externally named Active channel.

## v0.19 — external operation becomes an anonymous carrier wave

The outer action dispatcher is removed from the binary world-model step. The external operation is encoded as an anonymous amplitude vector, and every carrier participates through the same:

`geometry -> consequence route -> action lifetime`

equations.

8-seed result remains:

`312,839 / 312,839 = 100%`

Causal control:

`ACTION_WAVE_SHIFT = 0/200`

Thus the physical operation encoding remains causal, but no special action if/switch dispatcher is needed.

## v0.20 — one shared probability medium

Geometry, Route, Life, Closure, Spawn and Spawn/GameOver split were previously stored in separate learned structures.

v0.20 compiles all learned probabilities into one shared probability field. Inference reads only this shared field; the original learned parameter structures are zeroed after export.

The external interface remains:

`0/1 screen + self-born temporal trace + anonymous operation carrier`

Shared-field entries: `140`.

8-seed result:

`312,839 / 312,839 = 100%`

Causal control:

`FIELD_OFF = 0/100`

Engineering audit:
- C11 `-Wall -Wextra -Werror -pedantic`: PASS
- O2/O3 full output diff: 0 bytes
- UBSan reduced smoke stderr: 0 bytes

SHA-256:
- v0.18: `a4a961ebbda89d1436376f26ca07b94ee31dee3174dcd470f56d8a253d613dd4`
- v0.19: `ae01895634439b0cf2daeb8c4f57cfe9e04e87fbdff2a7622814462e48b7424c`
- v0.20: `39cdf52ed68b96af0128cb78feeb4586745b6664a645067691dea61f41e432ba`

## Current scientific boundary

v0.20 unifies the learned storage/readout medium, but not yet the complete learning process. Family-specific observers still exist during training, and their results are exported into the shared field afterward.

Therefore v0.20 supports:

`different physical input encodings -> one probability medium -> exact world dynamics`

but does not yet support the stronger claim:

`one generic residual-write rule directly gives birth to every world function in that same field`.

That is the next target.