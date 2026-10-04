# BPC Tetris Lifecycle v0.18

Complete-game Direct-Fit experiment testing task-independent fast/slow residual voxels after v0.17.

Main conclusion: **partial positive evidence, not adopted as the new best core.**

- A slow mature state is causally necessary for the learned Lock ability.
- 3-seed 200k same-stream Lock mean: **12.496%**.
- Slow-off mean Lock: **0.231%**; slow-address shift and slow phase flip: **0%**.
- Mature-only preserves essentially all Lock ability.
- However mature capacity keeps growing (mean Km at 200k: **18,101**) while Lock plateaus.
- A single slow residual control reached **19.463% Lock at 100k**, so the two-timescale mechanism is not proven superior.
- A strong-consistency maturity rule compressed Km to 941 but destroyed Lock.
- True global lazy decay reduced fast-state K strongly, but did not solve mature-state growth.

See REPORT.md and result_summary.csv.

The local experiment package also contains the C sources for the linear, coherent-maturity, global-decay, and direct-slow variants plus raw logs and verification.
