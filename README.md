# GeneralBPC: Learned World + Learned Reversible Equivalence

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
reachability routine. It selected exact learned forward/inverse round trips as
the closest implementable BPC mechanism. Its response named `jev-1.13.0`; no
classifier output, remote model, or API call enters BPC training, evaluation,
or runtime. Candidate ranking guided development only; the committed frozen
test, causal control, and deterministic rerun provide the evidence.

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
python3 test_reversible_wave_v05.py
python3 experiment_v05_frozen.py
python3 render_v05.py
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
