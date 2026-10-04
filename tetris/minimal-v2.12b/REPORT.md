# BPC Tetris Minimal v2.12b — Sparse Function Field + Multi-Phase Interference

Date: 2026-10-04

## Result

This version continues the minimal-function route rather than full-frame fitting.

The learned closure has been compressed to approximately **34 sparse positive physical effects** stored in **one shared Beta field**.

Redundant relations were removed:

- Row propagation is no longer learned separately; Line Clear reuses the already learned Down function.
- Lock and Spawn reuse one anonymous two-channel split function.
- The separate row CellWave is removed; row carrier cells reuse that same split.
- Spawn Active is no longer a 16x200 table; it is one translation-equivariant Preview->Active displacement function.
- Unseen relations have zero effect instead of requiring explicit negative storage.

A single hash phase creates false-positive relations when an unseen query aliases a learned positive address. v2.12b therefore uses three independent address phases inside the same shared field and the continuous pairwise-agreement readout:

`q = p1*p2 + p1*p3 + p2*p3 - 2*p1*p2*p3`

There is no top-1 path selection.

## Robust capacity frontier

Five address salts:

- 2^12 cells: unstable, **0% .. 99.05%**
- 2^13 cells: **5/5 = 100%**
- 2^14 cells: **5/5 = 100%**

The adopted tested frontier is therefore **8192 shared field cells**.

## Cross-seed reproduction

At 2^13:

- 3 independent address salts
- 3 independent rollout seeds
- 9 frozen combinations
- total compared ticks: **75,369**
- exact: **75,369 / 75,369 = 100%**
- Left / Right / Down / Rotate / Hard Drop: all exact
- first failure: none

## Line Clear stress test

Additional random boards with forced full rows:

- 1 row: 12,500 / 12,500
- 2 rows: 12,500 / 12,500
- 3 rows: 12,500 / 12,500
- 4 rows: 12,500 / 12,500

Total: **50,000 / 50,000 = 100%**.

Earlier causal audit after deleting the separate row-propagation function:

- normal reuse of Down: 100,000 / 100,000
- row carrier off: 0 / 100,000
- deliberately reuse Left instead of Down: 4 / 100,000 accidental matches

## Compression vs v2.6

Approximate:

- conceptual relations: ~7,070 -> **~34** (~208x fewer)
- robust shared field capacity: 2^22 -> **2^13** (512x fewer cells)
- training writes: ~6,468,350 -> **51,720** (~125x fewer, including all three phases)

This supports the interpretation that much of the earlier apparent complexity came from redundant representation and address false positives rather than from Tetris rules themselves.

## Engineering verification

- C11 `-Wall -Wextra -Werror`: PASS
- O2/O3 output: byte-identical
- SHA-256: `e5be7a3849db8917cb557eb7cde5e9c409b0a720610742f71e29f816964850f8`
- O2/O3 diff: 0 bytes
- UBSan exit: 0
- UBSan stderr: 0 bytes

## Strongest supported conclusion

In this controlled Tetris world, the full compositional closure can be represented as:

`single-cell effect -> spatial superposition -> shared carrier -> temporal recursion -> cross-plane reuse`

inside one compact multi-phase probability field.

This strongly reinforces the correction that Tetris should not be modeled as a 416-bit full-frame memorization problem.

## Boundary

This still does not establish a fully self-growing pure BPC core.

Remaining scaffolds include:

1. physical coordinate/channel identities are supplied;
2. Move / Rotate / Spawn / relaxation still have different execution procedures;
3. the latent rotation carrier remains an explicit internal channel;
4. micro-experience families are externally presented;
5. the three address phases and pairwise-interference law are fixed bottom-level physics.

The next frontier is execution-operator unification: make Move / Rotate / Spawn instances of one generic `function wave × raw tokens -> future tokens` propagation law.
