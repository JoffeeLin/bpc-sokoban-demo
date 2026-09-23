# BPC v0.48 aligned minimal-boundary result

Status: **PASS on the first and only frozen execution**.

The unchanged non-neural probability medium received anonymous aligned bytes,
anonymous action indices and physical next bytes.  A carrier byte exposed one
physical bit: whether the marked boundary remained after the action.  The
medium predicted that bit in parallel for all four actions; behavior selected
the action with the lowest predicted probability that the boundary would
remain.  There was no reward, task score, search, planner or evaluation write.

| Frozen held-out evidence | Result |
|---|---:|
| fresh rotation-balanced layouts | 512 |
| strict correct selection | **512 / 512 (100%)** |
| each physical orientation | **100%** |
| unseen action/context pairs | 16.87% |
| one-bit port Brier | 0.02335 |
| median probability margin | 0.61274 |
| non-port world-prediction Brier | 0.00307 |
| evaluation writes | **0** |

The causal controls did not reproduce the effect: action removal, local-only
readout, rotated actions, shifted states, removed carrier and flipped readout
all selected 0%; zeroing the spatial condition channel selected 16.21%.  The
candidate beat every fixed control by more than the preregistered 30-point
margin and all eleven gates passed.

This reproduces one-step coupling between physical world prediction and a
minimal external closure bit under corrected geometry.  It is a prerequisite,
not completion, of the theory's second phase: there is not yet a recurrent
internal state whose zero/flip intervention destroys long-process behavior.
It is not general Sokoban solving or AGI.

Machine-readable evidence:
[`artifacts/v48aligned_boundary/frozen.json`](artifacts/v48aligned_boundary/frozen.json).
