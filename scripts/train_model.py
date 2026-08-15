"""Fit a transparent temperature calibrator to historical probabilities."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.common import log_loss, read_loteca_csv
from scripts.preprocess_data import validate_rows


def train(history_path: str | Path, model_path: str | Path) -> dict:
    rows = read_loteca_csv(history_path)
    validate_rows(rows, historical=True)
    contests = sorted({int(row["Concurso"]) for row in rows})
    cutoff = contests[max(1, int(len(contests) * 0.8)) - 1]
    fit_rows = [row for row in rows if int(row["Concurso"]) <= cutoff]
    validation = [row for row in rows if int(row["Concurso"]) > cutoff]
    candidates = [value / 100 for value in range(50, 201)]
    temperature = min(candidates, key=lambda value: log_loss(fit_rows, value))
    model = {
        "type": "temperature_scaling",
        "temperature": temperature,
        "training_games": len(fit_rows),
        "validation_games": len(validation),
        "training_last_contest": cutoff,
        "validation_log_loss_raw": log_loss(validation, 1.0),
        "validation_log_loss_calibrated": log_loss(validation, temperature),
    }
    destination = Path(model_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return model
