# BPC Sokoban: Diverse-Level Frozen Test

A one-file Python experiment testing whether one Binary Probability Cube (BPC) memory can directly control ten structurally different 9×9 Sokoban layouts. Five levels are used for training and five independent layouts are held out until frozen evaluation.

![Frozen BPC fails held-out level 10](artifacts/poster.png)

**[Watch the 49-second result video](https://github.com/JoffeeLin/bpc-sokoban-demo/releases/download/v2.0.0/bpc_sokoban_10_levels.mp4)**

## Result: not adopted

| Condition | Result |
|---|---:|
| Training layouts | Levels 1, 3, 5, 7, 9 |
| Frozen replay on training layouts | 32/32 on every level |
| Independent unseen layouts | Levels 2, 4, 6, 8, 10 |
| Frozen replay on unseen layouts | 0/32 on every level; 0/160 total |
| Untrained control | 0/320 |
| Persistent writes during evaluation | 0 |

The model memorized the five training layouts but did not form a transferable direct policy. This negative result is retained rather than replacing the held-out layouts with rotations or mirrors.

## Input and restrictions

The model receives a raw 9×9 RGB frame quantized to the two high bits of every channel (486 binary bits) and four anonymous action indices. It receives no coordinates, object labels, route, search tree, Sokoban rules, handcrafted policy, neural network, mirror/rotation canonicalization, or evaluation-time learning.

The ten layouts have different wall sets, player starts, box starts, goals, and shortest routes. A solver was used only offline to confirm each literal level is solvable; it is not included in the BPC, training, evaluation, or video runtime.

The maximum pairwise Jaccard overlap between internal-wall sets is `0.267`, and all ten `(player, box, goal)` triples are unique.

## Mechanism

`BPC` is a sparse `raw frame × action × outcome` probability cube. Each cell holds exact Beta(1,1) Bernoulli counts for:

1. `P(terminal success | raw frame, action)`
2. `P(frame changes | raw frame, action)`

The action with the largest direct product is executed. Training uses reproducible uniform random exploration. The frozen model performs no persistent writes.

Because an unseen full frame has no matching memory cell, all four actions retain the same prior probability; deterministic tie-breaking repeatedly chooses `UP`. That is the observed failure mechanism.

## Run

Requirements: Python 3.11+, Pillow 12, and `ffmpeg` on `PATH`.

```bash
python3 -m pip install -r requirements.txt
python3 bpc_sokoban.py train
python3 bpc_sokoban.py test
python3 bpc_sokoban.py record
```

Outputs:

- `artifacts/result.json` — raw frozen result, controls, scope, and model hash
- `artifacts/model.pkl` — generated model (ignored by Git)
- `artifacts/bpc_sokoban_10_levels.mp4` — generated result video (release asset)
- `artifacts/poster.png` — final held-out failure frame

## Evidence boundary

This is a development result, not a frozen blind result. It provides evidence against cross-layout generalization for this exact full-frame BPC memory. It does not prove every possible BPC representation must fail, and it is not evidence for AGI.

## License

MIT
