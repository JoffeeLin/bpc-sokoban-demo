# v0.44 post-publication geometry audit

Date: 2026-09-23. This audit supersedes the spatial interpretation of the
Sokoban-physics half of v0.44.

`bpc_pure_medium_v41.canvas()` appended a 7x7 image as 49 contiguous bytes and
then appended padding to reach 64 bytes. `local()` interpreted those bytes with
an 8-cell row stride. Therefore the stored image was deterministic and raw,
but its horizontal/vertical stencil geometry did not match the displayed 7x7
board after the first row.

The v0.44 raw JSON, hashes, controls, no-write evidence and causal-lattice
result remain reproducible. The Sokoban track remains evidence for compressed
prediction over that fixed serialized byte interface, but it is **not valid
evidence for correctly aligned 2D axis-local Sokoban physics**. Therefore the
combined result must not be promoted as a two-domain spatial-physics
breakthrough until a new aligned-camera version independently passes.

The public repository and release are being annotated rather than rewritten or
deleted. v0.47 will use row-aligned 8x8 bytes and will rerun the physical and
boundary gates with fresh worlds.
