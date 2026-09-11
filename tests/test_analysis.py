import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("analysis", ROOT / "experiments" / "analyze_balance.py")
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


class RecordedStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "data" / "battle-outcomes.json").read_text())

    def test_complete_study(self):
        analysis.validate(self.data)

    def test_rejects_score_not_supported_by_outcome(self):
        data = copy.deepcopy(self.data)
        data["rows"][0]["score"] += 0.125
        with self.assertRaises(AssertionError):
            analysis.validate(data)

    def test_rejects_selection_after_training(self):
        data = copy.deepcopy(self.data)
        data["selected"] = 1.4
        with self.assertRaises(AssertionError):
            analysis.validate(data)

    def test_rejects_train_test_seed_overlap(self):
        data = copy.deepcopy(self.data)
        test = next(row for row in data["rows"] if row["split"] == "test")
        test["seed"] = data["rows"][0]["seed"]
        with self.assertRaises(AssertionError):
            analysis.validate(data)

    def test_rejects_unmatched_interventions(self):
        data = copy.deepcopy(self.data)
        row = next(row for row in data["rows"] if row["scale"] == 0.9)
        row["single"] = "wrong_species"
        with self.assertRaises(AssertionError):
            analysis.validate(data)

    def test_uncertainty_is_zero_for_constant_outcome(self):
        rows = [{"score": 1.0, "first": "p", "second": "e", "timeouts": 0, "draws": 0, "turns": [1, 1]}] * 8
        result = analysis.describe(rows)
        self.assertEqual(result["bootstrap95"], [1.0, 1.0])


if __name__ == "__main__":
    unittest.main()
