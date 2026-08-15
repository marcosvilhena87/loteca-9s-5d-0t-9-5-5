from __future__ import annotations

import csv
import json
import math
import unicodedata
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

OUTCOMES = ("1", "X", "2")
TIE_PRIORITY = {"1": 0, "2": 1, "X": 2}


def parse_decimal(value: str) -> float:
    text = (value or "").strip()
    if not text:
        return 0.0
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    return float(text)


def decimal_pt(value: float, digits: int = 9) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def normalize_team(name: str) -> str:
    text = unicodedata.normalize("NFKD", (name or "").upper())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.split())


def rank_probabilities(probabilities: Dict[str, float]) -> Tuple[List[str], Dict[str, int]]:
    order = sorted(OUTCOMES, key=lambda outcome: (-probabilities[outcome], TIE_PRIORITY[outcome]))
    rank_by_outcome = {outcome: idx + 1 for idx, outcome in enumerate(order)}
    return order, rank_by_outcome


def winner_outcome(team: str, mandante: str, visitante: str) -> str | None:
    target = normalize_team(team)
    if normalize_team(mandante) == target:
        return "1"
    if normalize_team(visitante) == target:
        return "2"
    return None


def format_palpite(outcomes: Iterable[str]) -> str:
    selected = set(outcomes)
    if selected == {"1", "X", "2"}:
        return "1X2"
    if selected == {"1", "X"}:
        return "1X"
    if selected == {"1", "2"}:
        return "12"
    if selected == {"X", "2"}:
        return "X2"
    if len(selected) == 1:
        return next(iter(selected))
    raise ValueError(f"Conjunto de resultados inválido: {selected}")


def load_csv(path: str | Path) -> List[dict]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def write_csv(path: str | Path, rows: Sequence[dict], fieldnames: Sequence[str]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=";", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def save_json(path: str | Path, payload: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)


def load_json(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def p_at_least_13(hit_probabilities: Sequence[float]) -> float:
    if len(hit_probabilities) != 14:
        raise ValueError("P(>=13) foi definida para exatamente 14 jogos.")
    qs = [min(max(float(q), 1e-15), 1.0) for q in hit_probabilities]
    log_product = sum(math.log(q) for q in qs)
    inv_sum = sum(1.0 / q for q in qs)
    return math.exp(log_product) * (inv_sum - 13.0)


def p_exactly_14(hit_probabilities: Sequence[float]) -> float:
    value = 1.0
    for q in hit_probabilities:
        value *= q
    return value
