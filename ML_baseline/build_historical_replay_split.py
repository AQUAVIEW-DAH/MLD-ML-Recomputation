import os
from datetime import datetime

import pandas as pd

DEFAULT_INPUT_PATH = "ML_baseline/training_data_combined_rtofs_2024_2025.csv"
DEFAULT_HOLDOUT_START = "2025-07-07"
DEFAULT_HOLDOUT_END = "2025-08-31"
DEFAULT_TRAIN_OUTPUT = "ML_baseline/training_data_train_historical_replay_pre_2025_07_07.csv"
DEFAULT_HOLDOUT_OUTPUT = "ML_baseline/training_data_holdout_historical_replay_2025_jul_aug.csv"
DEFAULT_REPORT_OUTPUT = "ML_baseline/historical_replay_split_report_2025_jul_aug.md"


def parse_row_date(value: str) -> pd.Timestamp:
    value = str(value).strip()
    if not value:
        raise ValueError("Empty date value")
    fmt = "%Y-%m-%d" if "-" in value else "%Y%m%d"
    return pd.Timestamp(datetime.strptime(value, fmt).date())


def summarize(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "rows": 0,
            "dates": 0,
            "platforms": 0,
            "sources": {},
            "instruments": {},
            "min_date": "n/a",
            "max_date": "n/a",
            "top_dates": {},
        }

    return {
        "rows": int(len(df)),
        "dates": int(df["split_date"].nunique()),
        "platforms": int(df["platform_id"].nunique()) if "platform_id" in df.columns else 0,
        "sources": df.get("source_family", pd.Series(dtype=object)).value_counts().to_dict(),
        "instruments": df.get("instrument", pd.Series(dtype=object)).value_counts().to_dict(),
        "min_date": str(df["split_date"].min().date()),
        "max_date": str(df["split_date"].max().date()),
        "top_dates": {str(k.date()): int(v) for k, v in df["split_date"].value_counts().head(10).sort_index().items()},
    }


def main() -> None:
    input_path = os.getenv("HIST_INPUT_DATA_PATH", DEFAULT_INPUT_PATH)
    holdout_start = pd.Timestamp(os.getenv("HIST_HOLDOUT_START", DEFAULT_HOLDOUT_START))
    holdout_end = pd.Timestamp(os.getenv("HIST_HOLDOUT_END", DEFAULT_HOLDOUT_END))
    train_output = os.getenv("HIST_TRAIN_OUTPUT_PATH", DEFAULT_TRAIN_OUTPUT)
    holdout_output = os.getenv("HIST_HOLDOUT_OUTPUT_PATH", DEFAULT_HOLDOUT_OUTPUT)
    report_output = os.getenv("HIST_SPLIT_REPORT_PATH", DEFAULT_REPORT_OUTPUT)

    df = pd.read_csv(input_path)
    raw_dates = df["obs_date"].fillna(df["rtofs_date"])
    df["split_date"] = raw_dates.map(parse_row_date)

    holdout_mask = (df["split_date"] >= holdout_start) & (df["split_date"] <= holdout_end)
    holdout_df = df.loc[holdout_mask].copy()
    train_df = df.loc[~holdout_mask].copy()

    train_df.drop(columns=["split_date"]).to_csv(train_output, index=False)
    holdout_df.drop(columns=["split_date"]).to_csv(holdout_output, index=False)

    train_summary = summarize(train_df)
    holdout_summary = summarize(holdout_df)

    holdout_platforms = set(holdout_df.get("platform_id", pd.Series(dtype=object)).dropna().astype(str))
    train_platforms = set(train_df.get("platform_id", pd.Series(dtype=object)).dropna().astype(str))
    unseen_platforms = sorted(holdout_platforms - train_platforms)

    with open(report_output, "w") as f:
        f.write("# Historical Replay Split Report\n\n")
        f.write(f"- Input data: `{input_path}`\n")
        f.write(f"- Holdout window: `{holdout_start.date()}` to `{holdout_end.date()}`\n")
        f.write(f"- Train output: `{train_output}`\n")
        f.write(f"- Holdout output: `{holdout_output}`\n\n")

        f.write("## Train Summary\n\n")
        for key, value in train_summary.items():
            f.write(f"- {key.replace('_', ' ').title()}: {value}\n")

        f.write("\n## Holdout Summary\n\n")
        for key, value in holdout_summary.items():
            f.write(f"- {key.replace('_', ' ').title()}: {value}\n")

        f.write("\n## Platform Overlap\n\n")
        f.write(f"- Holdout platforms also seen in train: {len(holdout_platforms & train_platforms)}\n")
        f.write(f"- Holdout platforms unseen in train: {len(unseen_platforms)}\n")
        if unseen_platforms:
            f.write(f"- Unseen platform examples: {unseen_platforms[:10]}\n")

    print(f"Wrote train split to {train_output}")
    print(f"Wrote holdout split to {holdout_output}")
    print(f"Wrote split report to {report_output}")


if __name__ == "__main__":
    main()
