import sys; import os; sys.path.insert(0, os.path.abspath(".."))
import pandas as pd
import numpy as np
import pickle
import logging
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_model():
    logger.info("Loading training dataset...")
    try:
        df = pd.read_csv("training_data.csv")
    except FileNotFoundError:
        logger.error("training_data.csv not found! Run data_builder.py first.")
        return
        
    if len(df) < 10:
        logger.warning(f"Extremely sparse dataset ({len(df)} rows). Training may heavily overfit or fail.")
        
    # We choose NOT to use Lat/Lon for the generic MVP so the model learns purely physical relationships
    # rather than memorizing spatial coordinate biases, enabling global applicability theoretically.
    features = ['model_sst', 'sst_gradient', 'model_mld']
    X = df[features]
    y = df['target_delta_mld']
    
    logger.info(f"Training on {len(df)} samples with features: {features}")
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
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
    out_file = "model.pkl"
    with open(out_file, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Serialized optimal pipeline object to: {out_file}")

if __name__ == "__main__":
    train_model()
