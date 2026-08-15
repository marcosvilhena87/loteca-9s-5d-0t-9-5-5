from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from scripts.common import OUTCOMES, load_csv, parse_decimal, rank_probabilities

REQUIRED_COLUMNS = {
    "Concurso", "Jogo", "Mandante", "Visitante", "1", "X", "2",
    "p(1)", "p(x)", "p(2)"
}


def _probabilities(row: dict) -> Dict[str, float]:
    probs = {
        "1": parse_decimal(row.get("p(1)", "")),
        "X": parse_decimal(row.get("p(x)", "")),
        "2": parse_decimal(row.get("p(2)", "")),
    }
    if min(probs.values()) < 0:
        raise ValueError(f"Probabilidade negativa no concurso {row.get('Concurso')} jogo {row.get('Jogo')}")
    total = sum(probs.values())
    if total <= 0:
        raise ValueError(f"Probabilidades inválidas no concurso {row.get('Concurso')} jogo {row.get('Jogo')}")
    return {key: value / total for key, value in probs.items()}


def _actual_outcome(row: dict) -> str | None:
    flags = [outcome for outcome in OUTCOMES if str(row.get(outcome, "0")).strip() == "1"]
    if not flags:
        return None
    if len(flags) != 1:
        raise ValueError(
            f"Resultado real deve ser one-hot no concurso {row.get('Concurso')} jogo {row.get('Jogo')}: {flags}"
        )
    return flags[0]


def preprocess(path: str | Path, require_actual: bool) -> List[dict]:
    rows = load_csv(path)
    if not rows:
        raise ValueError(f"CSV vazio: {path}")
    missing = REQUIRED_COLUMNS.difference(rows[0].keys())
    if missing:
        raise ValueError(f"Colunas ausentes em {path}: {sorted(missing)}")

    processed = []
    for row in rows:
        probs = _probabilities(row)
        order, rank_by_outcome = rank_probabilities(probs)
        actual = _actual_outcome(row)
        if require_actual and actual is None:
            raise ValueError(
                f"Histórico sem resultado real no concurso {row.get('Concurso')} jogo {row.get('Jogo')}"
            )
        enriched = dict(row)
        enriched["_probs"] = probs
        enriched["_order"] = order
        enriched["_rank_by_outcome"] = rank_by_outcome
        enriched["_actual"] = actual
        enriched["_top_hits"] = {
            1: int(actual is not None and rank_by_outcome[actual] == 1),
            2: int(actual is not None and rank_by_outcome[actual] == 2),
            3: int(actual is not None and rank_by_outcome[actual] == 3),
        }
        if actual is not None and sum(enriched["_top_hits"].values()) != 1:
            raise AssertionError("Falha interna no One-Hot top1/top2/top3")
        processed.append(enriched)
    return processed


def group_by_contest(rows: List[dict]) -> Dict[int, List[dict]]:
    grouped: Dict[int, List[dict]] = {}
    for row in rows:
        contest = int(row["Concurso"])
        grouped.setdefault(contest, []).append(row)
    for contest, games in grouped.items():
        games.sort(key=lambda item: int(item["Jogo"]))
        if len(games) != 14:
            raise ValueError(f"Concurso {contest} possui {len(games)} jogos; esperado: 14")
    return dict(sorted(grouped.items()))
