# v0.21 horizon sweep limitation

The saved `horizon_sweep.json` is development-only. Its `oracle` rows are invalid:
the first run passed physical-frame actuator rows to a controller operating in the
selected D4 gauge. The online, memoryless, no-update, shuffled, and zero-lag rows
do not use that oracle input and remain useful only for development sensitivity.
The script now contains the frame correction, but the sweep was not rerun and is
not admissible as frozen evidence.
