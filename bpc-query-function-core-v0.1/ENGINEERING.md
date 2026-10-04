# Engineering Specification — Query-Function Core v0.1

## 1. Engineering goal

Build one task-independent C core in which:

1. raw physical tokens enter a query wave;
2. accumulated relation states participate continuously;
3. the forward pass records real participation traces;
4. Reality Residual writes only through those traces;
5. persistent unexplained residual can grow local support topology;
6. future consequence controls relation participation and death;
7. accumulated function state can re-enter later queries.

The code must not require task semantic labels or task-specific functions.

## 2. Minimal state classes

The integrated implementation should ultimately use the same physical storage law for all of these:

### Raw token state
Current externally grounded state bits / waves.

### Relation/function state
History-shaped local dynamics that modify query propagation.

### Participation trace
Ephemeral forward-computation footprint. It exists only because the current query actually propagated through that relation.

### Residual state
Real prediction difference written back through actual traces.

### Relation carrier
A relation/function state that survives long enough to become ordinary material in a later query.

These are not semantic modules; they are time-scales / roles of one medium.

## 3. Forward pass

Conceptually:

\`\`\`c
query = encode_raw_state(...);
clear_ephemeral_trace();

for (internal_tick = 0; internal_tick < physical_limit; ++internal_tick) {
    for_each_reached_relation(r) {
        effect = relation_forward(r, query);
        query_interfere(query, effect);
        record_participation_trace(r, effect);
    }
    if (physical_settle(query)) break;
}

prediction = measure(query);
\`\`\`

Important constraints:

- no router;
- no top-1 relation;
- no task-class switch;
- no \`if (this is a move/sequence/cycle)\`;
- all participating relations remain continuous.

## 4. Reality Residual path

\`\`\`c
residual = reality - prediction;

for_each_actual_trace(t) {
    local_error = reflect(residual, t);
    accumulate_real_history(t.relation, t.local_query, local_error, reality);
}
\`\`\`

Controls required in every formal experiment:

- trace off;
- trace-address shift;
- phase/sign inversion when meaningful;
- whole-field equal writeback;
- no writeback.

## 5. Consequence-grounded participation

There is no binary maturity threshold in the frozen v0.3d line.

A relation maintains continuous participation strength from future real utility:

\`\`\`c
utility <- EMA(counterfactual real-loss improvement)
strength <- physical_map(max(0, utility))
\`\`\`

Participating relations share a finite query/effect budget so redundant copies cannot all claim the same residual energy.

When later reality no longer benefits from a relation, its strength decays toward zero.

## 6. Support topology growth

### v0.4d rule

Support topology starts empty. A new support is born only from traces that actually co-participated in a wrong query.

The same local rule handles increasing depth:

\`\`\`text
support + current participating trace -> extended support
\`\`\`

There is no global pair/triple/quad table.

### v0.5d focusing

Naively extending every co-occurring trace causes combinatorial growth. The current frozen improvement uses causal residual contrast:

\`\`\`text
mean unexplained residual under parent P
vs
mean unexplained residual under parent P + trace x
\`\`\`

Only persistent difference receives finite growth mass.

Correct events under the same condition decay unused growth mass.

## 7. Coarse-function stability

Query-error plasticity is scaled by real reuse history. Long-validated coarse functions remain active but are less plastic than new fine functions.

Current candidate:

\`\`\`c
plasticity = 1.0 / sqrt(1.0 + evals / tau);
\`\`\`

This prevents a new exception from immediately rewriting the coarse rule before the fine residual relation can form.

## 8. Relation-state re-entry

v0.8 adds the next computational requirement:

\`\`\`c
if (relation actually participated at t) {
    emit anonymous_relation_carrier(relation_id_or_state);
}

Q[t+1] += previous_relation_carrier;
\`\`\`

The temporal relation itself must also receive Reality Residual only through actual carrier participation.

Carrier-off and temporal-trace-writeback-off are mandatory causal controls.

## 9. Current frozen evidence sources

- \`src/bpc_consequence_lifecycle_v03d.c\`
- \`src/bpc_dynamic_support_v04d.c\`
- \`src/bpc_querytrace_causal_support_v05d.c\`
- \`src/bpc_query_algebra_v06.c\`
- \`src/bpc_query_algebra_v07_boundary.c\`
- \`src/bpc_relation_reentry_v08.c\`

These are evidence snapshots, not yet one production core. The next engineering milestone is to merge their task-independent mechanisms into one isomorphic field without preserving experiment-specific pools.

## 10. Current engineering invariants

Every promoted C implementation should pass:

\`\`\`text
-std=c11
-Wall -Wextra -Werror
O2 / O3 representative output diff = 0
UBSan stderr = 0
frozen evaluation writes = 0 where applicable
multiple independent seeds
causal ablations
\`\`\`

## 11. What must not be reintroduced

Do not solve future failures by adding:

\`\`\`text
pair_table_for_task()
sequence_operator()
cycle_operator()
periodic_state_id
semantic_relation_type
planner
search over candidate functions
manual hard-coded merge
manual function name or slot role
\`\`\`

If a capability requires one of these, record it as a boundary of the current core.
