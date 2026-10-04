# BPC Tetris Minimal v3.2 — Unified Probability Field + Anonymous Multi-Address Interference

Date: 2026-10-04

## Goal

Continue compressing the minimal Tetris line without adding Tetris-specific cognitive rules.
The target was no longer higher game accuracy. The target was to remove separate parameter stores and separate relation executors.

## What was removed before v3.2

The line had already established that 3x3 single-cell experience can form reusable movement, collision, rigid participation, recursive Hard Drop, rotation, lock, spawn and row propagation functions.

v2.6 compressed all learned binary relations into one direct-hashed Beta field.
v2.7-v2.9 then removed more duplicated functions:

- row propagation reuses the already learned DOWN function;
- lock/spawn branching reuses one anonymous direct/complement split relation;
- full-row participation reuses that same split relation.

Five independent v2.9 long runs at 2^22 all reached 100% tick exactness.

## v3.0 — one relation execution equation

Internal semantic carrier tags such as FROM_PREVIEW / FROM_WORLD / CARRIER were removed.
Spawn is distinguished only by raw source/destination channels.

Move, Rotate and Spawn were rewritten to use one generic probability propagator:

    source tokens -> shared Beta relation field -> destination-token probabilities

All source contributions combine continuously using the same noisy-OR equation.
The anonymous split function was also expressed through the same weighted token propagator.

Representative frozen result: 19,243 / 19,243 ticks exact = 100%.

## v3.1 — one collision carrier equation

The separate move_go / rot_go / spawn_carrier inference paths were removed.
Each relation first produces a candidate probability field, then one generic physical interference equation measures compatibility with the blocked field.

Representative result: 19,243 / 19,243 exact = 100%.

With one address per relation, salt 271828 produced 99.731726% at powers 22-24. Direct key audit found two same-family Spawn relations still colliding at power 24. At power 25 those collisions disappeared and exactness returned to 100%.

## v3.2 — anonymous multi-address participation

Every conceptual relation now participates through four independently hashed addresses in the SAME shared field. There are no semantic branches and no top-1 selection. All four addresses are written and all four probability estimates participate.

This is task-independent redundancy / interference.

### Capacity boundary

- p18 can fail substantially.
- p19 can be 100% for one salt but 99.12% for another.
- p20/p21/p22 still show rare failures for specific salts.
- p23 is the first tested point that survived the formal 5-salt / 5-world matrix.

Eight phases at fixed p20 were NOT universally better: increasing phase count also increases field occupancy and cross-talk. The relevant variable is the combination of redundancy and address density, not "more phases is always better".

### Formal p23 frozen result

Five independent world seeds paired with five independent hash salts:

- total ticks: 95,913
- exact ticks: 95,913
- exactness: 100%
- lock events: 29,545
- evaluation writes: zero

### Collision audit

There are about 7,056 conceptual learned relation keys. At p23/4-phase, tested salts still contain some individual address collisions, but no audited relation had two or more of its four phase addresses contaminated; each retained at least three clean participating addresses.

At lower powers, a small number of relations can have two or more contaminated phases, matching rare Drop failures. This is strong correlation, not yet a universal theorem.

## Current compressed description

    raw experience
      -> one shared probability field
      -> generic weighted token relation propagation
      -> generic physical compatibility carrier
      -> recurrent reuse to fixed point

The named C helpers still remain as experimental scaffolding for coordinate charts and external action injection.

## Remaining scaffolding

1. channel identities (active/world/preview/internal pivot carrier);
2. coordinate charts for translation, rotation-local space and preview-to-board grounding;
3. the outer action/process dispatcher;
4. the rule that injects the visible/external action carrier;
5. curriculum boundaries;
6. finite hash capacity and phase count.

The next experiment should remove the outer action/process dispatcher so that the same shared field dynamics determine which learned relations participate, while the external action enters only as another raw carrier.

## Verification

- GCC C11 -Wall -Wextra -Werror: PASS
- O2/O3 representative output: byte-identical
- UBSan stderr: 0 bytes
