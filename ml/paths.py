"""Shared repository paths for the MLD replay prototype."""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
DATASETS_DIR = ARTIFACTS_DIR / "datasets"
MODELS_DIR = ARTIFACTS_DIR / "models"
AUDITS_DIR = ARTIFACTS_DIR / "audits"
REPORTS_DIR = ARTIFACTS_DIR / "reports"
BENCHMARK_REPORTS_DIR = REPORTS_DIR / "benchmarks"
SOURCE_REPORTS_DIR = REPORTS_DIR / "source_audits"
TRAINING_REPORTS_DIR = REPORTS_DIR / "training"
LOGS_DIR = ROOT_DIR / "logs"
