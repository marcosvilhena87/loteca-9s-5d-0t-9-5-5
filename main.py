"""Run training, calibration and constrained ticket optimization."""

from scripts.predict_results import predict, print_telemetry
from scripts.train_model import train


def main() -> None:
    model = train("data/concursos_anteriores.csv", "models/model.json")
    print("=== CALIBRAÇÃO ===")
    status = "promovida" if model["calibration_promoted"] else "rejeitada; usando probabilidades brutas"
    print(f"Calibração: {status}")
    print(f"Temperatura candidata: {model['validation_candidate_temperature']:.2f} | implantação: {model['temperature']:.2f}")
    print(f"Log-loss validação: bruto={model['validation_log_loss_raw']:.6f}, calibrado={model['validation_log_loss_calibrated']:.6f}")
    rank_status = "promovida" if model["rank_calibration_promoted"] else "rejeitada"
    print(f"Calibração por rank: {rank_status} | lifts Top1/2/3={model['rank_lifts']}")
    risk_status = "promovida" if model["risk_rank_calibration_promoted"] else "rejeitada"
    print(f"Calibração por risk_rank: {risk_status}")
    print(f"Log-loss risk_rank: base={model['validation_log_loss_before_risk_rank']:.6f}, calibrado={model['validation_log_loss_risk_rank']:.6f}")
    tail = model["risk_rank_tail_validation"]
    print("Validação real dos bilhetes risk_rank: "
          f"13+ {tail['base_13plus']} -> {tail['challenger_13plus']} | "
          f"12+ {tail['base_12plus']} -> {tail['challenger_12plus']} | "
          f"Net13Gain={tail['net13_gain']:+d} "
          f"({tail['crossed_to_13plus']} ganhos, {tail['fell_below_13']} perdas)")
    print(f"Média de acertos: {tail['base_mean_hits']:.3f} -> {tail['challenger_mean_hits']:.3f}")
    print("\n=== AUDITORIA HISTÓRICA DO RISK_RANK ===")
    print("Rank | n | pTop1 previsto | hit observado | fail observado | IC95% hit | estabilidade | confiança | lift")
    for item in model["risk_rank_audit"]:
        print(f"{item['risk_rank']:>4} | {item['n_jogos']:>3} | {item['pTop1_medio_previsto']:.4f} | "
              f"{item['Top1_hit_observado']:.4f} | {item['Top1_fail_observado']:.4f} | "
              f"[{item['ic95_hit_low']:.4f}, {item['ic95_hit_high']:.4f}] | "
              f"{item['risk_rank_stability']:.3f} | {item['confidence_label']} "
              f"({item['historical_confidence']:.3f}) | {item['lift_shrunk']:.4f}")
    predictions, success = predict("data/proximo_concurso.csv", "models/model.json", "output/predictions.csv")
    print_telemetry(predictions, success)


if __name__ == "__main__":
    main()
