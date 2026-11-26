"""Tooling for the ANALOG CPU project.

The package reads the Qucs-S datasets committed alongside the schematics and
checks the simulated analogue gates against their digital reference truth
tables.

    python -m analog_cpu            # human-readable report
    python -m analog_cpu --json     # machine-readable report
"""

from .dataset import Dataset, digitize, find_runs, load_dataset, parse_dataset
from .gates import GATES, KNOWN_ISSUES, evaluate, truth_table
from .verify import GateReport, Observation, verify_all, verify_gate

__all__ = [
    "Dataset",
    "GATES",
    "KNOWN_ISSUES",
    "GateReport",
    "Observation",
    "digitize",
    "evaluate",
    "find_runs",
    "load_dataset",
    "parse_dataset",
    "truth_table",
    "verify_all",
    "verify_gate",
]

__version__ = "0.1.0"
