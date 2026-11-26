"""Digital reference models for the CMOS gates drawn in Qucs-S.

Each :class:`GateSpec` names the signals in the corresponding
``CMOS_*.dat.ngspice`` dataset and gives the ideal Boolean function. The
reference model is deliberately independent of the simulation: the whole point
of :mod:`analog_cpu.verify` is to compare the two.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Callable, Tuple


@dataclass(frozen=True)
class GateSpec:
    """Description of one simulated gate."""

    inputs: Tuple[str, ...]
    output: str
    function: Callable[..., int]
    description: str
    intermediates: Tuple[str, ...] = ()


GATES = {
    "CMOS_INVERTER": GateSpec(
        ("input",),
        "output",
        lambda a: 1 - a,
        "single CMOS inverter (one PMOS, one NMOS)",
    ),
    "CMOS_AND": GateSpec(
        ("inputa", "inputb"),
        "outputy",
        lambda a, b: a & b,
        "NAND stage (NODEN) followed by an inverter",
        ("noden",),
    ),
    "CMOS_NAND": GateSpec(
        ("inputa", "inputb"),
        "output",
        lambda a, b: 1 - (a & b),
        "parallel PMOS pull-up, series NMOS pull-down",
    ),
    "CMOS_NOR": GateSpec(
        ("inputa", "inputb"),
        "output",
        lambda a, b: 1 - (a | b),
        "series PMOS pull-up, parallel NMOS pull-down",
    ),
    "CMOS_OR": GateSpec(
        ("a", "b"),
        "y",
        lambda a, b: a | b,
        "NOR stage (N) followed by an inverter",
        ("n",),
    ),
}


#: Simulated gates with a diagnosed schematic problem. They are reported as
#: XFAIL (expected failure) until the schematic is fixed. This is not a way of
#: hiding the problem -- the reason is printed by the CLI and in the README.
KNOWN_ISSUES = {
    "CMOS_INVERTER": (
        "PMOS drain (net _net1 in the generated ngspice netlist) is not "
        "connected to OUTPUT; the simulated output stays at 0 V. Wire T1's "
        "drain to the OUTPUT node in CMOS_INVERTER.sch."
    ),
}


def evaluate(gate: str, inputs: Tuple[int, ...]) -> int:
    """Evaluate the ideal Boolean function of *gate*."""
    try:
        spec = GATES[gate]
    except KeyError:
        raise KeyError(f"unknown gate {gate!r}; have: {', '.join(GATES)}") from None
    if len(inputs) != len(spec.inputs):
        raise ValueError(
            f"{gate} expects {len(spec.inputs)} inputs, got {len(inputs)}"
        )
    return spec.function(*inputs)


def truth_table(gate: str) -> Tuple[Tuple[Tuple[int, ...], int], ...]:
    """Return all input vectors of *gate* with their expected outputs."""
    spec = GATES[gate]  # raises KeyError for unknown gates
    return tuple(
        (vector, spec.function(*vector))
        for vector in product((0, 1), repeat=len(spec.inputs))
    )
