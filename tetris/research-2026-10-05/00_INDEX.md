# BPC Tetris — 2026-10-05 Window Experiments

This directory preserves every experiment branch produced in the 2026-10-05 development window and separates **world fitting** from **operation fitting**.

## Research rule

The current priority is **fit the game first, then fit operation using the same BPC mechanism**. A higher score obtained by adding a separate policy/search/reward solution does not count as progress toward the target architecture.

## Branches

### `raw-visual-gamefit-v0.160-v0.161/`
Diagnostic bridge from Pure-Tetris v0.153 toward a visual interface.

- v0.160: one visible image + external action can bridge to the v0.153 world field.
- v0.160 two-seed: second seed exposes missing rare LineClear experience.
- v0.160b: destructive merge of observable identities into one binary plane fails completely; this is an information-loss negative control.
- v0.161: rare-event exposure shows the missing LineClear relation can be born, but naive repeated writes can destabilize it.

Status: evidence/history; **not** the current world-fit baseline.

### `world-then-play-v0.170-v0.172/`
First full 10×20 operation-learning diagnostic after freezing a fitted world.

- v0.170: Screen→Action held-out ≈81.75%, but autonomous play drifts.
- v0.171: write teacher operation on every visited state; short-term improvement followed by action-attractor collapse.
- v0.172: error-only Action-QEWB; delays pollution but does not close long-horizon play.

Status: operation branch paused until the game-fitting kernel becomes purer.

### `pure-gamefit-v0.180-v0.182/`
Pure-Tetris v0.153-based scaffold-deletion branch.

- v0.180: fixed `Active/World/Preview` semantic names removed; six anonymous visible-channel permutations all close.
- v0.181: deletes `mass_wave_equal_cross` and `cross_relation_coherence`; cross-channel function birth uses generic residual-reduction credit.
- v0.182: reverses downstream execution order and still closes, showing the researcher-chosen closure/cross ordering is not necessary.

Boundary: second world/action seed still exposes rare LineClear coverage failure. This branch is valuable purity evidence but is not chosen as the capability floor.

### `best-worldfit/`
Current selected world-fitting line.

The capability floor is Minimal v2.1's fully observable `visible state + action -> next state` world. Later proven purity mechanisms are backported only when the full regression remains exact.

- **v0.1**: removes the dedicated LineClear propagation function; row relocation reuses the learned Down function. 8-seed rollout remains 312,839/312,839 exact; 1–4 line stress 10,000/10,000.
- **v0.2**: deletes the learned three-bit `QGate`; Spawn and LineClear remain always eligible and jointly relax to a fixed point. Full 8-seed regression and LineClear stress remain 100%.

Status: **current baseline = Best World-Fit v0.2**.

## Current purity frontier

The next targets are to remove/merge the remaining duplicated execution vocabulary:

1. Move / Rotate / Spawn execution helpers -> one generic relation-propagation law;
2. row-carrier top-1 / detector -> simultaneous relation participation;
3. fixed semantic channel names -> anonymous observable information identity;
4. address grounding helpers -> ordinary address-wave relaxation;
5. keep the fully observable rotation world; do not reintroduce a supervised hidden pivot/latent target.

Every deletion must preserve the frozen regression suite before operation learning resumes.

### `binary-worldfit-v0.18-v0.20/`
Current strict world-fitting frontier after the black/white-screen correction.

- **v0.18**: external state is one 0/1 screen. A constructive alias proves one static binary frame is not always Markov; anonymous temporal trace born from frame change restores 8-seed 312,839/312,839 exact rollout. TRACE_OFF=1.48%, TRACE_SHIFT=0%.
- **v0.19**: external operation becomes an anonymous carrier wave; the world-model step has no action if/switch dispatcher. 312,839/312,839 remains exact; shifted action wave=0/200.
- **v0.20**: Geometry / Route / Life / Closure / Spawn / Split learned values are read from one shared probability medium (140 entries). The original separate learned structures are zeroed before inference. 312,839/312,839 remains exact; FIELD_OFF=0/100.

Current boundary: v0.20 unifies storage/readout, but family-specific training observers still exist before export into the shared field. The next target is direct generic residual writeback into this same field.

**Current world-fit frontier = Binary World-Fit v0.20.**
