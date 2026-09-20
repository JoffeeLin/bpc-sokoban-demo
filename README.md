# GeneralBPC: Frozen Cross-Layout Sokoban

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

The `classifier.dev` skill was used only to triage 18 de-identified summaries of
earlier BPC mechanisms. Its response named `jev-1.13.0`; no classifier output,
remote model, or API call enters BPC training, evaluation, or runtime. The first
batch also demonstrated why confidence is not proof of task fit: ambiguous label
wording misclassified a positive transfer result, so all low-confidence or
contradictory items were manually reviewed.

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
python3 experiment_v7_frozen.py
python3 render_v7.py
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
