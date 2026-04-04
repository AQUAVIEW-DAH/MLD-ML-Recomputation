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
    
    data_path = "ML_baseline/training_data.csv"
    if not os.path.exists(data_path):
        logger.error(f"{data_path} not found.")
        return
        
    df = pd.read_csv(data_path)
    
    if len(df) < 5:
        logger.error("Insufficient dataset rows for benchmarking.")
        return
        
    features = ['model_sst', 'sst_gradient', 'model_salinity', 'kinetic_energy', 'model_mld']
    X = df[features]
    y = df['target_delta_mld']
    groups = df['platform_id']
    
    unique_platforms = groups.nunique()
    logger.info(f"Loaded {len(df)} profiles across {unique_platforms} independent float deployments.")
    
    # Implementing Spatial/Platform Block Split recommended by Oceanographic Literature
    if unique_platforms > 1:
        logger.info("Applying standard GroupShuffleSplit to prevent spatial Data Leakage.")
        gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
        train_idx, test_idx = next(gss.split(X, y, groups))
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    else:
        logger.warning(f"Only {unique_platforms} unique platform found. Falling back to naive random split specifically for MVP pipeline testing.")
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
    models = {
        "XGBoost": XGBRegressor(n_estimators=100, max_depth=5, random_state=42),
        "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42),
        "HistGradientBoosting": HistGradientBoostingRegressor(max_iter=100, random_state=42),
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
    logger.info(f"\nThe optimal model for the production ML artifact is: {best_model}")

if __name__ == "__main__":
    benchmark_models()
