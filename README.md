# ANALOG CPU

A work-in-progress CPU built from discrete CMOS gates in **Qucs-S 26.1.1** and
simulated with **ngspice**. The original schematics and simulation datasets are
kept here alongside a small software/HDL reference design, so the analogue
behaviour can be checked against ideal Boolean logic automatically.

## Repository contents

| Path | Description |
| --- | --- |
| `CMOS_*.sch` | Qucs-S schematics (INVERTER, AND, NAND, NOR, OR) |
| `CMOS_*.dat.ngspice` | Transient simulation datasets produced by Qucs-S |
| `netlist_CMOS_NOR.cir` | Example generated ngspice netlist |
| `analog_cpu/` | Dependency-free Python verification tooling |
| `hdl/` | Verilog reference gates, ALU and tiny CPU, with testbenches |
| `tools/` | Netlist regeneration, HDL test runner, optional Octave plotting |
| `tests/` | Python unit tests |

## Current gate status

Run `python -m analog_cpu` to reproduce this summary:

```text
Gate             Status   Coverage  Details
------------------------------------------------------------------------------
CMOS_INVERTER    XFAIL    2/2       PMOS drain not connected to OUTPUT
CMOS_AND         PARTIAL  2/4       stimulus does not cover 01, 10
CMOS_NAND        PASS     4/4
CMOS_NOR         PASS     4/4
CMOS_OR          PARTIAL  2/4       stimulus does not cover 01, 10
```

`PARTIAL` means every *observed* input combination was correct, but the test
bench did not exercise all combinations. `XFAIL` is a documented known issue;
`python -m analog_cpu --strict` treats both as failures.

## Known issues

1. **CMOS_INVERTER output is stuck low.** The generated ngspice netlist contains
   `MT1 _net1 INPUT _net0 ...` and `MT2 OUTPUT INPUT 0 0`: the PMOS drain
   (`_net1`) is never connected to `OUTPUT`. Join T1's drain to the output node
   in `CMOS_INVERTER.sch` and re-run the simulation. Until then this gate is
   marked as an expected failure in `analog_cpu/gates.py`.
2. **AND and OR stimuli only cover two of four input states.** Both pulse
   sources start at the same time and have the same period, so only `00` and
   `11` appear. Stagger one source by half a period, as done in the NAND and
   NOR schematics, to exercise `01` and `10`.
3. **CMOS_OR internal node is marginal.** With `A = B = 0`, node `N` settles at
   about 3.83 V instead of the full 5 V; the generated netlist ties the second
   PMOS drain to ground (`MT2 0 B N N`). Check the series PMOS pull-up wiring
   in `CMOS_OR.sch`. The final output is still correct for the tested vectors.

## Python verification tooling

Requires Python 3.9 or newer; no third-party packages.

```bash
python -m analog_cpu                 # table of results; exits 0 with known issues allowed
python -m analog_cpu --strict        # fail on XFAIL/PARTIAL too
python -m analog_cpu --json          # machine-readable output
python -m unittest discover -s tests # unit tests
```

The checker digitises each waveform with Schmitt-trigger thresholds (30 % and
70 % of VDD), finds stable windows of the digital inputs, and takes a majority
vote over the settled tail of the output. Short transition windows are ignored.
It then compares the observation with the ideal truth table in
`analog_cpu/gates.py`.

## HDL reference design

The Verilog model is a digital counterpart to the CMOS gates, not a transistor
model. It is useful for checking that the intended logic is sound and for
experimenting with a CPU datapath built from those gates.

| File | Contents |
| --- | --- |
| `hdl/gates.v` | NOT, NAND, NOR, AND, OR, XOR (AND/OR mirror the two-stage CMOS schematics) |
| `hdl/full_adder.v` | One bit of a ripple-carry adder |
| `hdl/alu.v` | 4-bit ALU: pass, add, subtract, AND, OR, XOR, NOT, zero/carry flags |
| `hdl/cpu.v` | 4-bit accumulator CPU, 16-word program ROM and data RAM |
| `hdl/program.hex`, `hdl/program_branch.hex` | Small test programs |
| `hdl/tb_*.v` | Self-checking testbenches |

Run all testbenches with Icarus Verilog:

```bash
./tools/run_hdl_tests.sh     # or: make -C hdl test
```

Instruction words are `{opcode[7:4], operand[3:0]}`:

| Opcode | Instruction | Action |
| --- | --- | --- |
| `0` | `LDI imm` | `acc <= imm` |
| `1` | `ADD imm` | `acc <= acc + imm` |
| `2` | `SUB imm` | `acc <= acc - imm` |
| `3` | `AND imm` | `acc <= acc & imm` |
| `4` | `OR imm` | `acc <= acc | imm` |
| `5` | `XOR imm` | `acc <= acc ^ imm` |
| `6` | `NOT` | `acc <= ~acc` |
| `7` | `STA addr` | `mem[addr] <= acc` |
| `8` | `LDA addr` | `acc <= mem[addr]` |
| `9` | `JMP addr` | `pc <= addr` |
| `A` | `JZ addr` | branch if `acc == 0` |
| `F` | `HLT` | stop |

Each instruction takes two clock cycles (FETCH, EXECUTE).

## Regenerating netlists and plotting waveforms

```bash
./tools/regenerate_netlists.sh              # writes build/netlists/netlist_CMOS_*.cir
qucs-s -n --ngspice -i CMOS_NAND.sch -o netlist_CMOS_NAND.cir   # single schematic
ngspice netlist_CMOS_NAND.cir                                  # run a netlist

# Optional GNU Octave plotting helper:
octave --quiet --eval "addpath('tools'); plot_waveforms('CMOS_NAND.dat.ngspice')"
```

## License

MIT — see [LICENSE](LICENSE).
