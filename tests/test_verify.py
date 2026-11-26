"""Tests for truth-table verification of simulated datasets."""

from __future__ import annotations

import unittest
from pathlib import Path

from analog_cpu.dataset import Dataset
from analog_cpu.verify import verify_all, verify_gate

ROOT = Path(__file__).resolve().parents[1]


def make_dataset(inputs, output, duration=1e-3) -> Dataset:
    count = len(output)
    time = tuple(duration * i / (count - 1) for i in range(count))
    return Dataset("<synthetic>", "time", time, {"input": tuple(inputs), "output": tuple(output)})


class VerifyGateTests(unittest.TestCase):
    def test_detects_correct_inverter_behaviour(self) -> None:
        # Six low samples followed by six high samples; the output inverts one
        # sample later, mimicking propagation delay.
        data = make_dataset([0] * 6 + [5] * 6, [5] * 7 + [0] * 5)
        report = verify_gate("CMOS_INVERTER", data, min_samples=4)
        self.assertEqual(report.status, "pass")
        self.assertEqual(report.covered, 2)
        self.assertTrue(all(item.matches for item in report.observations))

    def test_detects_wrong_output(self) -> None:
        # Output stuck low, like the current CMOS_INVERTER schematic.
        data = make_dataset([0] * 6 + [1] * 6, [0] * 12)
        report = verify_gate("CMOS_INVERTER", data, min_samples=4)
        self.assertEqual(report.status, "xfail")  # listed in KNOWN_ISSUES

    def test_ignores_short_transition_windows(self) -> None:
        # A two-sample glitch between two long, identical input windows must
        # not be counted as a separate logic level.
        data = make_dataset([0] * 6 + [5] * 2 + [0] * 6, [5] * 6 + [0] * 2 + [5] * 6)
        report = verify_gate("CMOS_INVERTER", data, min_samples=4)
        self.assertEqual(report.covered, 1)
        self.assertTrue(all(item.matches for item in report.observations))
        self.assertEqual(report.status, "partial")  # only one input level seen


class VerifyAllTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reports = {report.name: report for report in verify_all(ROOT)}

    def test_all_datasets_were_found(self) -> None:
        self.assertEqual(
            set(self.reports),
            {
                "CMOS_AND",
                "CMOS_INVERTER",
                "CMOS_NAND",
                "CMOS_NOR",
                "CMOS_OR",
            },
        )
        for report in self.reports.values():
            with self.subTest(gate=report.name):
                self.assertNotIn(report.status, {"missing", "error"}, report.note)

    def test_nand_and_nor_pass_full_truth_tables(self) -> None:
        for name in ("CMOS_NAND", "CMOS_NOR"):
            with self.subTest(gate=name):
                report = self.reports[name]
                self.assertEqual(report.status, "pass", report.note)
                self.assertEqual(report.covered, 4)

    def test_and_and_or_have_incomplete_stimulus(self) -> None:
        for name in ("CMOS_AND", "CMOS_OR"):
            with self.subTest(gate=name):
                report = self.reports[name]
                self.assertEqual(report.status, "partial", report.note)
                self.assertEqual(report.covered, 2)
                self.assertTrue(all(item.matches for item in report.observations))

    def test_inverter_is_reported_as_known_issue(self) -> None:
        report = self.reports["CMOS_INVERTER"]
        self.assertEqual(report.status, "xfail")
        self.assertIn("_net1", report.note)


if __name__ == "__main__":
    unittest.main()
