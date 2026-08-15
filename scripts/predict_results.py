"""Constrained optimization of a single 9-dry/5-double Loteca ticket."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from scripts.common import normalized_team, probabilities, rank_results, read_loteca_csv, temperature_scale
from scripts.preprocess_data import validate_next_contest


@dataclass(frozen=True)
class Candidate:
    p0: float
    p1: float
    choices: tuple[tuple[int, ...], ...]

    @property
    def success(self) -> float:
        return self.p0 + self.p1


def _pareto(candidates: list[Candidate]) -> list[Candidate]:
    """Keep only (P(no miss), P(one miss)) non-dominated partial tickets."""
    ordered = sorted(candidates, key=lambda item: (-item.p0, -item.p1))
    result: list[Candidate] = []
    best_p1 = -1.0
    for candidate in ordered:
        if candidate.p1 > best_p1 + 1e-18:
            result.append(candidate)
            best_p1 = candidate.p1
    return result


def _allowed_options(row: dict[str, str], ranking: tuple[str, str, str]) -> list[tuple[int, ...]]:
    options = [(0,), (1,), (2,), (0, 1), (0, 2), (1, 2)]
    home, away = normalized_team(row["Mandante"]), normalized_team(row["Visitante"])
    if "FLAMENGO/RJ" in (home, away):
        victory = "1" if home == "FLAMENGO/RJ" else "2"
        options = [option for option in options if ranking.index(victory) in option]
    return options


def optimize(rows: list[dict[str, str]], temperature: float) -> tuple[list[dict], float]:
    validate_next_contest(rows)
    games = []
    for row in sorted(rows, key=lambda item: int(item["Jogo"])):
        probs = temperature_scale(probabilities(row), temperature)
        ranking = rank_results(probs)
        games.append((row, probs, ranking, _allowed_options(row, ranking)))

    # State: number of selected rank-1/rank-2/rank-3 outcomes and doubles.
    states: dict[tuple[int, int, int, int], list[Candidate]] = {(0, 0, 0, 0): [Candidate(1.0, 0.0, ())]}
    for row, probs, ranking, options in games:
        expanded: dict[tuple[int, int, int, int], list[Candidate]] = {}
        for counts, frontier in states.items():
            for option in options:
                new_counts = tuple(counts[index] + (index in option) for index in range(3)) + (counts[3] + (len(option) == 2),)
                if any(new_counts[index] > (9, 5, 5)[index] for index in range(3)) or new_counts[3] > 5:
                    continue
                coverage = sum(probs[ranking[index]] for index in option)
                bucket = expanded.setdefault(new_counts, [])
                for candidate in frontier:
                    bucket.append(Candidate(candidate.p0 * coverage, candidate.p1 * coverage + candidate.p0 * (1 - coverage), candidate.choices + (option,)))
        states = {state: _pareto(frontier) for state, frontier in expanded.items()}

    finalists = states.get((9, 5, 5, 5), [])
    if not finalists:
        raise RuntimeError("Não existe aposta que satisfaça todas as Hard Constraints")

    def soft_score(candidate: Candidate) -> tuple[int, int]:
        top1_early = sum(0 in choice for choice in candidate.choices[:9])
        avoids_palmeiras = 0
        for (row, _, ranking, _), choice in zip(games, candidate.choices):
            home, away = normalized_team(row["Mandante"]), normalized_team(row["Visitante"])
            if "PALMEIRAS/SP" in (home, away):
                victory = "1" if home == "PALMEIRAS/SP" else "2"
                avoids_palmeiras += ranking.index(victory) not in choice
        return avoids_palmeiras, top1_early

    best_probability = max(candidate.success for candidate in finalists)
    near_optimal = [candidate for candidate in finalists if best_probability - candidate.success <= 1e-12]
    best = max(near_optimal, key=soft_score)

    output = []
    for (row, probs, ranking, _), choice in zip(games, best.choices):
        selected = [ranking[index] for index in choice]
        ordered_marks = "".join(result for result in ("1", "X", "2") if result in selected)
        output.append({
            "Concurso": row["Concurso"], "Jogo": row["Jogo"], "Mandante": row["Mandante"], "Visitante": row["Visitante"],
            "p(1)": probs["1"], "p(X)": probs["X"], "p(2)": probs["2"],
            "top1": ranking[0], "top2": ranking[1], "top3": ranking[2],
            "p(top1)": probs[ranking[0]], "p(top2)": probs[ranking[1]], "p(top3)": probs[ranking[2]],
            "tipo": "duplo" if len(choice) == 2 else "seco", "palpite": ordered_marks,
            "ranks_selecionados": "+".join(f"top{index + 1}" for index in choice),
            "probabilidade_coberta": sum(probs[result] for result in selected),
        })
    return output, best.success


def predict(next_path: str | Path, model_path: str | Path, output_path: str | Path) -> tuple[list[dict], float]:
    model = json.loads(Path(model_path).read_text(encoding="utf-8"))
    predictions, success = optimize(read_loteca_csv(next_path), float(model["temperature"]))
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(predictions[0]), delimiter=";", lineterminator="\n")
        writer.writeheader()
        writer.writerows(predictions)
    return predictions, success


def print_telemetry(predictions: list[dict], success: float) -> None:
    print("\n=== TELEMETRIA DA APOSTA OTIMIZADA ===")
    for game in predictions:
        print(f"Jogo {game['Jogo']:>2} | {game['Mandante']} x {game['Visitante']}")
        print(f"  p(1)={game['p(1)']:.4f} p(X)={game['p(X)']:.4f} p(2)={game['p(2)']:.4f}")
        print(f"  ranking: {game['top1']} ({game['p(top1)']:.4f}) > {game['top2']} ({game['p(top2)']:.4f}) > {game['top3']} ({game['p(top3)']:.4f})")
        print(f"  {game['tipo']}: {game['palpite']} [{game['ranks_selecionados']}] cobertura={game['probabilidade_coberta']:.4f}")
    dry = sum(game["tipo"] == "seco" for game in predictions)
    doubles = sum(game["tipo"] == "duplo" for game in predictions)
    rank_counts = [sum(f"top{rank}" in game["ranks_selecionados"].split("+") for game in predictions) for rank in range(1, 4)]
    flamengo_games = [game for game in predictions if "FLAMENGO/RJ" in (normalized_team(game["Mandante"]), normalized_team(game["Visitante"]))]
    flamengo_ok = all(("1" if normalized_team(game["Mandante"]) == "FLAMENGO/RJ" else "2") in game["palpite"] for game in flamengo_games)
    print("\n=== VALIDAÇÃO DAS HARD CONSTRAINTS ===")
    print(f"Secos: {dry}/9 | Duplos: {doubles}/5 | Triplos: 0/0")
    print(f"Top1: {rank_counts[0]}/9 | Top2: {rank_counts[1]}/5 | Top3: {rank_counts[2]}/5")
    print(f"Flamengo/RJ: {'regra satisfeita' if flamengo_ok else 'REGRA VIOLADA'}")
    print(f"Objetivo otimizado P(acertos >= 13): {success:.8%}")
