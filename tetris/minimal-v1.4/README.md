# BPC Tetris Minimal v1.4

This experiment line replaces the early 416-bit whole-frame fitting approach with small reusable physical functions learned from single-cell/local experiences.

Frozen integrated result:

- one-step composed holdout: 20,000/20,000 exact
- Left 4086/4086
- Right 4050/4050
- Down 4014/4014
- Rotate 3905/3905
- Hard Drop 3945/3945
- one-step lock events 5697/5697
- free self-reentry rollout: 80,925/80,925 ticks exact
- rollout lock events: 24,935
- rollout game-over events: 2,000
- failures by action: zero

The model primitives are trained from local/single-cell reality, not tetromino-level rule tables. Hard Drop is recursive Down until action closure. Line clear is a shared full-row carrier followed by recursive local hole propagation.

Important boundary: this is still a controlled simplified Tetris mechanism experiment, not a claim of fully pure BPC learning commercial Tetris. Rotation still receives an anonymous pivot carrier; action-specific learned function families are staged by the C program; new random Preview is treated as exogenous reality input; SRS wall kicks/Hold/scoring/levels are not modeled.

Engineering: C11 -Wall -Wextra -Werror PASS; O2/O3 diff=0; UBSan exit=0, stderr=0.
