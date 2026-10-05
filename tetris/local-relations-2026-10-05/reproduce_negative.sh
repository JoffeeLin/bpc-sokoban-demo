#!/bin/sh
# This native C field snapshot assumes the original Linux ABI.
set -eu
cd "$(dirname "$0")"
mkdir -p build
compiler=${CC:-cc}
"$compiler" -std=c11 -O2 -Wall -Wextra -Werror -pedantic -I. '-DCORE="evidence/negative_model.c"' audit.c -lm -o build/audit_negative
"$compiler" -std=c11 -O2 -Wall -Wextra -Werror -pedantic audit.c -lm -o build/audit
if ./build/audit_negative autoplay evidence/negative_field.bin 1000 1 20261010 > build/negative_reproduced.txt; then
    printf 'Unexpected negative pass. Inspect ABI and raw logs.\n' >&2
    exit 1
else
    status=$?
    test "$status" -eq 1
fi
./build/audit autoplay evidence/negative_field.bin 1000 5 20261010 > build/same_field_repair.txt
cat build/negative_reproduced.txt
cat build/same_field_repair.txt
printf 'Old failure and same-field executor repair reproduced.\n'
