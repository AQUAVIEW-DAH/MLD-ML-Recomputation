import sys; import os; sys.path.insert(0, os.path.abspath(".."))
import pandas as pd
import numpy as np
import pickle
import logging
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import mean_absolute_error, r2_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_model():
    logger.info("Loading training dataset...")
    try:
        df = pd.read_csv("ML_baseline/training_data.csv")
    except FileNotFoundError:
        logger.error("training_data.csv not found! Run data_builder.py first.")
        return
        
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
    
    # HistGradientBoostingRegressor is scikit-learn's answer to LightGBM.
    # Tremendously fast and naturally handles missing values.
    # It builds trees interpreting the non-linear relationship between SST fronts and MLD residuals.
    model = HistGradientBoostingRegressor(
        max_iter=100, 
        learning_rate=0.1, 
        max_depth=5, 
        random_state=42
    )
    
    logger.info("Fitting Gradient Boosted Trees...")
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
    out_file = "ML_baseline/model.pkl"
    with open(out_file, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Serialized optimal pipeline object to: {out_file}")

if __name__ == "__main__":
    train_model()
