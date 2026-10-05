# BPC Raw-Visual GameFit v0.160–v0.161 — Diagnostic Branch

Date: 2026-10-05
Status: diagnostic branch; retained for evidence/history, not selected as the current best world-fit baseline.

## Goal

Test whether the then-current Pure-Tetris v0.153 world model could be moved toward a stricter visual interface without changing the learned game dynamics.

The target distinction was:

- interface bridge: render the visible state as one image, then decode visible colors back into the internal information channels;
- strict merged-binary input: collapse visible information identities into one binary board and test whether the same world model remains information-closed;
- rare-event follow-up: test whether missing LineClear in a second seed was experience coverage or representational inability.

## v0.160 — raw-visible interface bridge

`bpc_raw_visual_full_tetris_v0160.c` renders the state into a single visible frame and preserves visually distinguishable information identities. It then bridges that visible representation to the existing v0.153 field.

Representative seed1 result:

- step8/12/20: 100/100;
- program8/12/20: 50/50;
- deep12: 50/50;
- LineClear / arbitrary-row clear: 50/50;
- Spawn / GameOver: 50/50;
- rollout: 20,000/20,000.

This is useful as an interface-closure check, but it is **not** evidence that BPC itself discovered the visual channel decomposition: the bridge still reconstructs the internal information identities before the existing world model runs.

## v0.160 two-seed audit

The two-seed version retained 100% normal step/program/deep and Spawn/GameOver, but the second seed had:

- LineClear: 0/50;
- arbitrary-row clear: 0/50;
- multiline: 0/50.

The same seed remained exact on the other world functions and long rollout.

This reproduced the known rare-function coverage boundary: a world seed can fail to mature a low-frequency LineClear relation when the training stream does not contain enough causally useful clear events.

Increasing the same random experience stream to 192k did not fix that seed, so "more random ticks" is not equivalent to "more informative rare-event experience".

## v0.160b — destructive binary merge negative control

`bpc_raw_binary_full_tetris_v0160b.c` collapses the visible board identities into one binary layer.

Smoke result:

- step: 0%;
- program: 0%;
- Spawn/GameOver: 0%;
- rollout: diverges immediately.

Interpretation: this negative control removes information that is genuinely visible in a normal game display (e.g. different visible information instances / colors / regions). It therefore does **not** prove that a raw visual interface is impossible; it proves that destroying observable identity can make the state non-Markov / non-identifiable.

## v0.161 — rare-event exposure probe

The branch explicitly probed whether a small number of real LineClear consequences could birth the missing relation in the failing seed.

Observed diagnostic:

- 0 explicit rare exposures: LineClear 0/50;
- 1 exposure: LineClear 50/50, arbitrary 50/50, multiline1 50/50;
- additional repeated exposures in this prototype could destabilize the same relation again.

This is not a final curriculum solution. It showed two things:

1. the missing seed was capable of representing the LineClear consequence once the relevant reality was encountered;
2. naive repeated writes can overwrite / destabilize a rare mature relation, so experience lifecycle matters.

## Why this branch is not the current baseline

The later baseline selection is stricter:

- use Minimal v2.1 as the fully-observable world capability floor (8-seed long-rollout exactness);
- reuse later compression mechanisms such as v2.12b's Down reuse for LineClear;
- use later Pure/v3.x results only when they delete scaffolding without reintroducing hidden-state or supervision assumptions.

Thus v0.160-v0.161 is preserved as evidence, but subsequent world-fit purity work continues from `Best World-Fit` rather than from this branch.