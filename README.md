# GeneralBPC: Learned World + Relations + Macro Geometry

## v0.10 breakthrough: anonymous factor discovery without task names

One BPC learner now separates successful experience by the raw bit planes that
co-change on the terminal transition. It removes the plane shared by all
discovered factors, then activates factors from the remaining raw-plane
presence—without receiving `push`, `collect`, or another task-family label.

On 48 frozen, non-overlapping worlds and two new action seeds, automatic routing
matched a task-name oracle on all **342,139** routing decisions and completed
**4,284/6,144** 32-step episodes. Permuting the discovered raw-plane bindings
fell to **2,749/6,144**; the shared mixed-trace cube completed **3,962/6,144**.
See [`V10_AUTOFACTOR_RESULT.md`](V10_AUTOFACTOR_RESULT.md) and the
[`machine-readable result`](artifacts/v10autofactor/result.json).

![Frozen v0.10 result](artifacts/v10autofactor/poster_v10_autofactor.png)

Always activating both factors was slightly higher at `4,302/6,144`. The
supported advance is removal of task labels from factor discovery/routing, not
a routing performance gain. Equal probability multiplication and terminal
success events remain supplied; this is not autonomous operator invention or
AGI.

## v0.9 breakthrough: direct task composition without joint training

Two independent BPC policies learn from `2,000` push-only and `2,000`
collect-only episodes. Their four-way probabilities are multiplied equally at
inference, then sampled directly—no runtime planner, search, joint-task
training, or evaluation writes.

All 16 frozen worlds require pushing: they become unsolvable if boxes are held
fixed. Under a 32-step budget:

| Frozen condition | Successes | Rate |
|---|---:|---:|
| Independent probability product | **942 / 2,048** | **46.0%** |
| Collect-only specialist | 830 / 2,048 | 40.5% |
| Shared mixed-experience cube | 610 / 2,048 | 29.8% |
| Uniform random | 235 / 2,048 | 11.5% |
| Rotated learned actions | 71 / 2,048 | 3.5% |

Every new world had a successful direct-control trace. See
[`V09_DIRECT_RESULT.md`](V09_DIRECT_RESULT.md) and the machine-readable
[`v0.9 result`](artifacts/v09direct/result.json).

![Frozen v0.9 result](artifacts/v09direct/poster_v09_direct.png)

**[Watch all 16 frozen direct-control traces](https://github.com/JoffeeLin/bpc-sokoban-demo/releases/download/v9.0.0/bpc_direct_composition_v09_16_worlds.mp4)**

**[View the v0.9 result and video on X](https://x.com/JoffeeLin/status/2101700819158732821)**

The equal probability product is supplied, not autonomously invented. This is
bounded synthetic cross-task control—not arbitrary planning or AGI.

## v0.8 bridge: exact 64-step cross-task rollout

Before direct control, the v0.7 world function was recursively rolled forward
without teacher forcing. Across two new seeds it completed **6,000/6,000**
64-step trajectories exactly; all `1,681/1,681` trajectories that encountered
joint mechanisms remained exact, versus `1,081/1,681` for condition deletion
and `0/1,681` known by full-context memory. See
[`V08_ROLLOUT_RESULT.md`](V08_ROLLOUT_RESULT.md).

This is open-loop prediction under supplied actions, not planning.

## v0.7 breakthrough: two learned world functions compose

v0.7 trains on two disjoint streams—`150,000` push-only transitions and
`150,000` collect-only transitions—with **zero** local contexts containing both
an object and a mark. Its anonymous fragment chain then predicts two frozen
combined-world seeds exactly:

| Frozen condition | Never-trained joint transitions |
|---|---:|
| Learned fragment chain | **3,795 / 3,795** |
| Condition deletion only | 2,478 / 3,795 |
| Full-context memory known | **0 / 3,795** |

Both old families remained `60,000 / 60,000`, the first holdout repeated
bit-for-bit, and evaluation performed zero model writes. See
[`V07_CROSS_RESULT.md`](V07_CROSS_RESULT.md) and the machine-readable
[`v0.7 result`](artifacts/v07cross/result.json).

![Frozen v0.7 result](artifacts/v07cross/poster_v07_cross.png)

**[Watch all ten frozen joint transition classes](https://github.com/JoffeeLin/bpc-sokoban-demo/releases/download/v7.0.0/bpc_cross_task_v07_10_joint_classes.mp4)**

**[View the v0.7 video on X](https://x.com/JoffeeLin/status/2101692758604079216)**

The supported claim is exact local one-step world-function composition in a
supplied synthetic generator—not planning, a direct policy, or AGI.

## v0.6.1 breakthrough: supplied macro geometry removed

v0.6 learns anonymous push-delta templates from random interaction and uses
them instead of hand-written box-behind/player-behind geometry. Its macro
solver contains no supplied `ACTIONS`, `action ^ 1`, or `moved()` call.

| Frozen condition | Push-template audit | New maps |
|---|---:|---:|
| Learned anonymous geometry | **1,443 / 1,443** | **8 / 8** |
| Rotate templates, same experience | **0 / 1,443** | **0 / 8** |

All solutions replayed under true physics, both new four-box maps passed, and
evaluation performed zero model writes. The original v0.6 runner failed on a
tuple/list serialization assertion before touching the holdout; that failure
is preserved, and v0.6.1 changes only canonical JSON comparison. See
[V061_RESULT.md](V061_RESULT.md) and the machine-readable
[v0.6.1 result](artifacts/v061/result.json).

![Frozen v0.6 result](artifacts/v061/poster_v06.png)

**[Watch all eight frozen holdout replays](https://github.com/JoffeeLin/bpc-sokoban-demo/releases/download/v6.0.0/bpc_learned_geometry_v06_8_unseen.mp4)**

The remaining local action-relative addressing, terminal seeding,
equivalence-class choice, and backward wave are supplied. This is another
hybrid mechanism advance—not cross-task general intelligence or AGI.

## v0.5 breakthrough: supplied reachability removed

v0.5 discovers four inverse action relations from exact round-trip experience,
then uses learned reversible orbits instead of v0.4's hand-written free-space
flood fill. The inverse learner sees only anonymous action indices and exact
before/after microstates; it is not given direction names or inverse pairs.

| Frozen condition | Reach equivalence | New maps |
|---|---:|---:|
| Learned inverse relations | **4,000 / 4,000** | **8 / 8** |
| Wrong inverse, same experience | 7 / 4,000 | **0 / 8** |

The old supplied `reach()` function was deliberately replaced by an exception
before holdout solving. Both unseen four-box maps passed, every sequence replayed
under true physics, and evaluation performed zero model writes. See
[V05_RESULT.md](V05_RESULT.md) and the machine-readable
[v0.5 result](artifacts/v05/result.json).

![Frozen v0.5 result](artifacts/v05/poster_v05.png)

**[Watch all eight frozen holdout replays](https://github.com/JoffeeLin/bpc-sokoban-demo/releases/download/v5.0.0/bpc_reversible_equivalence_v05_8_unseen.mp4)**

**[View the v0.5 video on X](https://x.com/JoffeeLin/status/2101683972887707777)**

The remaining action-displacement interface, macro push-candidate enumeration,
terminal seeding, and backward wave are still supplied. This is a second hybrid
mechanism advance—not direct policy control, autonomous solver discovery,
cross-task general intelligence, or AGI.

## v0.4 breakthrough: one supplied world law removed

The new v0.4 branch restores the historical function-compressed configuration
wave, then replaces its hand-written push-validity decision with a **48-row
local transition probability cube learned only from 240,000 random raw game
transitions**.

In a pre-registered developer-frozen test:

| Frozen condition | Local transitions | Unseen maps |
|---|---:|---:|
| Learned three-cell `F_world` | **40,000 / 40,000** | **12 / 12** |
| Remove the third cell | **0 / 688 push transitions** | **0 / 12** |

All three unseen four-box maps passed even though learning experience contained
only one to three boxes. Every emitted action sequence was replayed through the
true environment, and frozen evaluation performed zero model writes. See
[V04_RESULT.md](V04_RESULT.md) and the machine-readable
[v0.4 result](artifacts/v04/result.json).

![Frozen v0.4 result](artifacts/v04/poster_v04.png)

**[Watch all 12 frozen holdout replays](https://github.com/JoffeeLin/bpc-sokoban-demo/releases/download/v4.0.0/bpc_learned_world_v04_12_unseen.mp4)**

The remaining reachability compression, macro candidate geometry, terminal
seeding, backward wave, and raw channels are still supplied. This is a hybrid
mechanism advance—not a pure direct policy, autonomous solver discovery,
cross-task general intelligence, or AGI.

## v7 direct-control result

One non-neural probability-cube controller learned from other layouts and then
directly controlled **10 structurally different, unseen Sokoban levels**. The
developer-frozen v7 result passed every pre-registered gate:

| Frozen condition | Successes | Rate |
|---|---:|---:|
| GeneralBPC v7 | **1098 / 2560** | **42.9%** |
| Remove joint relations | 652 / 2560 | 25.5% |
| Force frame-change fusion | 1077 / 2560 | 42.1% |
| Rotate learned action channels | 198 / 2560 | 7.7% |
| Uniform random | 389 / 2560 | 15.2% |

All ten unseen layouts had successful frozen episodes (`18–256 / 256` each),
and evaluation performed zero learned-state writes. See
[V7_RESULT.md](V7_RESULT.md) and the machine-readable
[result](artifacts/v7/result.json).

![Frozen v7 result](artifacts/v7/poster_v7.png)

**[Watch all 10 first-success traces](https://github.com/JoffeeLin/bpc-sokoban-demo/releases/download/v3.0.0/bpc_sokoban_v7_10_unseen_levels.mp4)**

**[View the published video on X](https://x.com/JoffeeLin/status/2101668685396230408)**

## What the model sees

- Raw `9×9×6` binary voxels derived from the visible board.
- Four anonymous external action indices.
- No coordinates, object labels, Sokoban rules, route, runtime solver/search,
  neural network, mirror mapping, or evaluation-time learning.

An offline solver only rejects unsolvable maps and fixes a shortest-distance
range. It never returns solution actions to training or inference.

## Mechanism

The encoder discovers low-frequency raw voxel groups by occurrence count, then
emits translation-shared raw identities, directed pair offsets, anonymous joint
geometry, nearby matter, and relation×matter conjunctions. A sparse BPC stores
exact Dirichlet/Beta counts. Successful real paths write action counts back to
the relations that participated; the frozen controller samples a four-way
probability distribution directly.

Training uses a separate high-order BPC only as a behavior policy to collect
experience. The released controller never contains or queries those high-order
features. Removing its joint relation families drops the frozen result by
`17.4` percentage points.

## Jev and classifier.dev influence

The interface borrows two ideas from Jev-style typed decisions: return the full
fixed-choice probability distribution, and keep narrow probabilistic questions
independent. The model exposes a separate `P(raw frame changes | relation,
action)` channel and normalized entropy confidence. Development evidence said
that forcing this channel into action choice hurt, so it remains observable but
is not part of the adopted controller.

The `classifier.dev` skill first triaged 18 de-identified summaries of earlier
BPC mechanisms, then classified 12 candidate replacements for v0.4's supplied
reachability routine and 16 candidates for the next scaffold. It selected
exact learned forward/inverse round trips for v0.5 and ranked learned macro
push deltas as a high-leverage implementable v0.6 experiment. Its response
named `jev-1.13.0`; no classifier output, remote model, or API call enters BPC
training, evaluation, or runtime. Candidate ranking guided development only;
the committed frozen tests, causal controls, and deterministic reruns provide
the evidence.

## Task-agnostic kernel

[`bpc_general_kernel.py`](bpc_general_kernel.py) extracts the reusable part:
variable action count, anonymous feature families, exact probability channels,
confidence, and optional defer. It has no game rules or semantic labels. Its
unit tests cover relation transfer to an unseen identity, channel separation,
and uncertainty deferral:

```bash
python3 -m unittest -v test_general_kernel.py
```

This is a reusable BPC decision kernel, **not evidence of general intelligence**.
Cross-task frozen transfer remains future work.

## Reproduce

Requirements: Python 3.11+, Pillow 12, and `ffmpeg` on `PATH`.

```bash
python3 -m pip install -r requirements.txt
python3 test_learned_geometry_v06.py
python3 experiment_v061_frozen.py
python3 render_v06.py
python3 experiment_v07_cross_frozen.py
python3 render_v07_cross.py
python3 experiment_v08_rollout_frozen.py
python3 experiment_v09_direct_frozen.py
python3 render_v09_direct.py
```

The committed protocol and holdout refuse silent source changes by verifying
their SHA-256 hashes. Generated model and MP4 files are ignored by Git; the MP4
is attached to the GitHub release.

## Evidence boundary

This supports limited cross-layout transfer inside one fixed `9×9`, single-box
distribution. It is a developer-frozen local holdout, not an independent blind
test. It does not establish arbitrary Sokoban, autonomous representation
discovery, cross-task generality, or AGI.

Older failed baselines and v5 evidence remain in the repository for provenance.

## License

MIT
