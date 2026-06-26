"""Tests for truth table generation."""

import unittest
from src.truth_table import (
    generate_truth_table_2input,
    generate_truth_table_3input,
    print_truth_table,
    get_all_2input_truth_tables,
)
from src.gates import AND, OR, NOT, XOR


class TestTruthTableGeneration(unittest.TestCase):
    """Test truth table generation functions."""

    def test_2input_and_table(self):
        table = generate_truth_table_2input(AND, "AND")
        self.assertEqual(len(table), 4)
        self.assertEqual(table, [(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 1)])

    def test_2input_or_table(self):
        table = generate_truth_table_2input(OR, "OR")
        self.assertEqual(len(table), 4)
        self.assertEqual(table, [(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 1)])

    def test_2input_xor_table(self):
        table = generate_truth_table_2input(XOR, "XOR")
        self.assertEqual(len(table), 4)
        self.assertEqual(table, [(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0)])

    def test_3input_table_length(self):
        def three_input_or(a, b, c):
            return 1 if (a or b or c) else 0

        table = generate_truth_table_3input(three_input_or, "OR3")
        self.assertEqual(len(table), 8)

    def test_print_table_returns_string(self):
        result = print_truth_table(AND, "AND", 2)
        self.assertIsInstance(result, str)
        self.assertIn("AND", result)
        self.assertIn("0", result)
        self.assertIn("1", result)

    def test_get_all_tables(self):
        tables = get_all_2input_truth_tables()
        self.assertIn("AND", tables)
        self.assertIn("OR", tables)
        self.assertIn("NOT", tables)
        self.assertIn("NAND", tables)
        self.assertIn("NOR", tables)
        self.assertIn("XOR", tables)
        self.assertIn("XNOR", tables)

        for name, table in tables.items():
            if name == "NOT":
                self.assertEqual(len(table), 2)
            else:
                self.assertEqual(len(table), 4)


if __name__ == "__main__":
    unittest.main()
