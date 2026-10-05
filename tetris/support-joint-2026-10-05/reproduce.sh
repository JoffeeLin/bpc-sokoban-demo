#!/usr/bin/env bash
set -eu
task_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
task_mode=${1:-quick}
task_out=${2:-results}
cd "$task_root"
mkdir -p "$task_out"
task_out=$(CDPATH= cd -- "$task_out" && pwd)
for readout in 0 1 2; do
    cc -std=c11 -O2 -Wall -Wextra -Wpedantic -Werror -DMODE="$readout" audit.c -lm -o "$task_out/audit_$readout"
    cc -std=c11 -O2 -Wall -Wextra -Wpedantic -Werror -DMODE="$readout" pilot.c -lm -o "$task_out/pilot_$readout"
    cc -std=c11 -O2 -Wall -Wextra -Wpedantic -Werror -DMODE="$readout" diagnose.c -lm -o "$task_out/diagnose_$readout"
    mkdir -p "$task_out/pair_$readout"
    (cd "$task_out/pair_$readout"; "$task_out/audit_$readout" pair > pair.txt)
done
cc -std=c11 -O3 -Wall -Wextra -Wpedantic -Werror -DMODE=2 audit.c -lm -o "$task_out/audit_2_O3"
cc -std=c11 -O1 -g -Wall -Wextra -Wpedantic -Werror -DMODE=2 -fsanitize=undefined -fno-sanitize-recover=all audit.c -lm -o "$task_out/audit_2_ubsan"
for variant in O3 ubsan; do
    mkdir -p "$task_out/${variant}_pair"
    (cd "$task_out/${variant}_pair"; "$task_out/audit_2_$variant" pair > pair.txt 2> stderr.txt)
done
python3 verify.py quick "$task_out"
if [ "$task_mode" = quick ]; then exit 0; fi
if [ "$task_mode" != full ]; then echo 'usage: reproduce.sh quick|full [output-directory]' >&2; exit 2; fi

# Serial full runs keep peak RAM near a single model's allocation budget.
for readout in 0 1 2; do
    "$task_out/pilot_$readout" > "$task_out/pilot_$readout.txt"
    "$task_out/audit_$readout" learn "$task_out/full_$readout.bin" 1 20000 55901 > "$task_out/full_${readout}_training.txt"
    "$task_out/audit_$readout" eval "$task_out/full_$readout.bin" 0 8 1000 120 0 > "$task_out/full_${readout}_old_self.txt"
    "$task_out/audit_$readout" eval "$task_out/full_$readout.bin" 28 4 1000 120 0 > "$task_out/full_${readout}_new_self.txt"
    "$task_out/audit_$readout" eval "$task_out/full_$readout.bin" 28 4 100 120 1 > "$task_out/full_${readout}_teacher.txt"
    "$task_out/audit_$readout" play "$task_out/full_$readout.bin" 10000 5 20261121 0 > "$task_out/full_${readout}_play.txt"
    "$task_out/audit_$readout" controls "$task_out/full_$readout.bin" > "$task_out/full_${readout}_controls.txt"
    "$task_out/diagnose_$readout" "$task_out/full_$readout.bin" > "$task_out/diagnose_$readout.txt"
done
"$task_out/audit_2_O3" learn "$task_out/full_2_O3.bin" 1 20000 55901 > "$task_out/full_2_O3_training.txt"
cmp "$task_out/full_2.bin" "$task_out/full_2_O3.bin" > "$task_out/O2_O3_field_cmp.txt"
for variant in 2 2_O3 2_ubsan; do
    "$task_out/audit_$variant" eval "$task_out/full_2.bin" 28 1 100 120 0 > "$task_out/${variant}_smoke_eval.txt" 2> "$task_out/${variant}_smoke_stderr.txt"
    "$task_out/audit_$variant" play "$task_out/full_2.bin" 1000 1 20261121 0 > "$task_out/${variant}_smoke_play.txt" 2>> "$task_out/${variant}_smoke_stderr.txt"
done
task_baseline=${BPC_BASELINE_DIR:-"$task_root/../direction-axis-2026-10-05"}
cc -std=c11 -O2 -Wall -Wextra -Wpedantic -Werror "$task_baseline/audit.c" -lm -o "$task_out/audit_baseline"
"$task_out/audit_baseline" eval "$task_baseline/field.bin" 28 4 1000 0 0 120 > "$task_out/baseline_new_self.txt"
python3 verify.py full "$task_out"
