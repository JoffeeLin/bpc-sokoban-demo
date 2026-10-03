# BPC Tetris v1.2 — Hierarchical Residual Closure

This directory records the frozen v1.2 Tetris mechanism experiment.

## Reproduce

```bash
gcc -O2 -std=c11 -Wall -Wextra -Werror bpc_tetris_v1_2_hierarchical_residual.c -lm -o bpc_tetris_v12
./bpc_tetris_v12 15000 5000 5000 400 3
./bpc_tetris_v12 15000 20000 20000 600 1
```

The model receives raw visible Tetris frame bits. It is not given piece type, x/y, rotation, landing position, collision, lock, clear, or spawn labels.

Main finding: a frozen mature local one-step gravity function plus local residual relations plus a cross-region composed residual relation produces non-zero, reproducible unknown-length terminal closure. At 20k/20k residual experience (seed 0), terminal full exact reached 58.17% and recursive-to-lock full exact reached 24.33%. Pair-relation off/flip/address-shift ablations collapse terminal full exact to 0%.

This is mechanism evidence, not a claim that BPC has learned full Tetris. See REPORT.md.
