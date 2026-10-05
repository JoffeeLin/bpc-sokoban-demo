# Direction and axis deletion — pre-run freeze protocol

Baseline commit: 8b094311c5cbabca4aea9ff9ae613574cd21077d.
Start with its 369-entry field; only four new one-hop direction probabilities
may change. Learn each physical intervention from exact observed consequences,
without manually naming the correct direction, rankings, rewards or a player
heuristic. The source of experience is actual game execution under hand-written
anonymous action tapes. No artificial training boards.

Delete fixed +y displacement and the vertical-only relation/column scan.
Use direction-wave projection for address ordering and collinearity.

After freezing: require old eight world streams and newly reserved indices
20–23 (1,000 episodes, horizon 120); 10,000 bottom-row and 10,000 arbitrary-row
clear cases; 2,500 vertical non-clear controls; five score-free play streams,
seeds 20261025–20261029, each 10,000 pieces; field bytes unchanged.
Require direction erased/reflected/turned ablations to degrade closure; O2/O3
agreement and UBSan smoke. Check flipped-screen observations separately with
an independently trained four-probability wave and unchanged other couplings.
The reflected observations are from the same real game, not a second task.
These are developer-held-out seed checks, not an independent blind test.

Stop promotion if the small deletion fails. Preserve negative evidence. The
inherited State/trace roles, ordinal vocabulary, atomic effects and scheduling
remain scaffolds even if this direction-and-axis deletion succeeds.
