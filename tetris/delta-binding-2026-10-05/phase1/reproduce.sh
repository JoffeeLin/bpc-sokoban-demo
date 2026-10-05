#!/usr/bin/env bash
set -eu
task_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
task_mode=${1:-quick}
task_out=${2:-results}
cd "$task_root"
mkdir -p "$task_out"
task_out=$(CDPATH= cd -- "$task_out" && pwd)
for spec in 'priority 0 0 0' 'next 2 0 0' 'delta 2 1 0' 'split_next 2 0 1' 'split_delta 2 1 1'; do
    read -r label mode encoding bind <<< "$spec"
    cc -std=c11 -O2 -Wall -Wextra -Wpedantic -Werror -DMODE="$mode" -DDELTA="$encoding" -DBIND_CURRENT="$bind" audit.c -lm -o "$task_out/audit_$label"
    cc -std=c11 -O2 -Wall -Wextra -Wpedantic -Werror -DMODE="$mode" -DDELTA="$encoding" -DBIND_CURRENT="$bind" pilot.c -lm -o "$task_out/pilot_$label"
    cc -std=c11 -O2 -Wall -Wextra -Wpedantic -Werror -DMODE="$mode" -DDELTA="$encoding" -DBIND_CURRENT="$bind" diagnose.c -lm -o "$task_out/diagnose_$label"
    mkdir -p "$task_out/pair_$label"
    (cd "$task_out/pair_$label"; "$task_out/audit_$label" pair > pair.txt)
done
cc -std=c11 -O3 -Wall -Wextra -Wpedantic -Werror audit.c -lm -o "$task_out/audit_candidate_O3"
cc -std=c11 -O1 -g -Wall -Wextra -Wpedantic -Werror -fsanitize=undefined -fno-sanitize-recover=all audit.c -lm -o "$task_out/audit_candidate_ubsan"
for variant in O3 ubsan; do
    mkdir -p "$task_out/${variant}_pair"
    (cd "$task_out/${variant}_pair"; "$task_out/audit_candidate_$variant" pair > pair.txt 2> stderr.txt)
done
if "$task_out/audit_next" eval "$task_out/pair_split_delta/pair_memory.bin" 32 1 1 120 0 > "$task_out/header_mismatch_stdout.txt" 2> "$task_out/header_mismatch_stderr.txt"; then
    echo 'mismatched target/query field accepted' >&2; exit 2
fi
python3 verify.py quick "$task_out"
if [ "$task_mode" = quick ]; then exit 0; fi
if [ "$task_mode" != full ]; then echo 'usage: reproduce.sh quick|full [output-directory]' >&2; exit 2; fi

# Independent models run serially to keep peak memory within one allocation.
for label in next delta split_next split_delta; do
    "$task_out/pilot_$label" > "$task_out/pilot_$label.txt"
done
for label in priority next split_next split_delta; do
    "$task_out/audit_$label" learn "$task_out/full_$label.bin" 1 20000 55901 > "$task_out/full_${label}_training.txt"
    "$task_out/audit_$label" eval "$task_out/full_$label.bin" 32 4 1000 120 0 > "$task_out/full_${label}_self.txt"
    "$task_out/audit_$label" eval "$task_out/full_$label.bin" 32 4 100 120 1 > "$task_out/full_${label}_teacher.txt"
    "$task_out/audit_$label" play "$task_out/full_$label.bin" 10000 5 20261151 0 > "$task_out/full_${label}_play.txt"
    "$task_out/audit_$label" controls "$task_out/full_$label.bin" > "$task_out/full_${label}_controls.txt"
    "$task_out/diagnose_$label" "$task_out/full_$label.bin" > "$task_out/diagnose_$label.txt"
done
"$task_out/audit_candidate_O3" learn "$task_out/full_candidate_O3.bin" 1 20000 55901 > "$task_out/full_candidate_O3_training.txt"
cmp "$task_out/full_split_delta.bin" "$task_out/full_candidate_O3.bin" > "$task_out/O2_O3_field_cmp.txt"
for variant in split_delta candidate_O3 candidate_ubsan; do
    "$task_out/audit_$variant" eval "$task_out/full_split_delta.bin" 32 1 100 120 0 > "$task_out/${variant}_smoke_eval.txt" 2> "$task_out/${variant}_smoke_stderr.txt"
    "$task_out/audit_$variant" play "$task_out/full_split_delta.bin" 1000 1 20261151 0 > "$task_out/${variant}_smoke_play.txt" 2>> "$task_out/${variant}_smoke_stderr.txt"
done
task_baseline=${BPC_BASELINE_DIR:-"$task_root/../direction-axis-2026-10-05"}
cc -std=c11 -O2 -Wall -Wextra -Wpedantic -Werror "$task_baseline/audit.c" -lm -o "$task_out/audit_baseline"
"$task_out/audit_baseline" eval "$task_baseline/field.bin" 32 4 1000 0 0 120 > "$task_out/baseline_new_self.txt"
python3 verify.py full "$task_out"
