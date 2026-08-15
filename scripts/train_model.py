"""Fit a transparent temperature calibrator to historical probabilities."""

from __future__ import annotations

import json
import math
from pathlib import Path

from scripts.common import actual_result, log_loss, probabilities, rank_results, rank_scale, read_loteca_csv, temperature_scale, top1_risk_scale
from scripts.preprocess_data import validate_rows


TEMPERATURES = tuple(value / 100 for value in range(50, 201))
MIN_VALIDATION_GAIN = 1e-6
RANK_PRIOR_GAMES = 20.0
RISK_PRIOR_GAMES = 30.0


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


def _rank_lifts(rows: list[dict[str, str]], temperature: float) -> list[float]:
    """Estimate smoothed observed/predicted ratios for Top1, Top2 and Top3."""
    predicted = [0.0, 0.0, 0.0]
    hits = [0.0, 0.0, 0.0]
    for row in rows:
        probs = temperature_scale(probabilities(row), temperature)
        ranking = rank_results(probs)
        for index, result in enumerate(ranking):
            predicted[index] += probs[result]
            hits[index] += actual_result(row) == result
    count = len(rows)
    return [
        (hits[index] + RANK_PRIOR_GAMES * predicted[index] / count)
        / (predicted[index] * (1.0 + RANK_PRIOR_GAMES / count))
        for index in range(3)
    ]


def _calibrated_log_loss(rows: list[dict[str, str]], temperature: float, lifts: list[float]) -> float:
    loss = 0.0
    for row in rows:
        probs = rank_scale(temperature_scale(probabilities(row), temperature), lifts)
        loss -= math.log(max(probs[actual_result(row)], 1e-15))
    return loss / len(rows)


def _risk_rank_lifts(rows: list[dict[str, str]], temperature: float, rank_lifts: list[float]) -> list[float]:
    """Learn smoothed Top1 calibration by within-contest risk rank 1..14."""
    predicted = [0.0] * 14
    hits = [0.0] * 14
    counts = [0] * 14
    contests: dict[int, list[dict[str, str]]] = {}
    for row in rows:
        contests.setdefault(int(row["Concurso"]), []).append(row)
    for contest_rows in contests.values():
        prepared = []
        for row in contest_rows:
            probs = rank_scale(temperature_scale(probabilities(row), temperature), rank_lifts)
            prepared.append((row, probs, probs[rank_results(probs)[0]]))
        for index, (row, probs, _) in enumerate(sorted(prepared, key=lambda item: (item[2], int(item[0]["Jogo"])))):
            top1 = rank_results(probs)[0]
            predicted[index] += probs[top1]
            hits[index] += actual_result(row) == top1
            counts[index] += 1
    lifts = []
    for index in range(14):
        if not counts[index] or predicted[index] <= 0:
            lifts.append(1.0)
            continue
        mean_predicted = predicted[index] / counts[index]
        smoothed_hits = hits[index] + RISK_PRIOR_GAMES * mean_predicted
        smoothed_predicted = predicted[index] + RISK_PRIOR_GAMES * mean_predicted
        lifts.append(smoothed_hits / smoothed_predicted)
    return lifts


def _risk_log_loss(rows: list[dict[str, str]], temperature: float, rank_lifts: list[float], risk_lifts: list[float]) -> float:
    loss = 0.0
    contests: dict[int, list[dict[str, str]]] = {}
    for row in rows:
        contests.setdefault(int(row["Concurso"]), []).append(row)
    for contest_rows in contests.values():
        prepared = []
        for row in contest_rows:
            probs = rank_scale(temperature_scale(probabilities(row), temperature), rank_lifts)
            prepared.append((row, probs, probs[rank_results(probs)[0]]))
        for index, (row, probs, _) in enumerate(sorted(prepared, key=lambda item: (item[2], int(item[0]["Jogo"])))):
            calibrated = top1_risk_scale(probs, risk_lifts[index])
            loss -= math.log(max(calibrated[actual_result(row)], 1e-15))
    return loss / len(rows)


def train(history_path: str | Path, model_path: str | Path) -> dict:
    rows = read_loteca_csv(history_path)
    validate_rows(rows, historical=True)
    contests = sorted({int(row["Concurso"]) for row in rows})
    cutoff = contests[max(1, int(len(contests) * 0.8)) - 1]
    fit_rows = [row for row in rows if int(row["Concurso"]) <= cutoff]
    validation = [row for row in rows if int(row["Concurso"]) > cutoff]
    validation_candidate = _best_temperature(fit_rows)
    raw_loss = log_loss(validation, 1.0)
    temperature_loss = _calibrated_log_loss(validation, validation_candidate, [1.0, 1.0, 1.0])
    candidate_lifts = _rank_lifts(fit_rows, validation_candidate)
    rank_loss = _calibrated_log_loss(validation, validation_candidate, candidate_lifts)
    candidate_loss = min(temperature_loss, rank_loss)
    selected_temperature, promoted = _validated_temperature(validation_candidate, raw_loss, candidate_loss)
    rank_promoted = promoted and rank_loss <= temperature_loss

    validation_rank_lifts = candidate_lifts if rank_promoted else [1.0, 1.0, 1.0]
    candidate_risk_lifts = _risk_rank_lifts(fit_rows, validation_candidate if promoted else 1.0, validation_rank_lifts)
    base_validation_loss = rank_loss if rank_promoted else (temperature_loss if promoted else raw_loss)
    risk_validation_loss = _risk_log_loss(
        validation, validation_candidate if promoted else 1.0, validation_rank_lifts, candidate_risk_lifts
    )
    risk_promoted = risk_validation_loss + MIN_VALIDATION_GAIN < base_validation_loss

    # After the calibration method has passed the chronological gate, refit its
    # sole parameter with every contest available before deployment.  The
    # validation contest outcomes are historical at this point and no future
    # contest information is used.
    temperature = _best_temperature(rows) if promoted else 1.0
    rank_lifts = _rank_lifts(rows, temperature) if rank_promoted else [1.0, 1.0, 1.0]
    risk_rank_lifts = _risk_rank_lifts(rows, temperature, rank_lifts) if risk_promoted else [1.0] * 14
    model = {
        "type": "temperature_scaling",
        "temperature": temperature,
        "calibration_promoted": promoted,
        "rank_calibration_promoted": rank_promoted,
        "rank_lifts": rank_lifts,
        "risk_rank_calibration_promoted": risk_promoted,
        "risk_rank_lifts": risk_rank_lifts,
        "validation_candidate_temperature": validation_candidate,
        "validation_selected_temperature": selected_temperature,
        "training_games": len(fit_rows),
        "validation_games": len(validation),
        "training_last_contest": cutoff,
        "validation_log_loss_raw": raw_loss,
        "validation_log_loss_calibrated": candidate_loss,
        "validation_log_loss_temperature": temperature_loss,
        "validation_log_loss_rank_calibrated": rank_loss,
        "validation_log_loss_before_risk_rank": base_validation_loss,
        "validation_log_loss_risk_rank": risk_validation_loss,
        "deployment_log_loss_all_history": log_loss(rows, temperature),
    }
    destination = Path(model_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return model
