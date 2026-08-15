import unittest

from scripts.common import rank_results
from scripts.predict_results import hit_distribution, optimize, validate_ticket
from scripts.train_model import _validated_temperature


class PipelineTests(unittest.TestCase):
    def test_hit_distribution_is_exact_and_normalized(self):
        distribution = hit_distribution([0.5, 0.25])
        self.assertEqual(distribution, [0.375, 0.5, 0.125])
        self.assertAlmostEqual(sum(distribution), 1.0)

    def test_calibration_is_only_promoted_after_out_of_sample_gain(self):
        self.assertEqual(_validated_temperature(0.8, 0.95, 0.94), (0.8, True))
        self.assertEqual(_validated_temperature(0.8, 0.95, 0.96), (1.0, False))
        self.assertEqual(_validated_temperature(0.8, 0.95, 0.95), (1.0, False))

    def test_mandatory_tie_break(self):
        self.assertEqual(rank_results({"1": 0.4, "X": 0.3, "2": 0.3}), ("1", "2", "X"))

    def test_optimizer_enforces_all_hard_constraints(self):
        rows = []
        for game in range(1, 15):
            rows.append({
                "Concurso": "1", "Jogo": str(game),
                "Mandante": "FLAMENGO/RJ" if game == 1 else f"TIME {game} A",
                "Visitante": f"TIME {game} B", "p(1)": "0,50", "p(x)": "0,30", "p(2)": "0,20",
            })
        predictions, probability = optimize(rows, 1.0)
        self.assertGreater(probability, 0)
        self.assertEqual(sum(item["tipo"] == "seco" for item in predictions), 9)
        self.assertEqual(sum(item["tipo"] == "duplo" for item in predictions), 5)
        for rank, expected in ((1, 9), (2, 5), (3, 5)):
            self.assertEqual(sum(f"top{rank}" in item["ranks_selecionados"].split("+") for item in predictions), expected)
        self.assertIn("1", predictions[0]["palpite"])
        distribution = hit_distribution([item["probabilidade_coberta"] for item in predictions])
        self.assertAlmostEqual(probability, sum(distribution[13:]))

    def test_independent_validator_rejects_a_tampered_ticket(self):
        rows = []
        for game in range(1, 15):
            rows.append({
                "Concurso": "1", "Jogo": str(game),
                "Mandante": f"TIME {game} A", "Visitante": f"TIME {game} B",
                "p(1)": "0,50", "p(x)": "0,30", "p(2)": "0,20",
            })
        predictions, _ = optimize(rows, 1.0)
        validate_ticket(predictions)
        predictions[0]["palpite"] = "1X2"
        with self.assertRaisesRegex(ValueError, "Hard Constraints violadas"):
            validate_ticket(predictions)


if __name__ == "__main__":
    unittest.main()
