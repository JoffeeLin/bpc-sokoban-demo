# Unified Theory — Query-Function Core v0.1

## 1. Pure-core boundary

The permanent distinction is:

> We may design BPC's task-independent physical laws, but not its cognitive structure.

Allowed bottom-level laws include state carrying, local propagation, interference, decay, conservation, prediction, Reality Residual writeback, lifecycle and physical measurement.

Not allowed as core cognition:

- object / entity labels;
- semantic relation classes;
- memory modules;
- target/planner/subgoal modules;
- task routers;
- repair/blocker roles;
- prewritten Function objects;
- top-1 internal path selection;
- test-specific patches.

## 2. Voxel-accumulated function

Raw information becomes current voxel state. Each voxel accumulates the real local history it actually experiences. Stable local transition dynamics emerging from that history are what an external observer may call a **function**.

\`\`\`text
Information
  -> Voxel State
  -> Real History Accumulation
  -> Stable Local Dynamics
  -> Function Emergence
  -> New State Evolution
\`\`\`

The function is not an object stored in a function library. It is the reason the medium evolves in a repeatable way.

## 3. Why accumulation alone is insufficient

Function accumulation only closes the first half of computation. A usable BPC must also close:

\`\`\`text
Accumulated Function
  -> Query Participation
  -> Prediction
  -> Real Consequence
  -> Reality Residual
  -> Writeback through actual participation
  -> Changed Function
\`\`\`

Without this lower loop, accumulated functions are static deposits rather than active computation.

## 4. Query wave as the active computational object

A query is not a lookup key. It is the current perturbation and propagation state of the whole medium.

Let the initial query contain current physical information:

\[
Q_t^{(0)} = \operatorname{Encode}(X_t,A_t,\text{available relation state})
\]

All accumulated voxel functions that are physically reached by this query participate continuously:

\[
\Phi_i^{(k)} = F_{M_i}(Q_i^{(k)})
\]

and the field evolves:

\[
Q_t^{(k+1)} = \mathcal P\!\left(Q_t^{(k)},\{\Phi_i^{(k)}\}\right).
\]

No internal discrete selection is required. Multiple compatible or incompatible relations may simultaneously strengthen, cancel, split or persist.

The prediction is measured only at a physical output boundary:

\[
\hat Y_t = \operatorname{Measure}(Q_t^*).
\]

## 5. Participation trace

Every relation that actually changes the current query leaves a physical trace:

\[
\tau_i = (\text{source state},\text{address/path},\text{amplitude},\text{phase},\text{duration},\text{output effect}).
\]

This trace is not a semantic relevance score. It is evidence that the relation actually participated in the forward computation.

## 6. Query-error writeback

When the real future arrives:

\[
D_t = Y_t-\hat Y_t,
\]

Reality Residual is not written uniformly to the whole field and is not assigned to one hand-picked winner.

It is reflected through the real forward traces:

\[
D_{t,i}=\mathcal R(D_t,\tau_i).
\]

Each participating voxel/function accumulates the new real history:

\[
H_i(t+1)=H_i(t)+\bigl(Q_{t,i},D_{t,i},Y_t\bigr),
\]

which changes its future dynamics:

\[
M_i(t)\rightarrow M_i(t+1).
\]

Thus **query-error writeback is itself new function history**.

## 7. Reuse

A reusable function does not need a \`reuse(F)\` call. A new surface state is reused when its query naturally falls into an already formed dynamical basin:

\[
Q(X_{new})\rightarrow F\rightarrow \hat Y.
\]

If reality confirms the prediction, the same function is reinforced without increasing irreducible complexity.

## 8. Coarse function first, residual growth second

The minimal support should explain reality first. New function freedom should be born only from persistent unexplained residual.

\`\`\`text
Coarse function explains first
  -> residual is small: do not grow structure
  -> residual persists under a more specific condition
  -> allow finer support to grow locally
\`\`\`

A one-off error is not sufficient evidence for a permanent new function.

## 9. Consequence-grounded lifecycle

A relation should not become permanent because its residual norm crosses a hand-written threshold. Its participation strength should be grounded in **future consequence**:

- Does using it reduce later real residual?
- Does removing it make prediction worse?
- When reality changes back, does its future utility disappear?

This yields a continuous lifecycle:

\`\`\`text
Birth -> weak participation -> repeated future utility -> stronger participation
     -> actual query-error reshaping -> reuse
     -> loss of future utility -> decay -> death / slot reuse
\`\`\`

## 10. Causal support focusing

Wide queries create combinatorial danger. Support growth should not enumerate all co-occurring tokens.

For a participating parent function \(P\) and a co-participating trace \(x\), compare unresolved future effects:

\[
C(P,x)=\overline D(P+x)-\overline D(P).
\]

Only a persistent contrast is evidence that the parent support is missing the added trace.

This makes residual itself answer:

> Which currently participating physical condition actually changes the unexplained future?

## 11. Stable coarse / plastic fine dynamics

A long-validated coarse function should not be destroyed by a small number of new exceptions before a fine function has time to form.

Current evidence supports a continuous reuse-dependent plasticity law such as:

\[
\pi_i=\frac{1}{\sqrt{1+\mathrm{reuse}_i/\tau}}.
\]

Old validated functions remain active but change slowly; newborn fine relations are more plastic.

This is not a semantic mature flag. It is a physical timescale derived from real reuse history.

## 12. Function state re-entry

A function must be able to become ordinary query matter for later computation.

If function \(F_1\) participates at time \(t\), its anonymous relation state may enter the next query:

\[
R_{F_1,t}\rightarrow Q_{t+1}.
\]

Then Reality Residual may form a higher relation:

\[
R_{F_1,t}+X_{t+1}\rightarrow F_2.
\]

This is the current BPC interpretation of function composition:

\[
\boxed{\text{function state}\rightarrow\text{ordinary query state}\rightarrow\text{higher function}}
\]

rather than an explicit \`compose(F1,F2)\` operator.

## 13. Function identity may be a dynamical orbit

A function identity need not be one static bit vector. If a relation repeatedly falls into a stable period, attractor or other stable trajectory, the trajectory itself may be the function identity.

This is the intended route to hidden process state:

\[
R_t\rightarrow Q\rightarrow R_{t+1}.
\]

The unresolved test is whether this can autonomously form stable period-3 / period-N processes without a clock, phase label or fixed history depth.

## 14. Compression criterion

Accuracy alone is insufficient. A wrong internal representation can fit the same outputs by proliferating redundant functions.

The long-term criterion is:

\[
G\uparrow,\qquad K_{irreducible}/G\downarrow.
\]

where:

- \(G\): permanently held-out generalization supported by the current function closure;
- \(K_{irreducible}\): internal function/support complexity that causally changes behavior.

A mechanism is stronger when it achieves the same or larger \(G\) with smaller, reusable and cleanly dying \(K\).

## 15. Unified loop

The current integrated theory is:

\`\`\`text
Reality X_t / action A_t
        ↓
Query wave Q_t
        ↓
Accumulated voxel functions participate continuously
        ↓
Prediction Ŷ_t
        ↓
Real future Y_t
        ↓
Reality Residual D_t
        ↓
Trace-grounded error reflection
        ↓
Existing-function reshaping
        +
Causally focused support growth when residual persists
        ↓
Function lifecycle / compression
        ↓
Participating relation state re-enters later queries
        ↺
\`\`\`

This is the current candidate bridge from **function accumulation** to **function computation**.
