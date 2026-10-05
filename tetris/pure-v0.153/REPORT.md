# BPC Pure-Tetris v0.153 — Current Best Snapshot

Date: 2026-10-05
Status: current best Pareto snapshot in the Pure-BPC Tetris deletion line; near-Pure candidate, NOT final Pure BPC.

## Why this snapshot is selected

v0.153 (`continuous D2 superposition; measure only target voxels`) is selected rather than the numerically newer v0.154–v0.156 branches because it keeps the full integrated capability set while avoiding the known complexity blow-ups or rollout failures of later deletion attempts.

The selected source removes the hard D2 birth-energy threshold: cross-plane relation hypotheses participate continuously and discrete measurement is deferred to target voxels.

## Saved v0.153 result

Single-seed complete integration run:

- couplings = 388
- K_eff = 32.48
- step4/8/12/20 = 100%
- program4/8/12/20 = 100%
- deep12 = 100%
- LineClear = 100%
- arbitrary-row LineClear = 100%
- multiline 1/2/3/4 = 100%
- one-child k2/k4 = 100%
- closure-off single-line = 0%
- Spawn = 100%
- GameOver = 100%
- 20,000-tick free rollout = 20,000/20,000
- rollout: 445 locks, 420 spawns, 25 gameovers; this particular rollout happened to contain 0 line clears.

Causal ablations in the same snapshot:

- FIELD_OFF: high-order program collapses
- OVERFLOW_OFF: high-order program collapses
- RELATION_OFF: high-order program collapses
- REENTRY_OFF: one-step remains strong but high-order program collapses strongly
- CHANNEL_SCRAMBLE: collapses

## Evidence boundary

The complete v0.153 output above is one seed. It must not be reported as a completed 2-seed formal result.

Independent earlier experiments in the same deletion line established that the second anonymous-channel seed can learn the LineClear child after the rare reality is actually experienced: the second seed moved from an undetermined 0.5 child state after the first real LineClear to a stable `dy=+1` relation after the second real LineClear, after which arbitrary-row and 1/2/3/4-line tests closed. That is supporting evidence for the mechanism, not a substitute for a formal two-seed v0.153 rerun.

## What has already been removed

The current deletion line no longer relies on explicit model-side functions or labels named:

- Move / Rotate / Collision / HardDrop / Lock / LineClear / Spawn / GameOver
- piece type / pivot / shape template
- blocker module / row detector / clear_line()
- basis / phase slots / gauge slots
- fixed direction-role IDs
- determinant / matrix inverse relation solver
- whole-transform candidate search / Hamming winner search
- internal direction top-1
- object-level `any blocked -> whole object` carry gate
- global overflow process flag
- fixed four-neighbor carry flood path
- explicit ZERO_TARGET wave / zero-target birth threshold
- fixed D2 birth-energy threshold

The surviving core increasingly has the form:

`binary voxel/channel state + anonymous Action wave + continuous residual + generic coupling + relation-wave collision + universal binary carry/overflow + mass closure + address grounding + re-entry + local/synchronous relaxation`.

## Why it is not yet final Pure BPC

### 1. The model still has an explicit staged forward pipeline

The current model step is structurally ordered as approximately:

`base_model_step -> closure_relax -> mass_context_birth_relax`

These stages are generic rather than Tetris-named, but Pure BPC should ideally have one medium in which the same waves coexist and relax, instead of the program deciding which family runs first.

### 2. Cross-plane function birth still has handcrafted structural filters

The v0.153 source still contains:

- `mass_wave_equal_cross(...)`
- `cross_relation_coherence(...)`
- `address_anchor(...)` for cross-plane grounding

These have strong negative-ablation evidence: deleting mass conservation or shape coherence naively causes false function birth, K inflation, and/or rollout divergence. Therefore they cannot simply be removed, but they have not yet been fully derived from one generic residual law.

### 3. Input is still pre-separated into three bit planes

The model receives Active, World, and Preview as separate observable channels rather than a single raw pixel/voxel stream. Anonymous channel identity is information-theoretically useful, but the present interface still gives more structure than raw screen pixels.

### 4. Boundary/address topology is still provided

A one-hop address lattice, physical boundaries, and address-grounding propagation are model primitives. These may ultimately qualify as physical-medium laws, but that requires cross-domain invariance evidence; they are not yet proven to be the unique/minimal Pure-BPC substrate.

### 5. Closure has a dedicated generic physical process

LineClear is no longer represented as a row rule, but closure is still implemented through a dedicated boundary-carry/echo + relaxation mechanism. This is far cleaner than `clear_line()`, yet the final Pure formulation should ideally make closure another emergent stable wave interaction in the same field.

### 6. Formal robustness is not yet sufficient

Current complete v0.153 result is one seed. The chain has many independent two-seed and channel-swap controls, but the exact latest snapshot should still receive a multi-seed formal rerun before being called frozen Pure-BPC Tetris.

## Current scientific judgement

The project has crossed an important boundary:

`Tetris-specific function engineering -> mostly task-independent wave/carry/relation physics`.

It has NOT yet crossed the stronger boundary:

`task-independent physical medium -> all necessary cognitive/function structures emerge with no hardwired processing stages or structural birth filters`.

Therefore the accurate label is:

**Near-Pure BPC Tetris / strong Pure-BPC candidate, not final Pure BPC.**

## Next highest-value deletions

1. Collapse `base -> closure -> cross-plane` staged execution into one synchronous/recurrent wave field.
2. Replace `cross_relation_coherence` and cross-plane `address_anchor` with ordinary participating-wave residual credit without K explosion.
3. Test whether information-mass conservation can be expressed solely as ordinary binary carry/closure rather than a special eligibility check.
4. Make all visible information channels fully symmetric or move from pre-separated bit planes toward a raw visible voxel/pixel interface.
5. Run a formal multi-seed long-rollout freeze only after those changes.