import pandas as pd
import numpy as np
import logging
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.base import clone
from xgboost import XGBRegressor
from sklearn.linear_model import LinearRegression
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ml.paths import BENCHMARK_REPORTS_DIR, DATASETS_DIR

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

N_SPLITS = int(os.getenv("BENCHMARK_N_SPLITS", "10"))
TEST_SIZE = float(os.getenv("BENCHMARK_TEST_SIZE", "0.2"))


def benchmark_models():
    logger.info("Starting Multi-Model Benchmarking with repeated spatial block holdouts...")
    
    data_path = os.getenv(
        "BENCHMARK_DATA_PATH",
        str(DATASETS_DIR / "training_data.csv"),
    )
    if not os.path.exists(data_path):
        logger.error(f"{data_path} not found.")
        return
        
    df = pd.read_csv(data_path)

    # Filter to rows with valid MLD data
    df = df.dropna(subset=["target_delta_mld", "observed_mld"])
    
    if len(df) < 5:
        logger.error(f"Insufficient dataset rows for benchmarking ({len(df)} rows).")
        return

    logger.info(f"Loaded {len(df)} profiles with valid MLD data.")
    if "instrument" in df.columns:
        logger.info(f"  Instruments: {df['instrument'].value_counts().to_dict()}")
    if "wod_source" in df.columns:
        logger.info(f"  Sources: {df['wod_source'].value_counts().to_dict()}")
        
    features = ['model_sst', 'sst_gradient', 'model_salinity', 'kinetic_energy', 'model_mld']
    X = df[features]
    y = df['target_delta_mld']

    # Use platform_id or cruise_id for grouping
    if "platform_id" in df.columns:
        groups = df["platform_id"]
    elif "cruise_id" in df.columns:
        groups = df["cruise_id"]
    else:
        groups = pd.Series(np.arange(len(df)))
    
    unique_platforms = groups.nunique()
    logger.info(f"Grouping by {unique_platforms} independent platforms/cruises.")
    
    # Implementing Spatial/Platform Block Split recommended by Oceanographic Literature
    if unique_platforms > 1:
        n_splits = max(1, N_SPLITS)
        logger.info(
            "Applying GroupShuffleSplit to prevent spatial data leakage (%d splits, test_size=%.2f).",
            n_splits,
            TEST_SIZE,
        )
        splits = list(GroupShuffleSplit(n_splits=n_splits, test_size=TEST_SIZE, random_state=42).split(X, y, groups))
    else:
        logger.warning(f"Only {unique_platforms} unique platform(s). Falling back to random split.")
        train_idx, test_idx = train_test_split(np.arange(len(df)), test_size=TEST_SIZE, random_state=42)
        splits = [(train_idx, test_idx)]

    first_train_idx, first_test_idx = splits[0]
    test_platform_counts = groups.iloc[first_test_idx].value_counts()
    logger.info("First split Train: %d samples, Test: %d samples", len(first_train_idx), len(first_test_idx))
        
    models = {
        "HistGradientBoosting": HistGradientBoostingRegressor(max_iter=200, max_depth=5, random_state=42),
        "RandomForest": RandomForestRegressor(n_estimators=200, random_state=42),
        "XGBoost": XGBRegressor(n_estimators=200, max_depth=5, random_state=42, n_jobs=2),
        "LinearRegression": LinearRegression()
    }
    
    results = []
    split_rows = []
    
    for name, model in models.items():
        logger.info(f"Evaluating: {name}...")
        metrics = []
        for split_id, (train_idx, test_idx) in enumerate(splits, start=1):
            split_model = clone(model)
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            split_model.fit(X_train, y_train)
            preds = split_model.predict(X_test)

            mae = mean_absolute_error(y_test, preds)
            rmse = np.sqrt(mean_squared_error(y_test, preds))
            r2 = r2_score(y_test, preds)
            metrics.append({"mae": mae, "rmse": rmse, "r2": r2})

            split_rows.append({
                "Model": name,
                "Split": split_id,
                "TestRows": len(test_idx),
                "TestGroups": groups.iloc[test_idx].nunique(),
                "MAE": round(mae, 3),
                "RMSE": round(rmse, 3),
                "R2": round(r2, 3),
                "HeldOut": groups.iloc[test_idx].value_counts().head(6).to_dict(),
            })

        metrics_df = pd.DataFrame(metrics)
        
        results.append({
            "Model": name,
            "MAE_mean": round(metrics_df["mae"].mean(), 3),
            "MAE_std": round(metrics_df["mae"].std(ddof=0), 3),
            "RMSE_mean": round(metrics_df["rmse"].mean(), 3),
            "RMSE_std": round(metrics_df["rmse"].std(ddof=0), 3),
            "R2_mean": round(metrics_df["r2"].mean(), 3),
            "R2_std": round(metrics_df["r2"].std(ddof=0), 3),
            "MAE_min": round(metrics_df["mae"].min(), 3),
            "MAE_max": round(metrics_df["mae"].max(), 3),
        })
        
    results_df = pd.DataFrame(results).sort_values(by="MAE_mean", ascending=True)
    split_df = pd.DataFrame(split_rows)
    undefined_r2_splits = int(split_df["R2"].isna().sum())
    
    logger.info("\n=== FINAL BENCHMARK LEADERBOARD ===")
    print(results_df.to_string(index=False))
    
    best_model = results_df.iloc[0]["Model"]
    best_mae = results_df.iloc[0]["MAE_mean"]
    best_r2 = results_df.iloc[0]["R2_mean"]
    logger.info(f"\nBest model: {best_model} (mean MAE={best_mae}m, mean R²={best_r2})")

    # Save updated benchmark results
    out_path = os.getenv(
        "BENCHMARK_OUTPUT_PATH",
        str(BENCHMARK_REPORTS_DIR / "benchmark_results.md"),
    )
    source_series = df.get("wod_source", pd.Series(["unknown"]))
    source_family_series = df.get("source_family", pd.Series(["unknown"]))
    with open(out_path, "w") as f:
        f.write(f"# ML Pipeline Benchmarking — v3 (Direct Source Ingestion)\n\n")
        f.write(f"**Timestamp:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Data path:** `{data_path}`\n")
        f.write(f"**Dataset:** {len(df)} profiles from direct sources ({', '.join(source_series.unique())})\n")
        f.write(f"**Region:** Gulf of Mexico (-98,18,-80,31)\n")
        f.write(
            f"**Validation:** Repeated GroupShuffleSplit by platform/cruise "
            f"({unique_platforms} groups, {len(splits)} splits, test_size={TEST_SIZE:.2f})\n\n"
        )
        f.write("## Multi-Model Leaderboard\n\n")
        f.write("| Model | MAE mean | MAE std | RMSE mean | RMSE std | R² mean | R² std | MAE range |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for _, row in results_df.iterrows():
            f.write(
                f"| **{row['Model']}** | {row['MAE_mean']}m | {row['MAE_std']}m | "
                f"{row['RMSE_mean']}m | {row['RMSE_std']}m | {row['R2_mean']} | "
                f"{row['R2_std']} | {row['MAE_min']}m-{row['MAE_max']}m |\n"
            )
        f.write("\n## Validation Interpretation\n")
        f.write(
            f"- Best repeated grouped MAE: {best_model} at {best_mae}m mean MAE "
            f"with mean R²={best_r2}.\n"
        )
        f.write(
            "- This repeated grouped result is a data-coverage diagnostic, not a production-ready "
            "model acceptance result; cross-platform generalization remains unstable.\n"
        )
        if undefined_r2_splits:
            f.write(
                f"- R² was undefined for {undefined_r2_splits} model/split evaluations because "
                "the grouped test fold had fewer than two rows.\n"
            )
        f.write("- Do not freeze or accept a new `model.pkl` from this run.\n")

        f.write(f"\n## Data Summary\n")
        f.write(f"- Total profiles: {len(df)}\n")
        f.write(f"- Source families: {source_family_series.value_counts().to_dict()}\n")
        f.write(f"- Instruments: {df.get('instrument', pd.Series(['unknown'])).value_counts().to_dict()}\n")
        f.write(f"- First split train/test: {len(first_train_idx)}/{len(first_test_idx)}\n")
        f.write(f"- First split held-out platforms: {test_platform_counts.head(10).to_dict()}\n")
        f.write(f"- Test rows per split: min={split_df['TestRows'].min()}, max={split_df['TestRows'].max()}\n")
        f.write(f"- Observed MLD range: {df['observed_mld'].min():.1f}m to {df['observed_mld'].max():.1f}m\n")
        f.write(f"- Model MLD range: {df['model_mld'].min():.1f}m to {df['model_mld'].max():.1f}m\n")

        f.write("\n## Split Diagnostics\n\n")
        f.write("| Model | Split | Test rows | Test groups | MAE | RMSE | R² | Held-out platforms |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for _, row in split_df.sort_values(["Model", "Split"]).iterrows():
            f.write(
                f"| {row['Model']} | {int(row['Split'])} | {int(row['TestRows'])} | "
                f"{int(row['TestGroups'])} | {row['MAE']}m | {row['RMSE']}m | "
                f"{row['R2']} | {row['HeldOut']} |\n"
            )
    logger.info(f"Benchmark results saved to: {out_path}")

if __name__ == "__main__":
    benchmark_models()
