# BPC v0.45 frozen reproduction result

Status: **FAIL / NON-ADOPTED**. The first frozen execution used commit
`810eb2d`, unchanged source hashes and 512 fresh balanced worlds. No rerun or
threshold change is made.

## Evidence

- aggregate strict closure selection: 70.90%;
- port Brier: 0.10124;
- median correct-action probability margin: 0.17727;
- unseen full local contexts: 14.32%;
- non-port world Brier: 0.004959 versus local-only 0.004957;
- active cells: 15,144 at fixed `2^20` capacity;
- action-removed and local-only selection: 0%;
- rotated-action selection: 8.79%;
- shifted-state selection: 12.30%;
- evaluation writes: zero, with all digests unchanged.

Ten of eleven gates passed. Per-orientation strict selection was 75.78%,
79.69%, 69.53%, and **58.59%**. The last orientation missed the frozen 60%
minimum, so the entire result is non-adopted despite passing the original ten
development gates.

## Decision

Do not publish v0.45 as a breakthrough and do not lower the per-orientation
gate. The core is exactly action-renaming equivariant, but independently drawn
decorations leave finite directional sampling variation. A successor may use
fresh, physically executed rotation-orbit worlds so every underlying layout is
experienced in all four directions; it must retain the same core and frozen
thresholds. This remains a one-step boundary experiment, not long-process
behavior or AGI.
