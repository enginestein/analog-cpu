"""Tests for the Qucs dataset reader and waveform helpers."""

from __future__ import annotations

import unittest
from pathlib import Path

from analog_cpu.dataset import (
    Dataset,
    digitize,
    find_runs,
    load_dataset,
    parse_dataset,
)

ROOT = Path(__file__).resolve().parents[1]

SAMPLE_DATASET = """<Qucs Dataset 26.1.1>
<indep time 6>
0.0
1.0e-6
2.0e-6
3.0e-6
4.0e-6
5.0e-6
</indep>
<dep tran.v(INPUTA) time>
0.0
0.0
0.0
5.0
5.0
5.0
</dep>
<dep tran.v(output) time>
5.0
5.0
4.99
0.0
0.01
0.0
</dep>
"""


class ParseDatasetTests(unittest.TestCase):
    def test_parses_header_signals_and_samples(self) -> None:
        data = parse_dataset(SAMPLE_DATASET, "sample.dat")

        self.assertEqual(data.independent_name, "time")
        self.assertEqual(len(data), 6)
        self.assertAlmostEqual(data.duration(), 5e-6)
        self.assertEqual(data.signal("inputa"), (0.0, 0.0, 0.0, 5.0, 5.0, 5.0))
        self.assertEqual(data.signal("tran.v(output)"), data.signal("output"))

    def test_unknown_signal_lists_available_names(self) -> None:
        data = parse_dataset(SAMPLE_DATASET)
        with self.assertRaisesRegex(KeyError, "have: inputa, output"):
            data.signal("missing")

    def test_rejects_non_dataset_text(self) -> None:
        with self.assertRaisesRegex(ValueError, "not a Qucs dataset"):
            parse_dataset("hello\n")

    def test_rejects_signal_with_wrong_length(self) -> None:
        broken = SAMPLE_DATASET.replace("0.01\n0.0\n</dep>", "0.01\n</dep>")
        with self.assertRaisesRegex(ValueError, "has 5 samples, expected 6"):
            parse_dataset(broken)

    def test_rejects_non_numeric_sample(self) -> None:
        broken = SAMPLE_DATASET.replace("5.0e-6\n</indep>", "oops\n</indep>")
        with self.assertRaisesRegex(ValueError, "expected a number"):
            parse_dataset(broken)

    def test_loads_every_committed_dataset(self) -> None:
        paths = sorted(ROOT.glob("CMOS_*.dat.ngspice"))
        self.assertEqual(len(paths), 5)
        for path in paths:
            with self.subTest(path=path.name):
                data = load_dataset(path)
                self.assertGreater(len(data), 100)
                self.assertTrue(data.signals)


class DigitizeTests(unittest.TestCase):
    def test_converts_levels_with_hysteresis(self) -> None:
        # With Vdd = 5 V the thresholds are 1.5 V and 3.5 V: 4 V switches
        # high, then 3 V stays high because it is inside the hysteresis band.
        values = (0.0, 1.0, 4.0, 3.0, 5.0, 2.0)
        self.assertEqual(digitize(values), (0, 0, 1, 1, 1, 1))

    def test_empty_input(self) -> None:
        self.assertEqual(digitize(()), ())

    def test_rejects_bad_thresholds(self) -> None:
        with self.assertRaises(ValueError):
            digitize((0.0, 5.0), low=0.8, high=0.2)


class FindRunsTests(unittest.TestCase):
    def test_groups_equal_vectors(self) -> None:
        # Two input signals, five samples each.
        vectors = ((0, 0, 0, 1, 1), (0, 0, 1, 1, 1))
        runs = find_runs(vectors)
        self.assertEqual([(run.start, run.end, run.vector) for run in runs], [
            (0, 2, (0, 0)),
            (2, 3, (0, 1)),
            (3, 5, (1, 1)),
        ])
        self.assertEqual([run.length for run in runs], [2, 1, 2])

    def test_accepts_empty_input(self) -> None:
        self.assertEqual(find_runs(()), ())


if __name__ == "__main__":
    unittest.main()
