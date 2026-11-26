#!/usr/bin/env bash
# Compile and run every self-checking Verilog testbench with Icarus Verilog.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
hdl_dir="$repo_root/hdl"
build_dir="$(mktemp -d "${TMPDIR:-/tmp}/analog-cpu-hdl.XXXXXX")"
trap 'rm -rf "$build_dir"' EXIT

if ! command -v iverilog >/dev/null 2>&1 || ! command -v vvp >/dev/null 2>&1; then
    echo "iverilog/vvp not found; install Icarus Verilog to run HDL tests" >&2
    exit 1
fi

sources=(gates.v full_adder.v alu.v cpu.v)
testbenches=(tb_gates tb_alu tb_cpu tb_branch)
status=0

cd "$hdl_dir"
for tb in "${testbenches[@]}"; do
    if ! iverilog -g2012 -s "$tb" -o "$build_dir/$tb" "${sources[@]}" "$tb.v"; then
        echo "ERROR $tb: compilation failed"
        status=1
        continue
    fi
    if vvp "$build_dir/$tb" > "$build_dir/$tb.log" 2>&1 \
        && grep -q 'PASS' "$build_dir/$tb.log" \
        && ! grep -q 'FAIL' "$build_dir/$tb.log"; then
        echo "PASS $tb"
    else
        echo "FAIL $tb"
        cat "$build_dir/$tb.log"
        status=1
    fi
done

exit "$status"
