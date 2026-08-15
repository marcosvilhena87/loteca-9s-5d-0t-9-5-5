from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from scripts.common import (
    decimal_pt, format_palpite, load_json, p_at_least_13,
    p_exactly_14, rank_probabilities, winner_outcome, write_csv,
)
from scripts.preprocess_data import preprocess
from scripts.train_model import calibrate_probabilities

RANK_SUBSETS = ((1,), (2,), (3,), (1, 2), (1, 3), (2, 3))


@dataclass(frozen=True)
class Choice:
    ranks: Tuple[int, ...]
    outcomes: Tuple[str, ...]
    q: float
    is_single: bool
    includes_palmeiras_win: bool


@dataclass
class Candidate:
    log_product: float
    inverse_sum: float
    choices: List[Choice]

    @property
    def p13plus(self) -> float:
        return math.exp(self.log_product) * (self.inverse_sum - 13.0)


def _choices_for_game(row: dict, probs: Dict[str, float], rank_by_outcome: Dict[str, int]) -> List[Choice]:
    outcome_by_rank = {rank: outcome for outcome, rank in rank_by_outcome.items()}
    flamengo_win = winner_outcome("FLAMENGO/RJ", row["Mandante"], row["Visitante"])
    palmeiras_win = winner_outcome("PALMEIRAS/SP", row["Mandante"], row["Visitante"])

    result = []
    for ranks in RANK_SUBSETS:
        outcomes = tuple(outcome_by_rank[rank] for rank in ranks)
        if flamengo_win is not None and flamengo_win not in outcomes:
            continue
        q = sum(probs[outcome] for outcome in outcomes)
        result.append(Choice(
            ranks=ranks,
            outcomes=outcomes,
            q=q,
            is_single=len(ranks) == 1,
            includes_palmeiras_win=palmeiras_win is not None and palmeiras_win in outcomes,
        ))
    return result


def _pareto_prune(candidates: List[Candidate]) -> List[Candidate]:
    candidates.sort(key=lambda c: (-c.log_product, -c.inverse_sum))
    kept: List[Candidate] = []
    best_inverse = -1.0
    for candidate in candidates:
        if candidate.inverse_sum > best_inverse + 1e-14:
            kept.append(candidate)
            best_inverse = candidate.inverse_sum
    return kept


def _soft_metrics(choices: Sequence[Choice]) -> dict:
    top1_presence = [1 if 1 in choice.ranks else 0 for choice in choices]
    early_weight = sum((15 - idx) * flag for idx, flag in enumerate(top1_presence, start=1))
    fragments = 0
    longest = current = 0
    previous = 0
    for flag in top1_presence:
        if flag:
            current = current + 1 if previous else 1
            longest = max(longest, current)
            if not previous:
                fragments += 1
        else:
            current = 0
        previous = flag
    palmeiras_marks = sum(choice.includes_palmeiras_win for choice in choices)
    score = early_weight + 3.0 * longest - 2.0 * fragments - 12.0 * palmeiras_marks
    return {
        "score": score,
        "early_weight": early_weight,
        "longest_top1_run": longest,
        "top1_fragments": fragments,
        "palmeiras_win_marks": palmeiras_marks,
    }


def optimize_ticket(games: List[dict], calibrated_probabilities: List[Dict[str, float]], soft_tolerance: float = 0.0025):
    if len(games) != 14:
        raise ValueError(f"O concurso precisa ter 14 jogos; recebido: {len(games)}")

    game_context = []
    for row, probs in zip(games, calibrated_probabilities):
        order, rank_by_outcome = rank_probabilities(probs)
        game_context.append((row, probs, order, rank_by_outcome))

    dp = {(0, 0, 0, 0): [Candidate(0.0, 0.0, [])]}
    for row, probs, _, rank_by_outcome in game_context:
        next_dp = defaultdict(list)
        for (singles, r1, r2, r3), candidates in dp.items():
            for choice in _choices_for_game(row, probs, rank_by_outcome):
                new_singles = singles + int(choice.is_single)
                counts = [r1, r2, r3]
                for rank in choice.ranks:
                    counts[rank - 1] += 1
                if new_singles > 9 or counts[0] > 9 or counts[1] > 5 or counts[2] > 5:
                    continue
                state = (new_singles, counts[0], counts[1], counts[2])
                for candidate in candidates:
                    next_dp[state].append(Candidate(
                        log_product=candidate.log_product + math.log(max(choice.q, 1e-15)),
                        inverse_sum=candidate.inverse_sum + 1.0 / max(choice.q, 1e-15),
                        choices=candidate.choices + [choice],
                    ))
        dp = {state: _pareto_prune(candidates) for state, candidates in next_dp.items()}

    finalists = dp.get((9, 9, 5, 5), [])
    if not finalists:
        raise RuntimeError("Nenhuma solução satisfaz simultaneamente todas as Hard Constraints.")

    best_probability = max(candidate.p13plus for candidate in finalists)
    threshold = best_probability * (1.0 - soft_tolerance)
    near_optimal = [candidate for candidate in finalists if candidate.p13plus >= threshold]
    selected = max(near_optimal, key=lambda candidate: (_soft_metrics(candidate.choices)["score"], candidate.p13plus))
    return selected, game_context, {
        "pareto_finalists": len(finalists),
        "near_optimal_finalists": len(near_optimal),
        "strict_best_p13plus": best_probability,
        "soft_tolerance": soft_tolerance,
        **_soft_metrics(selected.choices),
    }


def _validate_hard_constraints(games: List[dict], choices: Sequence[Choice]) -> dict:
    singles = sum(choice.is_single for choice in choices)
    doubles = len(choices) - singles
    rank_counts = {rank: sum(rank in choice.ranks for choice in choices) for rank in (1, 2, 3)}
    flamengo_ok = True
    for row, choice in zip(games, choices):
        flamengo_win = winner_outcome("FLAMENGO/RJ", row["Mandante"], row["Visitante"])
        if flamengo_win is not None and flamengo_win not in choice.outcomes:
            flamengo_ok = False
    checks = {
        "singles": singles,
        "doubles": doubles,
        "triples": 0,
        "top1_marks": rank_counts[1],
        "top2_marks": rank_counts[2],
        "top3_marks": rank_counts[3],
        "flamengo_win_included": flamengo_ok,
    }
    if (singles, doubles, rank_counts[1], rank_counts[2], rank_counts[3], flamengo_ok) != (9, 5, 9, 5, 5, True):
        raise AssertionError(f"Hard Constraints violadas: {checks}")
    return checks


def predict(
    contest_path: str | Path,
    model_path: str | Path = "models/model.json",
    output_path: str | Path = "output/predictions.csv",
    soft_tolerance: float = 0.0025,
) -> dict:
    games = preprocess(contest_path, require_actual=False)
    games.sort(key=lambda row: int(row["Jogo"]))
    model = load_json(model_path)

    calibrated_probabilities = [
        calibrate_probabilities(row["_probs"], model["alpha"], model["biases"])
        for row in games
    ]
    selected, context, optimizer_meta = optimize_ticket(games, calibrated_probabilities, soft_tolerance)
    checks = _validate_hard_constraints(games, selected.choices)

    hit_probabilities = [choice.q for choice in selected.choices]
    p13plus = p_at_least_13(hit_probabilities)
    p14 = p_exactly_14(hit_probabilities)
    p13 = p13plus - p14

    rows_out = []
    print("\n=== LOTECA ML | TELEMETRIA AUDITÁVEL ===")
    print(f"Concurso: {games[0]['Concurso']} | objetivo: maximizar P(>=13)")
    print(f"P(14)={p14:.8%} | P(13)={p13:.8%} | P(>=13)={p13plus:.8%}")
    print(f"Fronteira Pareto final: {optimizer_meta['pareto_finalists']} | quase-ótimos: {optimizer_meta['near_optimal_finalists']}")
    print("Hard: 9 secos / 5 duplos / 0 triplos | marcas top1/top2/top3 = 9/5/5")
    print("-" * 118)

    for row, probs, ctx, choice in zip(games, calibrated_probabilities, context, selected.choices):
        order = ctx[2]
        palpite = format_palpite(choice.outcomes)
        ordered_probs = [probs[outcome] for outcome in order]
        print(
            f"J{int(row['Jogo']):02d} {row['Mandante']} x {row['Visitante']} | "
            f"p1={probs['1']:.4f} pX={probs['X']:.4f} p2={probs['2']:.4f} | "
            f"ranking={order[0]}>{order[1]}>{order[2]} | palpite={palpite:<2} | q(hit)={choice.q:.4f}"
        )
        rows_out.append({
            "Concurso": row["Concurso"],
            "Jogo": row["Jogo"],
            "Mandante": row["Mandante"],
            "Visitante": row["Visitante"],
            "p(1)": decimal_pt(probs["1"]),
            "p(X)": decimal_pt(probs["X"]),
            "p(2)": decimal_pt(probs["2"]),
            "top1_result": order[0],
            "top2_result": order[1],
            "top3_result": order[2],
            "p(top1)": decimal_pt(ordered_probs[0]),
            "p(top2)": decimal_pt(ordered_probs[1]),
            "p(top3)": decimal_pt(ordered_probs[2]),
            "Palpite": palpite,
            "Tipo": "SECO" if choice.is_single else "DUPLO",
            "marcou_top1": int(1 in choice.ranks),
            "marcou_top2": int(2 in choice.ranks),
            "marcou_top3": int(3 in choice.ranks),
            "q_hit": decimal_pt(choice.q),
            "inclui_vitoria_palmeiras": int(choice.includes_palmeiras_win),
        })

    print("-" * 118)
    print(f"Soft: maior run Top1={optimizer_meta['longest_top1_run']} | fragmentos={optimizer_meta['top1_fragments']} | vitória Palmeiras marcada={optimizer_meta['palmeiras_win_marks']}")
    print(f"Validação Hard Constraints: OK -> {checks}\n")

    fields = [
        "Concurso", "Jogo", "Mandante", "Visitante", "p(1)", "p(X)", "p(2)",
        "top1_result", "top2_result", "top3_result", "p(top1)", "p(top2)", "p(top3)",
        "Palpite", "Tipo", "marcou_top1", "marcou_top2", "marcou_top3", "q_hit",
        "inclui_vitoria_palmeiras",
    ]
    write_csv(output_path, rows_out, fields)
    return {
        "p14": p14,
        "p13": p13,
        "p13plus": p13plus,
        "hard_constraints": checks,
        "optimizer": optimizer_meta,
        "output_path": str(output_path),
    }
