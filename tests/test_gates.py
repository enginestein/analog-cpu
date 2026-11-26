"""Tests for the ideal gate reference models."""

from __future__ import annotations

import unittest

from analog_cpu.gates import GATES, evaluate, truth_table


class GateModelTests(unittest.TestCase):
    def test_known_gates_are_present(self) -> None:
        self.assertEqual(
            set(GATES),
            {
                "CMOS_AND",
                "CMOS_INVERTER",
                "CMOS_NAND",
                "CMOS_NOR",
                "CMOS_OR",
            },
        )

    def test_inverter_truth_table(self) -> None:
        self.assertEqual(truth_table("CMOS_INVERTER"), (((0,), 1), ((1,), 0)))

    def test_two_input_truth_tables(self) -> None:
        expected = {
            "CMOS_AND": [0, 0, 0, 1],
            "CMOS_NAND": [1, 1, 1, 0],
            "CMOS_NOR": [1, 0, 0, 0],
            "CMOS_OR": [0, 1, 1, 1],
        }
        vectors = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for name, outputs in expected.items():
            with self.subTest(gate=name):
                table = truth_table(name)
                self.assertEqual([inputs for inputs, _ in table], vectors)
                self.assertEqual([output for _, output in table], outputs)

    def test_evaluate_matches_truth_table(self) -> None:
        for name in GATES:
            with self.subTest(gate=name):
                for inputs, output in truth_table(name):
                    self.assertEqual(evaluate(name, inputs), output)

    def test_bad_gate_or_input_count_raises(self) -> None:
        with self.assertRaises(KeyError):
            evaluate("CMOS_XOR", (0, 0))
        with self.assertRaisesRegex(ValueError, "expects 2 inputs"):
            evaluate("CMOS_AND", (0,))


if __name__ == "__main__":
    unittest.main()
