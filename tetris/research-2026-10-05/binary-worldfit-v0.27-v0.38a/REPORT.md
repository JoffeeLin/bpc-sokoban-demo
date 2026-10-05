# BPC Binary World-Fit v0.27–v0.38a — Purity Reduction Report

Date: 2026-10-05

## Goal

Continue the strict world-fitting route:

`0/1 visible screen + external operation -> same BPC medium -> next 0/1 visible screen`

The purpose is not to increase Tetris score. The purpose is to remove researcher-provided function categories, special observers, and procedural rules while preserving exact world dynamics.

## Stable capability floor

All promoted checkpoints are compared against the frozen Binary World-Fit regression:

- 8 independent rollout seeds: 312,839 / 312,839 ticks exact;
- 1/2/3/4-line stress: 10,000 / 10,000;
- vertical through-board non-clear: 2,500 / 2,500;
- no handwritten occupied/outside collision decision;
- no clear_line / row detector / hole propagation / distance-specific clear table / whole-chain closure scanner.

## v0.27 — remove function-family namespace (positive)

The field no longer receives keys such as `K_GAUGE`, `K_ROUTE`, `K_LIFE`, `K_SPAWN`, or `K_CLOSURE` as function-family namespaces.

A learned address is instead formed by collisions among primitive participating waves, e.g.:

- Action wave × spatial relation;
- Action wave × feasibility wave × route wave;
- proposal wave × destination-state wave;
- boundary wave × local relation;
- address-relation wave × effect wave.

Formal result: 8-seed rollout remains 312,839 / 312,839; clear stress remains 100%.

Interpretation: function-family names are not required as storage namespaces.

## v0.28 / v0.28b — Action lifetime from visible trajectory residual

v0.28 first attempted to remove the dedicated Action-lifetime observer and failed (~70% long-rollout exactness). The failure showed that comparing the wrong temporal scale gives incorrect persistence credit.

v0.28b changed the credit to compare a one-micro model consequence with the real full visible transition. The remaining residual directly teaches whether the Action carrier must re-enter.

Result: clear stress 100%; first two formal seeds exact. The same mechanism was retained in later fully frozen checkpoints.

Interpretation: Action lifetime can be learned from visible temporal consequence rather than a named HardDrop rule.

## v0.29 — route credit from real visible transition (positive)

The old micro-route target was replaced with competing consequence hypotheses on ordinary real transitions. Candidate move / persistence / world-write consequences are applied, and only hypotheses that explain the real next state receive credit.

Effect-equivalent routes share the same participating spatial-effect wave rather than relying only on Action ID.

Result: all 8 frozen seeds exact; clear stress exact; smoke/engineering checks pass.

## v0.30 / v0.30b — Spawn relation born from ordinary visible trajectory (positive)

The dedicated one-cell Preview->Active spawn curriculum was removed. Candidate cross-region displacement relations are proposed from ordinary game transitions and credited only when they reconstruct the real newly visible active pattern.

v0.30 was a pilot. v0.30b used 12,000 ordinary visible transitions.

Frozen evaluation of v0.30b:

- seed0..7: all exact;
- 8-seed total remains 312,839 / 312,839;
- clear stress remains exact.

The learned sparse Spawn relation remains a single reusable cross-region displacement.

## v0.31 — Closure from ordinary visible residual, first attempt (negative)

Special closure micro-training was removed. The learner compared a model-produced pre-downstream mid-state with the real final visible state.

Result:

- vertical negative: 100%;
- clear stress: 0 / 10,000.

Cause: local output labels inferred from final pixel occupancy are ambiguous. A pixel that remains `1` may be the same information instance or a different instance shifted into the same address.

This is an information-instance / credit-assignment problem, not missing Tetris rules.

## v0.32 — global residual-reduction credit (partial)

Each closure-address effect was applied as a hypothesis and credited by how much it reduced whole-world residual.

Result:

- single-line: 2,500 / 2,500;
- double/triple/tetris: 0;
- ordinary rollout seeds remained exact.

The learner gave positive credit both to `down` and `gone` for `closure below`; repeated closures therefore caused destructive interference.

## v0.32b — direct competition between consequence effects (negative)

Alternative effects were made to compete through residual explanation.

Result: clear stress 0 / 10,000.

Conclusion: high-order consequences cannot be forced into mutually-exclusive first-order effects when several functions must jointly explain one reality transition.

## v0.33 — atomic death + birth factorization (partial)

`persist/down/gone` was replaced by two lower-level effects:

- source death;
- +1 destination birth.

Thus movement can emerge as `death + birth`, disappearance as `death`, and persistence as no effect.

The correct atomic amplitudes were learned for single closure contexts, but multi-line stress remained 25% (only single-line exact).

Diagnosis: a voxel in a cleared row can simultaneously participate in `same closure` and `closure below`. A higher-order relation-of-relations is required to suppress transfer when the source itself belongs to a closure.

## v0.34 — first relation-of-relation attempt (negative diagnostic)

A generic high-order key was introduced as a collision of:

`address relation A × address relation B × existing effect`

Training used external autoplay transitions, but the model compared the real macro transition against only a one-micro model mid-state. No pair credit was born (`pair gate = 1.0`).

Conclusion: credit must operate at the same temporal depth as the real Action consequence.

## v0.35 — macro-time relation-of-relation residual (PROMOTED)

The already learned Action lifetime is reused to recurrently produce the model state immediately before downstream world relations. No Lock label is supplied; the same Action carrier simply re-enters until its learned lifetime dies.

External autoplay then supplies ordinary real `Screen + Action -> Screen` experiences. When two existing address relations coexist, forcing an existing effect open vs closed is compared against the real final screen; residual difference writes a high-order coupling.

Learned:

`pair(same-address, closure-below) × +1-birth gate = 0.020408`

This suppresses the false re-birth of information that itself belongs to a cleared closure while another closure also exists below it.

Formal frozen result:

- clear stress: 10,000 / 10,000;
- vertical non-clear: 2,500 / 2,500;
- seed0..7: 312,839 / 312,839 exact;
- every evaluation: `FIELD_UNCHANGED=1`.

Causal control:

- learned pair gate 0.020408 -> clear stress 10,000 / 10,000;
- forcibly opening the pair gate to 0.999999 -> 2,500 / 10,000, only single-line survives.

Engineering:

- O2/O3 frozen inference diff: 0 bytes;
- UBSan smoke stderr: 0 bytes.

Interpretation: a genuine relation-of-relation function can be born from visible gameplay residual and is causally necessary for multi-line composition.

## v0.36 — remove dedicated Closure event curriculum using ordinary slow-play (negative/partial)

The external player still chooses placements, but the final descent is emitted as repeated ordinary `Down` operations. Training data are therefore only one-step visible `Screen + Operation -> Screen` transitions; no forced-clear state generator is used.

Two ordinary-play passes produced hundreds of real residual/clear events and learned the high-order pair gate.

Result:

- double/triple/tetris: 100%;
- single-line: 0%;
- total clear stress: 7,500 / 10,000;
- normal rollout seeds tested remained exact.

The basic same-address death function was mis-credited in dense natural boards.

## v0.37 — joint function-combination residual credit (negative/partial)

Instead of independent marginal `death` and `birth`, the learner allowed three effect waves to compete continuously:

- death;
- birth;
- death × birth.

This correctly learned `death×birth` for the closure-below relation, but natural dense transitions still mis-assigned the same-address effect. Result remained 7,500 / 10,000 (single-line failed).

Scientific boundary exposed by v0.36/v0.37:

> In a binary occupancy screen, after a line shift the fact that a pixel is still `1` does not reveal whether the same information instance persisted or another instance moved into that address. Natural dense trajectories therefore contain an information-instance correspondence ambiguity that cannot always be resolved from final bit values alone by naive residual attribution.

The next pure route should introduce/reuse an anonymous self-born information-instance continuity trace, not restore a LineClear rule.

## v0.38a — Spawn/GameOver split from ordinary visible transitions (PROMOTED)

Returning to the stable v0.35 closure checkpoint, the synthetic Spawn/GameOver split curriculum was removed.

From 12,000 ordinary real transitions, the learner silently accepted only transitions for which one of the ordinary spawn consequence hypotheses exactly explained the visible final Active+GameOver state. No event label was supplied.

Observed credit:

- credited transitions: 3,831;
- direct spawn consequences: 3,522;
- terminal/complement consequences: 309.

Learned split:

- feasible `C=1`: direct = 0.999716, complement = 0.000284;
- blocked `C=0`: direct = 0.003215, complement = 0.996785.

Frozen formal result:

- clear stress: 10,000 / 10,000;
- vertical negative: 2,500 / 2,500;
- seed0..7: 312,839 / 312,839 exact;
- every seed: `FIELD_UNCHANGED=1`.

Engineering:

- O2/O3 frozen inference diff: 0 bytes;
- UBSan smoke stderr: 0 bytes.

## Current promoted checkpoint

**Binary World-Fit v0.38a**

Current stable description:

`0/1 visible screen`
`+ self-born temporal process trace`
`+ anonymous external operation carrier`
`-> one shared probability field with no function-family namespace`
`-> reality-born spatial/effect relations`
`-> learned proposal x destination-state interference`
`-> visible-transition consequence routes`
`-> visible-trajectory Action lifetime`
`-> ordinary-trajectory Spawn relation`
`-> ordinary-trajectory Spawn/GameOver split`
`-> opposite-boundary local-wave interference`
`-> closure/address function coupling`
`-> autoplay-born relation-of-relation coupling`
`-> next 0/1 visible screen`

## Remaining major purity scaffolds

1. The base closure atomic functions are still bootstrapped by a forced-event observer in the promoted checkpoint. v0.36/v0.37 show why naive removal fails: information-instance correspondence becomes ambiguous in dense natural binary transitions.
2. Geometry is still bootstrapped from a 1/2/3-voxel micro curriculum and uses a dedicated geometric observer.
3. proposal/destination compatibility still uses a dedicated micro observer, although the learned relation itself is shared by move/rotation/spawn.
4. The binary screen is internally decomposed into transient vs persistent arrays using a self-born temporal trace; the trace is causal, but the execution representation is still structurally separated.
5. Stable v0.38a still gates downstream relaxation on lock amplitude; v0.26 showed scheduler-free participation is plausible but computationally expensive and not formally frozen.
6. Physical address/lattice topology and the physical Preview screen region remain substrate assumptions.

## Next target

Do not restore LineClear labels or rules. The next high-value experiment is an anonymous information-instance continuity/provenance wave that is born from temporal relations and lets ordinary dense gameplay assign residual credit to source/destination instances without semantic Active/World identities. This should be tested specifically on removing the remaining forced closure bootstrap while preserving v0.38a's full regression.