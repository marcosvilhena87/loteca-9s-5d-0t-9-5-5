"""Fit a transparent temperature calibrator to historical probabilities."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.common import log_loss, read_loteca_csv
from scripts.preprocess_data import validate_rows


TEMPERATURES = tuple(value / 100 for value in range(50, 201))
MIN_VALIDATION_GAIN = 1e-6


def _best_temperature(rows: list[dict[str, str]]) -> float:
    """Return the grid temperature with the lowest multiclass log-loss."""
    return min(TEMPERATURES, key=lambda value: log_loss(rows, value))


def _validated_temperature(candidate: float, raw_loss: float, calibrated_loss: float) -> tuple[float, bool]:
    """Promote calibration only when it improves unseen chronological data.

    A temperature fitted in-sample can make the probabilities worse and, in
    turn, make the ticket optimizer confidently choose the wrong allocation.
    Falling back to 1.0 makes that failure mode explicit and deterministic.
    """
    promoted = calibrated_loss + MIN_VALIDATION_GAIN < raw_loss
    return (candidate if promoted else 1.0), promoted


def train(history_path: str | Path, model_path: str | Path) -> dict:
    rows = read_loteca_csv(history_path)
    validate_rows(rows, historical=True)
    contests = sorted({int(row["Concurso"]) for row in rows})
    cutoff = contests[max(1, int(len(contests) * 0.8)) - 1]
    fit_rows = [row for row in rows if int(row["Concurso"]) <= cutoff]
    validation = [row for row in rows if int(row["Concurso"]) > cutoff]
    validation_candidate = _best_temperature(fit_rows)
    raw_loss = log_loss(validation, 1.0)
    candidate_loss = log_loss(validation, validation_candidate)
    selected_temperature, promoted = _validated_temperature(validation_candidate, raw_loss, candidate_loss)

    # After the calibration method has passed the chronological gate, refit its
    # sole parameter with every contest available before deployment.  The
    # validation contest outcomes are historical at this point and no future
    # contest information is used.
    temperature = _best_temperature(rows) if promoted else 1.0
    model = {
        "type": "temperature_scaling",
        "temperature": temperature,
        "calibration_promoted": promoted,
        "validation_candidate_temperature": validation_candidate,
        "validation_selected_temperature": selected_temperature,
        "training_games": len(fit_rows),
        "validation_games": len(validation),
        "training_last_contest": cutoff,
        "validation_log_loss_raw": raw_loss,
        "validation_log_loss_calibrated": candidate_loss,
        "deployment_log_loss_all_history": log_loss(rows, temperature),
    }
    destination = Path(model_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return model
