#!/usr/bin/env bash
set -eu
task_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
mode=${1:-quick}
task_out=${2:-results}
cd "$task_root"
mkdir -p "$task_out"
task_out=$(CDPATH= cd -- "$task_out" && pwd)
for variant in O2 O3 ubsan local; do mkdir -p "$task_out/$variant"; done
cc -std=c11 -O2 -Wall -Wextra -Wpedantic -Werror audit.c -o "$task_out/audit_O2"
cc -std=c11 -O3 -Wall -Wextra -Wpedantic -Werror audit.c -o "$task_out/audit_O3"
cc -std=c11 -O1 -g -Wall -Wextra -Wpedantic -Werror -fsanitize=undefined -fno-sanitize-recover=all audit.c -o "$task_out/audit_ubsan"
cc -std=c11 -O2 -Wall -Wextra -Wpedantic -Werror -DGLOBAL_SUPPORT=0 audit.c -o "$task_out/audit_local"
for variant in O2 O3 ubsan local; do
    (cd "$task_out/$variant"; "$task_out/audit_$variant" pair > pair.txt 2> stderr.txt)
done
python3 verify.py quick "$task_out"
if [ "$mode" = quick ]; then exit 0; fi
if [ "$mode" != full ]; then echo "usage: reproduce.sh quick|full [output-directory]" >&2; exit 2; fi

"$task_out/audit_O2" learn "$task_out/memory.bin" 1 20000 55901 > "$task_out/memory_training.txt"
"$task_out/audit_O2" learn "$task_out/raw.bin" 0 20000 55901 > "$task_out/raw_training.txt"
for variant in memory raw; do
    "$task_out/audit_O2" eval "$task_out/$variant.bin" 0 8 1000 120 0 > "$task_out/${variant}_original_self.txt"
    "$task_out/audit_O2" eval "$task_out/$variant.bin" 24 4 1000 120 0 > "$task_out/${variant}_reserved_self.txt"
    "$task_out/audit_O2" play "$task_out/$variant.bin" 10000 5 20261030 0 > "$task_out/${variant}_reserved_play.txt"
    "$task_out/audit_O2" controls "$task_out/$variant.bin" > "$task_out/${variant}_controls.txt"
done
"$task_out/audit_O2" eval "$task_out/memory.bin" 24 4 1000 120 1 > "$task_out/memory_teacher.txt"
"$task_out/audit_O3" learn "$task_out/O3_memory.bin" 1 20000 55901 > "$task_out/O3_training.txt"
cmp "$task_out/memory.bin" "$task_out/O3_memory.bin"
for variant in O2 O3 ubsan; do
    "$task_out/audit_$variant" eval "$task_out/memory.bin" 24 1 100 120 0 > "$task_out/${variant}_eval.txt" 2>> "$task_out/$variant/stderr.txt"
    "$task_out/audit_$variant" play "$task_out/memory.bin" 1000 1 20261030 0 > "$task_out/${variant}_play.txt" 2>> "$task_out/$variant/stderr.txt"
done
task_baseline=${BPC_BASELINE_DIR:-"$task_root/../direction-axis-2026-10-05"}
cc -std=c11 -O2 -Wall -Wextra -Wpedantic -Werror "$task_baseline/audit.c" -lm -o "$task_out/audit_baseline"
"$task_out/audit_baseline" eval "$task_baseline/field.bin" 24 4 1000 0 0 120 > "$task_out/baseline_reserved_self.txt"
python3 verify.py full "$task_out"
