"""Reader for the Qucs-S/ngspice transient datasets used in this project.

A dataset file (``*.dat.ngspice``) has this shape::

    <Qucs Dataset 26.1.1>
    <indep time 3>
    0.0
    1.0e-6
    2.0e-6
    </indep>
    <dep tran.v(output) time>
    5.0
    5.0
    0.0
    </dep>

The parser intentionally has no third-party dependencies: it only needs the
standard library, which keeps the verification tooling usable in CI.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping, Sequence, Tuple

_INDEP_RE = re.compile(
    r"<\s*indep\s+(\S+)\s+(\d+)\s*>(.*?)<\s*/\s*indep\s*>", re.DOTALL
)
_DEP_RE = re.compile(
    r"<\s*dep\s+(\S+)\s+(\S+)\s*>(.*?)<\s*/\s*dep\s*>", re.DOTALL
)
_NODE_RE = re.compile(r"\(([^)]+)\)\s*$")


@dataclass(frozen=True)
class Run:
    """A contiguous stretch of samples with an identical input vector.

    ``end`` is exclusive, following Python slice conventions.
    """

    start: int
    end: int
    vector: Tuple[int, ...]

    @property
    def length(self) -> int:
        return self.end - self.start


@dataclass(frozen=True)
class Dataset:
    """A parsed transient dataset."""

    source: str
    independent_name: str
    independent: Tuple[float, ...]
    signals: Mapping[str, Tuple[float, ...]]

    def __len__(self) -> int:
        return len(self.independent)

    def signal(self, name: str) -> Tuple[float, ...]:
        """Return samples for *name*.

        Both the full Qucs name (``tran.v(output)``) and the short node name
        (``output``) are accepted.
        """
        key = short_name(name)
        try:
            return self.signals[key]
        except KeyError:
            available = ", ".join(sorted(self.signals)) or "none"
            raise KeyError(
                f"signal {name!r} not found in {self.source} (have: {available})"
            ) from None

    def duration(self) -> float:
        """Return the length of the simulation in seconds."""
        return self.independent[-1] - self.independent[0] if self.independent else 0.0


def short_name(raw: str) -> str:
    """Strip the Qucs decoration from a signal name.

    ``tran.v(INPUTA)`` becomes ``inputa``; plain names are lower-cased.
    """
    match = _NODE_RE.search(raw)
    return (match.group(1) if match else raw).lower()


def _numbers(text: str) -> Tuple[float, ...]:
    values = []
    for token in text.split():
        try:
            values.append(float(token))
        except ValueError as exc:
            raise ValueError(f"expected a number in dataset, got {token!r}") from exc
    return tuple(values)


def parse_dataset(text: str, source: str = "<text>") -> Dataset:
    """Parse the contents of a Qucs dataset file.

    Raises ``ValueError`` with a helpful message for malformed or unsupported
    files, so callers can report a broken dataset rather than silently
    producing wrong results.
    """
    if not re.match(r"\s*<\s*Qucs Dataset\b", text):
        raise ValueError(f"{source}: not a Qucs dataset file")

    independent_match = _INDEP_RE.search(text)
    if independent_match is None:
        raise ValueError(f"{source}: no <indep> section found")

    name, count_text, body = independent_match.groups()
    expected = int(count_text)
    time = _numbers(body)
    if len(time) != expected:
        raise ValueError(
            f"{source}: <indep {name} {expected}> contains {len(time)} samples"
        )
    if expected < 2:
        raise ValueError(f"{source}: dataset needs at least two samples")

    signals: Dict[str, Tuple[float, ...]] = {}
    for raw_name, independent_ref, dep_body in _DEP_RE.findall(text):
        if independent_ref != name:
            raise ValueError(
                f"{source}: signal {raw_name!r} uses {independent_ref!r}, "
                f"expected {name!r}"
            )
        values = _numbers(dep_body)
        if len(values) != expected:
            raise ValueError(
                f"{source}: signal {raw_name!r} has {len(values)} samples, "
                f"expected {expected}"
            )
        key = short_name(raw_name)
        if key in signals:
            raise ValueError(f"{source}: duplicate signal {raw_name!r}")
        signals[key] = values

    if not signals:
        raise ValueError(f"{source}: no <dep> signals found")

    return Dataset(source, name, time, signals)


def load_dataset(path: str | Path) -> Dataset:
    """Read and parse a dataset file from disk."""
    dataset_path = Path(path)
    return parse_dataset(dataset_path.read_text(encoding="utf-8"), str(dataset_path))


def digitize(
    values: Sequence[float], vdd: float = 5.0, low: float = 0.3, high: float = 0.7
) -> Tuple[int, ...]:
    """Convert an analogue waveform to 0/1 with Schmitt-trigger thresholds.

    ``low`` and ``high`` are fractions of ``vdd``. The hysteresis band stops
    noise around the switching point from being counted as extra transitions.
    """
    if not values:
        return ()
    if not 0 < low < high < 1:
        raise ValueError("require 0 < low < high < 1")

    low_level, high_level = low * vdd, high * vdd
    initial_high = values[0] > vdd / 2
    state = int(initial_high)
    bits = []
    for value in values:
        if value >= high_level:
            state = 1
        elif value <= low_level:
            state = 0
        bits.append(state)
    return tuple(bits)


def find_runs(vectors: Sequence[Sequence[int]]) -> Tuple[Run, ...]:
    """Group sample indices into runs of constant input vectors.

    ``vectors`` holds one digital signal per input, all with the same length.
    """
    if not vectors:
        return ()
    columns = list(zip(*vectors))
    runs = []
    start = 0
    for index in range(1, len(columns) + 1):
        if index == len(columns) or columns[index] != columns[start]:
            runs.append(Run(start, index, columns[start]))
            start = index
    return tuple(runs)
