import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
import pickle
import logging
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.linear_model import LinearRegression
from xgboost import XGBRegressor
from ml.paths import DATASETS_DIR, MODELS_DIR, TRAINING_REPORTS_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_DATA_PATH = str(DATASETS_DIR / "training_data.csv")
DEFAULT_MODEL_PATH = str(MODELS_DIR / "model.pkl")
DEFAULT_REPORT_PATH = str(TRAINING_REPORTS_DIR / "train_ml_report.md")


def build_model(model_name: str):
    if model_name == "linear":
        return LinearRegression()
    if model_name == "random_forest":
        return RandomForestRegressor(n_estimators=200, random_state=42)
    if model_name == "xgboost":
        return XGBRegressor(n_estimators=200, max_depth=5, random_state=42, n_jobs=2)
    return HistGradientBoostingRegressor(
        max_iter=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=42,
    )


def write_report(report_path, data_path, model_name, out_file, df, train_idx, test_idx, groups, mae, r2):
    with open(report_path, "w") as f:
        f.write("# Train ML Report\n\n")
        f.write(f"- Data path: `{data_path}`\n")
        f.write(f"- Model type: `{model_name}`\n")
        f.write(f"- Output artifact: `{out_file}`\n")
        f.write(f"- Rows: {len(df)}\n")
        f.write(f"- Platforms/groups: {groups.nunique()}\n")
        f.write(f"- Train rows: {len(train_idx)}\n")
        f.write(f"- Test rows: {len(test_idx)}\n")
        f.write(f"- Test MAE: {mae:.3f}m\n")
        f.write(f"- Test R²: {r2:.3f}\n")
        if "source_family" in df.columns:
            f.write(f"- Source families: {df['source_family'].value_counts().to_dict()}\n")
        if "instrument" in df.columns:
            f.write(f"- Instruments: {df['instrument'].value_counts().to_dict()}\n")
        f.write("- This is a candidate artifact only; do not overwrite/freeze the production `model.pkl` from this run.\n")

def train_model():
    logger.info("Loading training dataset...")
    data_path = os.getenv("TRAIN_DATA_PATH", DEFAULT_DATA_PATH)
    out_file = os.getenv("TRAIN_MODEL_OUTPUT", DEFAULT_MODEL_PATH)
    report_path = os.getenv("TRAIN_REPORT_PATH", DEFAULT_REPORT_PATH)
    model_name = os.getenv("TRAIN_MODEL_TYPE", "hist_gbm").strip().lower()
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        logger.error("%s not found! Run data builder first.", data_path)
        return

    df = df.dropna(subset=["target_delta_mld", "observed_mld"]).copy()
        
    if len(df) < 10:
        logger.warning(f"Extremely sparse dataset ({len(df)} rows). Training may heavily overfit or fail.")
        
    # We choose NOT to use Lat/Lon for the generic MVP so the model learns purely physical relationships
    # rather than memorizing spatial coordinate biases, enabling global applicability theoretically.
    features = ['model_sst', 'sst_gradient', 'model_salinity', 'kinetic_energy', 'model_mld']
    X = df[features]
    y = df['target_delta_mld']
    
    if 'platform_id' not in df.columns:
        logger.warning("No 'platform_id' found, falling back to random groups")
        groups = np.arange(len(df))
    else:
        groups = df['platform_id']
    
    logger.info(f"Training on {len(df)} samples with features: {features}")
    
    # Use GroupShuffleSplit to prevent data leakage from the same temporal mooring/glider deployments
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(gss.split(X, y, groups=groups))
    
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    
    if 'platform_id' in df.columns:
        train_platforms = df.iloc[train_idx]['platform_id'].nunique()
        test_platforms = df.iloc[test_idx]['platform_id'].nunique()
        logger.info(f"Split distribution -> Train: {len(X_train)} samples ({train_platforms} platforms), Test: {len(X_test)} samples ({test_platforms} platforms)")
    
    model = build_model(model_name)
    
    logger.info("Fitting model type: %s", model_name)
    model.fit(X_train, y_train)
    
    # Evaluate
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    
    logger.info("=== EVALUATION REPORT ===")
    logger.info(f"Mean Absolute Error (Test): {mae:.2f} meters")
    logger.info(f"R^2 Score (Test): {r2:.3f}")
    
    # In tree regression, feature importances are harder to extract directly from HistGBM without permutation,
    # but the evaluation metrics directly represent the proof of concept viability.
    
    # Save the artifact
    with open(out_file, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Serialized optimal pipeline object to: {out_file}")
    write_report(report_path, data_path, model_name, out_file, df, train_idx, test_idx, groups, mae, r2)
    logger.info("Training report saved to: %s", report_path)

if __name__ == "__main__":
    train_model()
