#!/usr/bin/env bash
# Regenerate ngspice netlists from every Qucs-S schematic in the repository.
# Output goes to build/netlists/ by default (ignored by git).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="${1:-$repo_root/build/netlists}"

if ! command -v qucs-s >/dev/null 2>&1; then
    echo "qucs-s not found; install Qucs-S to regenerate netlists" >&2
    exit 1
fi

mkdir -p "$output_dir"
for schematic in "$repo_root"/CMOS_*.sch; do
    name="$(basename "$schematic" .sch)"
    netlist="$output_dir/netlist_${name}.cir"
    qucs-s -n --ngspice -i "$schematic" -o "$netlist" >/dev/null 2>&1
    echo "generated $netlist"
done
