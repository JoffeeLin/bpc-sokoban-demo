# BPC v0.47 aligned phase-one development result

Status: **PASS / AUTHORIZE ONE INDEPENDENT FREEZE**.

The first execution passed every preregistered gate after correcting the camera
stride. Across 2,304 fresh joint-world transitions, 37.99% of full action/local
contexts were unseen. Defined-bit Brier was 0.00327, changed-bit Brier was
0.04830, and unseen-changed Brier was 0.07305. On changed and unseen-changed
bits the candidate improved over action removal by 83.19% and 77.25%; the
corresponding improvements over action rotation were 92.29% and 88.57%.

The 2^20-cell medium used 11,720 active addresses for 2,719 unique training
states. Evaluation made zero writes and preserved both digests. All 87 unit
tests, including explicit coordinate, padding, physical-neighbor and rotation
checks, passed before execution.

This is development evidence for correctly aligned one-step physical
prediction. It is not yet frozen evidence, goal behavior, Sokoban solving,
cross-domain transfer, or AGI. The only authorized next step is one
separately preregistered fresh-seed reproduction with unchanged gates.
