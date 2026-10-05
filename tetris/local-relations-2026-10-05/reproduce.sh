#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p build
compiler=${CC:-cc}
"$compiler" -std=c11 -O2 -Wall -Wextra -Werror -pedantic audit.c -lm -o build/audit
./build/audit train build/field.bin > build/training.txt
./build/audit eval build/field.bin 0 8 1000 2500 2500 120 > build/original_worlds.txt
./build/audit eval build/field.bin 16 4 1000 0 0 120 > build/reserved_worlds.txt
./build/audit autoplay build/field.bin 1000 5 20261020 > build/reserved_autoplay.txt
./build/audit gap build/field.bin 2500 > build/arbitrary_clear.txt
./build/audit controls build/field.bin > build/controls.txt
./build/audit autoplay build/field.bin 1000 5 20261010 > build/counterexample_regression.txt
"$compiler" -std=c11 -O1 -g -Wall -Wextra -Werror -pedantic -fsanitize=undefined -fno-sanitize-recover=all audit.c -lm -o build/audit_ubsan
./build/audit_ubsan eval build/field.bin 8 1 100 100 100 120 > build/ubsan.txt 2> build/ubsan_stderr.txt
test ! -s build/ubsan_stderr.txt
"$compiler" -std=c11 -O3 -Wall -Wextra -Werror -pedantic audit.c -lm -o build/audit_O3
./build/audit eval build/field.bin 0 2 300 500 500 120 > build/O2.txt
./build/audit_O3 eval build/field.bin 0 2 300 500 500 120 > build/O3.txt
sed 's/ CPU_SECONDS=[0-9.]*//' build/O2.txt > build/O2_normalized.txt
sed 's/ CPU_SECONDS=[0-9.]*//' build/O3.txt > build/O3_normalized.txt
cmp build/O2_normalized.txt build/O3_normalized.txt
printf 'All frozen checks passed. Raw logs are in build/.\n'
