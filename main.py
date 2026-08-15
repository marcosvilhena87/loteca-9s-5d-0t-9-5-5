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
    predictions, success = predict("data/proximo_concurso.csv", "models/model.json", "output/predictions.csv")
    print_telemetry(predictions, success)


if __name__ == "__main__":
    main()
