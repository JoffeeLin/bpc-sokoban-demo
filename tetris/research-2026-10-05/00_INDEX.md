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


### `binary-worldfit-v0.21-v0.26/`
Direct shared-field learning and removal of handwritten collision / clear propagation.

- **v0.21** negative: direct Beta writeback in one field failed because tiny smoothed probabilities survived recurrently.
- **v0.21b** positive: one centered binary amplitude `max(0,2P-1)` restores the full 312,839/312,839 rollout.
- **v0.22** positive: deletes handwritten occupied/outside collision decisions; proposal × destination-state compatibility is learned in the shared field and reused by movement/rotation/spawn.
- **v0.23** negative stress: deletes hole propagation but still memorizes closure consequence by exact distance; 1–4 line stress only 3.61%.
- **v0.24** positive: compresses distance to generic address relations (same / closure below / closure above); 1–4 line stress 10,000/10,000 and 8-seed rollout exact.
- **v0.25** negative: one-sided boundary wave contaminates closure seeds.
- **v0.25b** positive/current stable checkpoint: opposite-boundary local waves must interfere; no whole-chain scanner. 1–4 line stress 10,000/10,000, vertical negative 2,500/2,500, 8-seed rollout 312,839/312,839, O2/O3 diff 0, UBSan clean.
- **v0.26** pilot: removes lock-triggered downstream scheduling and preserves capability, but computational cost increases substantially; not yet promoted.

**Current stable world-fit frontier = Binary World-Fit v0.25b.**


### `autoplay-verification-v0.25b/`
Independent external autoplayer verification of the frozen Binary World-Fit v0.25b checkpoint.

The external player searches rotations/horizontal placements and deliberately clears lines; its heuristic/search state is never passed to BPC. The exact same selected operations are sent independently to the real environment and frozen BPC world model.

Formal result across five 1000-piece streams:
- 5,000 placed pieces;
- 22,199 actions;
- 1,652 real clear events / 1,880 lines cleared;
- 9 four-line clears;
- visible-frame exact = **22,199 / 22,199**;
- temporal-trace diagnostic exact = **22,199 / 22,199**;
- BPC divergence = **0**;
- frozen SharedField byte-identical before/after evaluation.

Controls: FIELD_OFF and ACTION_SHIFT both diverge on the first action. O2/O3 output diff = 0 bytes; UBSan smoke stderr = 0 bytes.

Interpretation: strong evidence that v0.25b fits the tested controlled Tetris dynamics under goal-directed line-clearing trajectories. This does not claim BPC has learned to play; the player is external.


### `binary-worldfit-v0.39-v0.40b/`
Latest visible-trajectory scaffold deletion.

- **v0.39**: Spawn/GameOver split final credit comes from ordinary visible lock transitions; frozen 8-seed regression remains 312,839/312,839 exact.
- **v0.40/v0.40b**: dedicated single-cell compatibility micro curriculum is removed from final credit. Proposal/destination compatibility is learned from ordinary visible gameplay; v0.40b uses product-responsibility credit and freezes at empty=0.999746, occupied=0.000333, boundary=0.000187.
- **v0.40b formal**: clear stress 10,000/10,000; vertical non-clear 2,500/2,500; seed0..7 = 312,839/312,839; O2/O3 diff 0 bytes; UBSan stderr 0 bytes.

**Current promoted world-fit checkpoint = Binary World-Fit v0.40b.**
Remaining high-value scaffolds are geometry micro curriculum/observer, transient-vs-persistent internal execution split, separate execution helpers, lock-triggered downstream scheduling, staged training orchestration, and physical lattice/Preview-region substrate assumptions.


### `binary-worldfit-v0.27-v0.40/`
Purity-compression continuation from the black/white world-fit line.

Key promoted results:
- v0.27 removes function-family namespaces from SharedField addresses.
- v0.28b learns Action lifetime from ordinary visible trajectories.
- v0.29 learns route consequences from visible-transition residuals.
- v0.30b learns Spawn displacement from ordinary visible transitions.
- v0.38 solves closure credit using whole-world leave-one-coupling-out residuals from ordinary play only; clear stress 10,000/10,000 and 8-seed rollout 312,839/312,839.
- v0.39 relearns Spawn/GameOver split only from ordinary lock transitions; no dedicated blocked/unblocked Spawn curriculum; full regression remains exact.
- v0.40 relearns empty/occupied/boundary compatibility only from ordinary visible game transitions by global ON/OFF counterfactual residual credit; no dedicated collision micro-curriculum; full regression remains exact.

Negative results v0.28, v0.31, v0.32b and v0.25/v0.23 predecessors are retained because they identify credit-assignment and temporal-scale failure modes.

**Current stable world-fit frontier = Binary World-Fit v0.40.**

Largest remaining dedicated curriculum: geometry gauge/basis/phase still begins from researcher-designed 1/2/3-voxel micro-experience. Next target is to learn geometry from ordinary 4-cell game transitions only.


### `binary-worldfit-v0.41-v0.43/`
Latest scheduler/geometry scaffold audit.

- **v0.41**: scheduler-free carrier participation is pilot-positive (clear 2,000/2,000; seed0 11,812/11,812) but not fully frozen.
- **v0.42**: removes the 1/2/3-voxel geometry curriculum; ordinary visible play recovers gauges/basis, but phase ambiguity prevents downstream credit. Negative.
- **v0.42b**: relation-preserving visible transitions recover translation geometry and compatibility; clear stress returns 2,000/2,000, but rotation chirality remains ambiguous and rollout is ~85%. Partial, not promoted.
- **v0.43**: two-step same-function reentry cannot resolve 90-degree chirality and collapses. Negative.

**Current promoted checkpoint remains v0.40b.** Next geometry route is local one-hop relation-wave relaxation (Pure-Tetris v0.39 mechanism), not further global gauge/basis/phase patching.
