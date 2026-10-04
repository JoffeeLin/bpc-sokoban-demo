# Roadmap — Query-Function Core v0.1

## P0 — Preserve the frozen evidence chain

Do not overwrite v0.3d, v0.4d, v0.5d, v0.6, v0.7 or v0.8. They serve different causal claims.

## P1 — Relation Carrier Orbit v0.9

### Question

Can relation state itself form a stable recurrent function orbit?

### Forbidden shortcuts

Do not provide:

- phase labels;
- a clock;
- fixed \`history[2]\`, \`history[3]\`, ...;
- period-specific operators;
- a hand-written cycle state machine.

### Candidate physical loop

\`\`\`text
R_t
 -> same query medium
 -> prediction / new relation state R_{t+1}
 -> real consequence
 -> residual
 -> actual R_t participation trace
 -> R dynamics update
 -> R_{t+1} re-enters
\`\`\`

### Minimum worlds

1. hidden period-3: identical raw input, outputs \`0,0,1,...\`;
2. hidden period-5;
3. period change \`3 -> 5 -> 3\` to test reconstruction/death;
4. nonperiodic control where no stable carrier orbit should be promoted.

### Acceptance

- hidden period-3 and period-5 reach near/exact closure without clock/history-depth injection;
- carrier off returns to information-theoretic baseline;
- trace writeback off fails;
- wrong carrier phase/address fails;
- internal K remains bounded and does not grow linearly with time;
- after period change, obsolete orbit loses causal participation rather than remaining as permanent clutter.

## P2 — Merge temporal relation pool into the ordinary support medium

v0.8 still has a separate temporal relation pool. Replace this with one isomorphic storage/propagation law so that raw relation, fine support and temporal carrier differ only by their current physical state/history, not by code type.

Acceptance: v0.5d and v0.8 abilities survive with no \`temporal_pool\` special case.

## P3 — Cross-algebra frozen-core test

Freeze the same core and change only experience across:

- conjunction/support;
- order-sensitive process;
- phase/cycle;
- reversible transform;
- one continuous or signed transform family.

No new operator is allowed between worlds.

The target is not merely accuracy. Compare \`G\`, effective causal \`K\`, birth/death curves and relation reuse.

## P4 — Return to Tetris only after the self-building loop is stronger

When P1–P3 succeed, restart Tetris from raw screen/action/real-next-screen only.

Do **not** seed the hand-compressed Tetris function closure.

The success criterion is whether the new query-function core autonomously re-discovers a compact function system whose causal closure reaches the game dynamics with \`G up\` and \`K/G down\`.

The old manually compressed Tetris line is retained only as a reference upper bound for how small the world closure can be.
