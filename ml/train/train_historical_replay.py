import os
import pickle
import logging
from pathlib import Path
import sys

import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ml.paths import DATASETS_DIR, MODELS_DIR, TRAINING_REPORTS_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_TRAIN_PATH = str(DATASETS_DIR / "training_data_train_historical_replay_pre_2025_07_07.csv")
DEFAULT_HOLDOUT_PATH = str(DATASETS_DIR / "training_data_holdout_historical_replay_2025_jul_aug.csv")
DEFAULT_MODEL_OUTPUT = str(MODELS_DIR / "model_historical_replay_2025_jul_aug.pkl")
DEFAULT_REPORT_OUTPUT = str(TRAINING_REPORTS_DIR / "train_ml_report_historical_replay_2025_jul_aug.md")
FEATURES = ['model_sst', 'sst_gradient', 'model_salinity', 'kinetic_energy', 'model_mld']

MODELS = {
    "LinearRegression": LinearRegression(),
    "RandomForest": RandomForestRegressor(n_estimators=200, random_state=42),
    "XGBoost": XGBRegressor(n_estimators=200, max_depth=5, random_state=42, n_jobs=2),
    "HistGradientBoosting": HistGradientBoostingRegressor(max_iter=200, max_depth=5, random_state=42),
}


def load_frame(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df.dropna(subset=["target_delta_mld", "observed_mld"]).copy()


def metric_summary(obs: pd.Series, pred: pd.Series) -> dict:
    return {
        "mae": float(mean_absolute_error(obs, pred)),
        "rmse": float(mean_squared_error(obs, pred) ** 0.5),
        "r2": float(r2_score(obs, pred)),
    }


def main() -> None:
    train_path = os.getenv("HIST_TRAIN_DATA_PATH", DEFAULT_TRAIN_PATH)
    holdout_path = os.getenv("HIST_HOLDOUT_DATA_PATH", DEFAULT_HOLDOUT_PATH)
    model_output = os.getenv("HIST_MODEL_OUTPUT_PATH", DEFAULT_MODEL_OUTPUT)
    report_output = os.getenv("HIST_REPORT_OUTPUT_PATH", DEFAULT_REPORT_OUTPUT)

    train_df = load_frame(train_path)
    holdout_df = load_frame(holdout_path)

    X_train = train_df[FEATURES]
    y_train = train_df["target_delta_mld"]
    X_holdout = holdout_df[FEATURES]
    y_holdout = holdout_df["target_delta_mld"]
    obs_holdout = holdout_df["observed_mld"]
    raw_holdout = holdout_df["model_mld"]

    raw_metrics = metric_summary(obs_holdout, raw_holdout)

    results = []
    fitted_models = {}
    for name, model in MODELS.items():
        logger.info("Training %s on %d rows", name, len(train_df))
        fitted = clone(model)
        fitted.fit(X_train, y_train)
        pred_delta = fitted.predict(X_holdout)
        corrected = raw_holdout + pred_delta

        delta_mae = mean_absolute_error(y_holdout, pred_delta)
        corrected_metrics = metric_summary(obs_holdout, corrected)

        results.append({
            "Model": name,
            "Corrected_MAE": round(corrected_metrics["mae"], 3),
            "Corrected_RMSE": round(corrected_metrics["rmse"], 3),
            "Corrected_R2": round(corrected_metrics["r2"], 3),
            "Delta_MAE": round(delta_mae, 3),
            "Mean_Correction": round(float(pd.Series(pred_delta).mean()), 3),
        })
        fitted_models[name] = fitted

    results_df = pd.DataFrame(results).sort_values(["Corrected_MAE", "Corrected_RMSE"], ascending=[True, True])
    best_name = results_df.iloc[0]["Model"]
    best_model = fitted_models[best_name]

    with open(model_output, "wb") as f:
        pickle.dump(best_model, f)

    with open(report_output, "w") as f:
        f.write("# Historical Replay Training Report\n\n")
        f.write(f"- Train data: `{train_path}`\n")
        f.write(f"- Holdout data: `{holdout_path}`\n")
        f.write(f"- Output artifact: `{model_output}`\n")
        f.write(f"- Train rows: {len(train_df)}\n")
        f.write(f"- Holdout rows: {len(holdout_df)}\n")
        f.write(f"- Train platforms: {train_df['platform_id'].nunique()}\n")
        f.write(f"- Holdout platforms: {holdout_df['platform_id'].nunique()}\n")
        f.write(f"- Train source families: {train_df['source_family'].value_counts().to_dict()}\n")
        f.write(f"- Holdout source families: {holdout_df['source_family'].value_counts().to_dict()}\n")
        f.write(f"- Selected model: `{best_name}`\n\n")
        f.write("## Raw RTOFS Holdout Baseline\n\n")
        f.write(f"- Raw MAE: {raw_metrics['mae']:.3f}m\n")
        f.write(f"- Raw RMSE: {raw_metrics['rmse']:.3f}m\n")
        f.write(f"- Raw R²: {raw_metrics['r2']:.3f}\n\n")
        f.write("## Corrected Holdout Leaderboard\n\n")
        f.write("| Model | Corrected MAE | Corrected RMSE | Corrected R² | Residual MAE | Mean Correction |\n")
        f.write("| :--- | ---: | ---: | ---: | ---: | ---: |\n")
        for _, row in results_df.iterrows():
            f.write(
                f"| {row['Model']} | {row['Corrected_MAE']}m | {row['Corrected_RMSE']}m | {row['Corrected_R2']} | {row['Delta_MAE']}m | {row['Mean_Correction']}m |\n"
            )
        best = results_df.iloc[0]
        f.write("\n## Interpretation\n\n")
        f.write("- This artifact is trained strictly on pre-holdout rows and evaluated on the frozen historical replay window.\n")
        f.write(
            f"- Best corrected holdout result: `{best_name}` with MAE {best['Corrected_MAE']}m versus raw RTOFS MAE {raw_metrics['mae']:.3f}m.\n"
        )
        f.write(
            f"- Best corrected holdout R²: {best['Corrected_R2']} versus raw RTOFS R² {raw_metrics['r2']:.3f}.\n"
        )
        f.write("- Use this artifact for historical replay mode, not as a claim of real-time 2026 readiness.\n")

    print(results_df.to_string(index=False))
    print(f"Raw baseline: MAE={raw_metrics['mae']:.3f} RMSE={raw_metrics['rmse']:.3f} R2={raw_metrics['r2']:.3f}")
    print(f"Saved best model to {model_output}")
    print(f"Saved report to {report_output}")


if __name__ == "__main__":
    main()
