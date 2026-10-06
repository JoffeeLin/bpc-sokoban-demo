# BPC Minimal Kernel v1.54–v1.66 — Scaffold Deletion Report

Date: 2026-10-06

## Evidence boundary
This batch is a minimal-kernel mechanism line. It does **not** replace the frozen full-Tetris world-fit checkpoint. The purpose is to continue deleting internal scaffolds before reintegrating the same residual law into the real Tetris stream.

## Stable controlled task
A 24-position deterministic physical world is used only as an audit harness. Each active physical position causes two future physical positions. Training uses a continuous multi-source stream; evaluation uses unseen multi-source combinations. There is no singleton curriculum in this batch.

## v1.54 — remove `observe()` / `predict()` and named now/future roles
Replaced separate prediction and learning APIs with one `reality_tick()`:
1. current medium propagates;
2. physical reality arrives;
3. one residual writes back through participating relations;
4. reality becomes the medium for the next tick.

Time exists only through re-entry, not through separate `now` / `future` function roles.

Result: `300000/300000`, 48 resident true relations, false max 0, frozen field unchanged.

## v1.55 — relation stores one scalar mass
Deleted persistent `off/on` relation state. Each relation stores only one continuous mass; complementary off-mass is `1-mass` and exists only while `move_mass()` acts.

Result: `300000/300000`, 48 resident relations, frozen field unchanged.

## v1.56 — remove internal binary selection
Core propagation emits continuous amplitudes only. `>0.5` binary measurement is moved to the external physical measurement boundary; it is not part of the relation kernel.

Result: measured `300000/300000`, maximum continuous error 0, frozen field unchanged.

## v1.57 — reality re-entry uses the same mass-motion primitive
Deleted direct `medium = reality` overwrite. Reality re-enters each physical position through the same `move_mass()` primitive used for relation birth/death.

Result: `300000/300000`, frozen field unchanged.

## v1.58 — delete event-level `Delta[]` relation update objects
Deleted the explicit list of relation updates. Each tick contains one global output residual vector; every participating ordered relation synchronously reads that residual.

Result: `300000/300000`, frozen field unchanged.

## v1.59 — remove special Reality type
Current state, prediction and physical reality are all the same continuous `Medium` type. Binary values are an external property of this test environment, not an internal truth class.

Result: `300000/300000`, frozen field unchanged.

## v1.60 — remove compile-time port count
The kernel no longer knows a fixed number of screen/action/history positions. Port count is supplied by the external physical topology at runtime.

Result: `300000/300000`, 48 true relations.

## v1.61 — remove predeclared relation capacity
Sparse relation storage grows only when relation mass is actually born. No external maximum relation count is supplied to the kernel.

Result: `300000/300000`; 48 positive relations remained.

## v1.62 — BIT state and relation state share one mass store
Deleted persistent `Medium` vs `Field` storage separation. Physical BIT positions and ordered relation amplitudes are addresses in the same sparse mass store and both are changed through `move_mass()`.

Result: `300000/300000`; 48 positive relations; 52 total active store cells; frozen relation field unchanged.

## v1.63 — remove participation gates
Deleted `if(source>0)` and `if(residual!=0)` participation selection. All physical positions traverse the same continuous equations; zero amplitude naturally has zero effect.

Result: `300000/300000`.

## v1.64 — relation birth is not a positive-residual branch
An absent relation begins at zero mass and is passed through `move_mass()` exactly like an existing relation. It is materialized only if the resulting physical mass is positive. There is no `if(residual>0) birth` cognition rule.

Result: `300000/300000`.

## v1.65 / v1.65b — relation death is zero mass, not object deletion
The first v1.65 retained zero-mass historical relation cells and became too slow with linear lookup; this was an efficiency failure, not an accuracy result.

v1.65b replaced lookup with an auto-growing hash store while keeping zero-mass relations physically present. No `erase relation` cognition operation remains.

Result: `300000/300000`; 48 positive relations; 370 stored cells including zero-mass history; frozen positive field unchanged.

## v1.66 — physical addresses supplied by the external medium
Deleted kernel-owned `node_addr(port)` identity. The outside physical substrate supplies arbitrary port addresses; the kernel only composes ordered physical addresses into relations.

Three independently permuted physical-address layouts were trained/evaluated:
- trial0: 48 positive relations;
- trial1: 48 positive relations;
- trial2: 48 positive relations;
- total exact: `300000/300000`.

## v1.66 engineering audit
- C11 `-Wall -Wextra -Werror -pedantic`: PASS
- O2/O3 output diff: 0 bytes
- UBSan stderr: 0 bytes

## Current candidate kernel
The controlled mechanism is now approximately:

`physical address mass`
`+ ordered physical-address relation mass`
`+ one sparse mass store`
`+ one move_mass() primitive`
`+ one global reality residual`
`+ synchronous relation responsibility`
`+ reality re-entry`

Deleted in this batch:
- observe/predict role split;
- named now/future API roles;
- relation off/on persistent pair;
- internal binary selection;
- direct reality overwrite;
- Delta update objects;
- special Reality type;
- fixed port count;
- fixed relation capacity;
- Medium/Field persistent-store split;
- boolean participation gates;
- positive-residual birth branch;
- relation-object deletion on death;
- kernel-owned physical port addressing.

## Next experiment
Reintegrate the v1.64–v1.66 global-residual mechanism into a real black/white Tetris `screen + operation -> next screen` stream. The critical test is whether higher-order collision/relation waves can receive useful credit from the same global visible residual without reintroducing Geometry/Spawn/Closure family observers.