# BPC Tetris Time-Triangle v0.19

This experiment tests the proposal that the cube Z axis can directly carry time/function depth:

- frame 1 enters L1;
- L1 participates in predicting frame 2;
- real residual writes back into participating old slices;
- frame 2 becomes L2;
- L1+L2 participate in predicting frame 3;
- and so on.

The strongest reproducible Z=6 candidate gives partial positive evidence:
ordered multi-slice participation and old-slice writeback are causally useful, especially at prediction depths >1. However complete Lock remains 0%, and increasing Z to 12 does not improve the result.

Therefore v0.19 is **partial evidence for temporal accumulation, not proof that time-as-Z is sufficient for complete Tetris**.

See REPORT.md and result_summary.csv.
