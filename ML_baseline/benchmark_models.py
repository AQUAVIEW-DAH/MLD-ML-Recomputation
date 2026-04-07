import pandas as pd
import numpy as np
import logging
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from xgboost import XGBRegressor
from sklearn.linear_model import LinearRegression
import sys
import os

sys.path.insert(0, os.path.abspath(".."))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def benchmark_models():
    logger.info("Starting Multi-Model Benchmarking with Spatial Block Holdouts...")
    
    data_path = os.path.join(os.path.dirname(__file__), "training_data.csv")
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
        logger.info("Applying GroupShuffleSplit to prevent spatial data leakage.")
        gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
        train_idx, test_idx = next(gss.split(X, y, groups))
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        test_platform_counts = groups.iloc[test_idx].value_counts()
    else:
        logger.warning(f"Only {unique_platforms} unique platform(s). Falling back to random split.")
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        test_platform_counts = groups.iloc[y_test.index].value_counts()

    logger.info(f"Train: {len(X_train)} samples, Test: {len(X_test)} samples")
        
    models = {
        "HistGradientBoosting": HistGradientBoostingRegressor(max_iter=200, max_depth=5, random_state=42),
        "RandomForest": RandomForestRegressor(n_estimators=200, random_state=42),
        "XGBoost": XGBRegressor(n_estimators=200, max_depth=5, random_state=42),
        "LinearRegression": LinearRegression()
    }
    
    results = []
    
    for name, model in models.items():
        logger.info(f"Evaluating: {name}...")
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        
        mae = mean_absolute_error(y_test, preds)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        r2 = r2_score(y_test, preds)
        
        results.append({
            "Model": name,
            "MAE": round(mae, 3),
            "RMSE": round(rmse, 3),
            "R2": round(r2, 3)
        })
        
    results_df = pd.DataFrame(results).sort_values(by="MAE", ascending=True)
    
    logger.info("\n=== FINAL BENCHMARK LEADERBOARD ===")
    print(results_df.to_string(index=False))
    
    best_model = results_df.iloc[0]["Model"]
    best_mae = results_df.iloc[0]["MAE"]
    best_r2 = results_df.iloc[0]["R2"]
    logger.info(f"\nBest model: {best_model} (MAE={best_mae}m, R²={best_r2})")

    # Save updated benchmark results
    out_path = os.path.join(os.path.dirname(__file__), "benchmark_results.md")
    source_series = df.get("wod_source", pd.Series(["unknown"]))
    source_family_series = df.get("source_family", pd.Series(["unknown"]))
    with open(out_path, "w") as f:
        f.write(f"# ML Pipeline Benchmarking — v3 (Direct Source Ingestion)\n\n")
        f.write(f"**Timestamp:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Dataset:** {len(df)} profiles from direct sources ({', '.join(source_series.unique())})\n")
        f.write(f"**Region:** Gulf of Mexico (-98,18,-80,31)\n")
        f.write(f"**Validation:** GroupShuffleSplit by platform/cruise ({unique_platforms} groups)\n\n")
        f.write("## Multi-Model Leaderboard\n\n")
        f.write("| Model | MAE | RMSE | R² |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for _, row in results_df.iterrows():
            f.write(f"| **{row['Model']}** | {row['MAE']}m | {row['RMSE']}m | {row['R2']} |\n")
        f.write(f"\n## Data Summary\n")
        f.write(f"- Total profiles: {len(df)}\n")
        f.write(f"- Source families: {source_family_series.value_counts().to_dict()}\n")
        f.write(f"- Instruments: {df.get('instrument', pd.Series(['unknown'])).value_counts().to_dict()}\n")
        f.write(f"- Train/Test split: {len(X_train)}/{len(X_test)}\n")
        f.write(f"- Held-out platforms: {test_platform_counts.head(10).to_dict()}\n")
        f.write(f"- Observed MLD range: {df['observed_mld'].min():.1f}m to {df['observed_mld'].max():.1f}m\n")
        f.write(f"- Model MLD range: {df['model_mld'].min():.1f}m to {df['model_mld'].max():.1f}m\n")
    logger.info(f"Benchmark results saved to: {out_path}")

if __name__ == "__main__":
    benchmark_models()
