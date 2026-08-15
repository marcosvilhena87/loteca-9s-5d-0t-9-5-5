from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Tuple

from scripts.common import OUTCOMES, save_json
from scripts.preprocess_data import preprocess


def _softmax(values: List[float]) -> List[float]:
    peak = max(values)
    exps = [math.exp(v - peak) for v in values]
    total = sum(exps)
    return [v / total for v in exps]


def calibrate_probabilities(probs: Dict[str, float], alpha: float, biases: Dict[str, float]) -> Dict[str, float]:
    eps = 1e-12
    logits = [alpha * math.log(max(probs[outcome], eps)) + biases[outcome] for outcome in OUTCOMES]
    calibrated = _softmax(logits)
    return {outcome: calibrated[idx] for idx, outcome in enumerate(OUTCOMES)}


def train_calibrator(
    history_path: str | Path,
    model_path: str | Path = "models/model.json",
    epochs: int = 700,
    learning_rate: float = 0.035,
    l2: float = 0.002,
    half_life_contests: float = 220.0,
) -> dict:
    rows = preprocess(history_path, require_actual=True)
    latest = max(int(row["Concurso"]) for row in rows)

    alpha = 1.0
    biases = {outcome: 0.0 for outcome in OUTCOMES}
    eps = 1e-12
    weighted_rows: List[Tuple[dict, float]] = []
    for row in rows:
        age = latest - int(row["Concurso"])
        weight = 0.5 ** (age / half_life_contests)
        weighted_rows.append((row, weight))
    weight_sum = sum(weight for _, weight in weighted_rows)

    for _ in range(epochs):
        grad_alpha = 0.0
        grad_bias = {outcome: 0.0 for outcome in OUTCOMES}
        for row, weight in weighted_rows:
            logp = [math.log(max(row["_probs"][outcome], eps)) for outcome in OUTCOMES]
            logits = [alpha * logp[idx] + biases[outcome] for idx, outcome in enumerate(OUTCOMES)]
            calibrated = _softmax(logits)
            actual = row["_actual"]
            for idx, outcome in enumerate(OUTCOMES):
                error = calibrated[idx] - (1.0 if outcome == actual else 0.0)
                grad_alpha += weight * error * logp[idx]
                grad_bias[outcome] += weight * error

        grad_alpha = grad_alpha / weight_sum + l2 * (alpha - 1.0)
        for outcome in OUTCOMES:
            grad_bias[outcome] = grad_bias[outcome] / weight_sum + l2 * biases[outcome]

        alpha -= learning_rate * grad_alpha
        for outcome in OUTCOMES:
            biases[outcome] -= learning_rate * grad_bias[outcome]
        mean_bias = sum(biases.values()) / 3.0
        for outcome in OUTCOMES:
            biases[outcome] -= mean_bias
        alpha = min(max(alpha, 0.20), 3.0)

    raw_logloss = 0.0
    calibrated_logloss = 0.0
    top_hits = {1: 0, 2: 0, 3: 0}
    for row, weight in weighted_rows:
        actual = row["_actual"]
        raw_logloss -= weight * math.log(max(row["_probs"][actual], eps))
        calibrated = calibrate_probabilities(row["_probs"], alpha, biases)
        calibrated_logloss -= weight * math.log(max(calibrated[actual], eps))
        top_hits[row["_rank_by_outcome"][actual]] += 1

    model = {
        "version": 1,
        "method": "multinomial_log_probability_calibration",
        "alpha": alpha,
        "biases": biases,
        "half_life_contests": half_life_contests,
        "training_rows": len(rows),
        "latest_contest": latest,
        "weighted_raw_logloss": raw_logloss / weight_sum,
        "weighted_calibrated_logloss": calibrated_logloss / weight_sum,
        "historical_rank_hit_rates": {str(rank): top_hits[rank] / len(rows) for rank in (1, 2, 3)},
        "tie_priority": ["1", "2", "X"],
    }
    save_json(model_path, model)
    return model
