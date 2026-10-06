# BPC Binary World-Fit — Current Best

Current promoted checkpoint: **v1.13**

This directory is the canonical entry point for the best fully frozen world-fitting version currently promoted in the Tetris line.

## Verified capability

- 8 independent long-rollout seeds
- exact visible-state reproduction: **312,839 / 312,839**
- no divergence in any formal seed
- GCC C11 O2/O3 strict builds: PASS
- O2/O3 full-output diff: 0 bytes
- UBSan reduced smoke: 0-byte stderr

## Current interface

The inference core accepts only:

- a 15x20 binary visible screen;
- the model's self-maintained temporal trace;
- a 5-port external action wave.

The promoted core uses the shared BIT + RELATION probability field and no separate neural network, reward model, planner, policy table, handwritten collision rule, row detector, clear-line procedure, hole propagator, or function-family namespace.

## Important boundary

This is the current best **world-model** checkpoint. It does not mean BPC has already learned to play Tetris autonomously. The next intended validation is to feed demonstrations from an external successful player into the same medium and test whether action-port waves can emerge without adding a separate policy-learning module.

The frozen field binary used by historical evaluations is not present as a standalone file in the currently available artifact set, so this directory preserves the promoted inference source, public API, formal result, and report. Historical experiment sources remain under ../research-2026-10-06/.

## Source identity

Promoted source SHA-256: `30c60001c935352ad5a811710e6cf20addf37c106ca7d48ebdacd83fec1288f0`

Promoted result SHA-256: `57e776a34ca448baf3f49d3b526de50ab33c35ecefbcca5a6094758a431c70fe`
