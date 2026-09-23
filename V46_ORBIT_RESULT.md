# BPC v0.46 rotation-orbit result

Status: **FAIL / NON-ADOPTED**. With the unchanged v0.45 core and matched
four-rotation physical experience, aggregate strict selection fell to 67.77%
and per-orientation rates were 78.13%, 75.00%, 65.63%, and 52.34%. The 70%
aggregate and 60%-per-orientation gates both failed.

All probability, control, world-retention, compression and zero-write gates
passed. The persistent directional asymmetry under exact experience orbits
triggered a source audit rather than another threshold adjustment.

The audit found that the Sokoban camera serialized its 7x7 pixels contiguously
into bytes 0–48, while every physical stencil used an 8-cell row stride. There
was no padding byte after each seven-pixel row. Consequently, vertical and
diagonal stencil neighbors did not correspond to the rendered 2D grid. This
explains why action-channel permutation tests passed while physical rotation
did not.

v0.46 is retained as the falsifying evidence. Do not rerun it or claim its
failure was sampling noise. A successor must introduce a correctly aligned
8x8 physical camera as a new version and revalidate world prediction before
returning to closure behavior.
