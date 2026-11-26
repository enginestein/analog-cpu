"""Compare simulated gate waveforms with their ideal truth tables.

The simulator produces a continuous transient waveform; digital inputs are
stable only in windows between stimulus edges. For each stable window we take
a majority vote over the settled tail of the output waveform, then compare it
with the reference model. Windows shorter than ``min_samples`` are ignored so
that edge transitions are not mistaken for logic states.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Sequence, Tuple

from .dataset import Dataset, digitize, find_runs, load_dataset
from .gates import GATES, KNOWN_ISSUES, evaluate, truth_table

DEFAULT_ROOT = Path(__file__).resolve().parent.parent
STATUSES = ("pass", "partial", "xfail", "fail", "missing", "error")


@dataclass(frozen=True)
class Observation:
    """One stable input window and the output measured in it."""

    inputs: Tuple[int, ...]
    expected: int
    observed: int
    start: float
    end: float
    samples: int

    @property
    def matches(self) -> bool:
        return self.observed == self.expected


@dataclass
class GateReport:
    """Result of checking one gate dataset."""

    name: str
    status: str
    observations: List[Observation] = field(default_factory=list)
    covered: int = 0
    total: int = 0
    note: str = ""

    @property
    def ok(self) -> bool:
        """Whether this result is acceptable in a normal (non-strict) run."""
        return self.status in {"pass", "partial", "xfail"}


def verify_gate(
    name: str,
    dataset: Dataset,
    *,
    vdd: float = 5.0,
    min_samples: int = 8,
    tail_fraction: float = 0.3,
) -> GateReport:
    """Check one parsed dataset against the reference model for *name*."""
    spec = GATES[name]  # raises KeyError for unknown gates
    if not 0 < tail_fraction < 1:
        raise ValueError("tail_fraction must be between 0 and 1")

    input_bits = tuple(digitize(dataset.signal(signal), vdd) for signal in spec.inputs)
    output_bits = digitize(dataset.signal(spec.output), vdd)

    observations: List[Observation] = []
    for run in find_runs(input_bits):
        if run.length < min_samples:
            continue
        tail_start = run.start + int(run.length * (1.0 - tail_fraction))
        tail_start = min(tail_start, run.end - 1)
        tail = output_bits[tail_start : run.end]
        observed = 1 if 2 * sum(tail) > len(tail) else 0
        observations.append(
            Observation(
                inputs=run.vector,
                expected=evaluate(name, run.vector),
                observed=observed,
                start=dataset.independent[run.start],
                end=dataset.independent[run.end - 1],
                samples=len(tail),
            )
        )

    # Repeated windows should agree. If they do not, keep the failing one so
    # an intermittent fault cannot be averaged away.
    by_vector = {}
    for observation in observations:
        previous = by_vector.get(observation.inputs)
        if previous is None or (not observation.matches and previous.matches):
            by_vector[observation.inputs] = observation
    observations = sorted(by_vector.values(), key=lambda item: item.inputs)

    failures = [item for item in observations if not item.matches]
    total = len(truth_table(name))
    covered = len(observations)

    if failures and name in KNOWN_ISSUES:
        status, note = "xfail", KNOWN_ISSUES[name]
    elif failures:
        status = "fail"
        note = "; ".join(
            "in=" + "".join(map(str, item.inputs)) + f" expected {item.expected}, got {item.observed}"
            for item in failures
        )
    elif covered < total:
        status = "partial"
        missing = [
            "".join(map(str, vector))
            for vector, _ in truth_table(name)
            if vector not in by_vector
        ]
        note = "stimulus does not cover input vector(s): " + ", ".join(missing)
    else:
        status, note = "pass", ""

    return GateReport(name, status, observations, covered, total, note)


def verify_all(
    root: str | Path = DEFAULT_ROOT,
    *,
    vdd: float = 5.0,
    min_samples: int = 8,
    tail_fraction: float = 0.3,
) -> Tuple[GateReport, ...]:
    """Verify every known gate whose dataset is present in *root*."""
    root_path = Path(root)
    reports = []
    for name in GATES:
        dataset_path = root_path / f"{name}.dat.ngspice"
        if not dataset_path.is_file():
            reports.append(
                GateReport(name, "missing", note=f"no dataset at {dataset_path}")
            )
            continue
        try:
            dataset = load_dataset(dataset_path)
            report = verify_gate(
                name,
                dataset,
                vdd=vdd,
                min_samples=min_samples,
                tail_fraction=tail_fraction,
            )
        except (OSError, ValueError, KeyError) as exc:
            report = GateReport(name, "error", note=str(exc))
        reports.append(report)
    return tuple(reports)


def summarize(reports: Sequence[GateReport], *, strict: bool = False) -> bool:
    """Print a report table and return whether all gates passed.

    In strict mode expected failures (XFAIL) and incomplete stimulus coverage
    are treated as failures too.
    """
    print(f"{'Gate':<16} {'Status':<8} {'Coverage':<9} Details")
    print("-" * 78)
    for report in reports:
        coverage = f"{report.covered}/{report.total}"
        print(f"{report.name:<16} {report.status.upper():<8} {coverage:<9} {report.note}")

    acceptable = {"pass"} if strict else {"pass", "partial", "xfail"}
    unexpected = [report.name for report in reports if report.status not in acceptable]
    print("-" * 78)
    if unexpected:
        print("Unexpected result(s): " + ", ".join(unexpected))
        return False
    print("All gate checks passed" + (" (strict)" if strict else " (known issues allowed)"))
    return True
