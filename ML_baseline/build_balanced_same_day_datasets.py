"""
Build balanced same-day RTOFS training variants from completed source audits.

This script does not refetch source data and never overwrites training_data.csv.
It is for testing whether capped ERDDAP glider density improves grouped
validation relative to the all-source same-day table.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
WOD_PATH = BASE_DIR / "training_data_wod_xbt_rtofs_2024_2025.csv"
ARGO_PATH = BASE_DIR / "training_data_argo_gdac_rtofs_2024_2025.csv"
ERDDAP_PATH = BASE_DIR / "training_data_erddap_glider_rtofs_2024_2025.csv"
REPORT_PATH = BASE_DIR / "BALANCED_SAME_DAY_RTOFS_REPORT.md"
MAX_OBSERVED_MLD_M = 100.0


VARIANTS = [
    {
        "name": "erddap_cell025_cap1",
        "description": "All WOD+Argo rows plus at most 1 ERDDAP row per platform/date/0.25-degree cell.",
        "erddap_cell_degree": 0.25,
        "erddap_cap": 1,
    },
    {
        "name": "erddap_cell025_cap2",
        "description": "All WOD+Argo rows plus at most 2 ERDDAP rows per platform/date/0.25-degree cell.",
        "erddap_cell_degree": 0.25,
        "erddap_cap": 2,
    },
    {
        "name": "erddap_cell025_cap3",
        "description": "All WOD+Argo rows plus at most 3 ERDDAP rows per platform/date/0.25-degree cell.",
        "erddap_cell_degree": 0.25,
        "erddap_cap": 3,
    },
]


def cell_count(df: pd.DataFrame, degree: float) -> int:
    if df.empty:
        return 0
    cells = pd.DataFrame(
        {
            "lat": (df["lat"].astype(float) // degree) * degree,
            "lon": (df["lon"].astype(float) // degree) * degree,
        }
    ).drop_duplicates()
    return int(len(cells))


def load_sources() -> pd.DataFrame:
    df = pd.concat(
        [pd.read_csv(WOD_PATH), pd.read_csv(ARGO_PATH), pd.read_csv(ERDDAP_PATH)],
        ignore_index=True,
        sort=False,
    )
    observed_mld = pd.to_numeric(df["observed_mld"], errors="coerce")
    return df[observed_mld.between(10.0, MAX_OBSERVED_MLD_M, inclusive="both")].copy()


def cap_erddap(df: pd.DataFrame, cell_degree: float, cap: int) -> pd.DataFrame:
    non_erddap = df[df["source_family"] != "ERDDAP_GLIDER"].copy()
    erddap = df[df["source_family"] == "ERDDAP_GLIDER"].copy()
    erddap["lat_cell"] = (erddap["lat"].astype(float) // cell_degree) * cell_degree
    erddap["lon_cell"] = (erddap["lon"].astype(float) // cell_degree) * cell_degree
    erddap["time_delta_sort"] = pd.to_numeric(
        erddap.get("obs_model_time_delta_hours"),
        errors="coerce",
    ).fillna(999.0)
    erddap = erddap.sort_values(
        [
            "platform_id",
            "obs_date",
            "lat_cell",
            "lon_cell",
            "time_delta_sort",
            "obs_time",
        ],
        kind="mergesort",
    )
    erddap = erddap.groupby(
        ["platform_id", "obs_date", "lat_cell", "lon_cell"],
        group_keys=False,
    ).head(cap)
    erddap = erddap.drop(columns=["lat_cell", "lon_cell", "time_delta_sort"])
    return pd.concat([non_erddap, erddap], ignore_index=True, sort=False)


def summarize(name: str, description: str, df: pd.DataFrame, out_path: Path) -> dict[str, object]:
    return {
        "variant": name,
        "description": description,
        "path": str(out_path.relative_to(BASE_DIR.parent)),
        "rows": int(len(df)),
        "platforms": int(df["platform_id"].nunique()),
        "dates": int(df["obs_date"].nunique()),
        "source_families": df["source_family"].value_counts().to_dict(),
        "cell025": cell_count(df, 0.25),
        "cell05": cell_count(df, 0.5),
        "cell10": cell_count(df, 1.0),
        "top_platforms": df["platform_id"].value_counts().head(8).to_dict(),
        "obs_mld_min": float(df["observed_mld"].min()),
        "obs_mld_max": float(df["observed_mld"].max()),
    }


def write_report(summaries: list[dict[str, object]]) -> None:
    with REPORT_PATH.open("w") as f:
        f.write("# Balanced Same-Day RTOFS Dataset Audit\n\n")
        f.write("## Purpose\n")
        f.write(
            "Build source-balanced variants from completed WOD-XBT, Argo GDAC, "
            "and ERDDAP glider same-day RTOFS datasets. These variants keep all "
            "WOD-XBT and Argo rows, then cap repeated ERDDAP glider observations "
            "within platform/date/0.25-degree cells.\n\n"
        )
        f.write("## Dataset Variants\n\n")
        f.write(
            "| Variant | Rows | Source Families | Platforms | Dates | "
            "0.25° Cells | 0.5° Cells | 1.0° Cells |\n"
        )
        f.write("| :--- | ---: | :--- | ---: | ---: | ---: | ---: | ---: |\n")
        for summary in summaries:
            f.write(
                f"| `{summary['variant']}` | {summary['rows']} | "
                f"{summary['source_families']} | {summary['platforms']} | "
                f"{summary['dates']} | {summary['cell025']} | "
                f"{summary['cell05']} | {summary['cell10']} |\n"
            )
        f.write("\n## Variant Details\n\n")
        for summary in summaries:
            f.write(f"### {summary['variant']}\n")
            f.write(f"- Path: `{summary['path']}`\n")
            f.write(f"- Description: {summary['description']}\n")
            f.write(f"- Top platforms: {summary['top_platforms']}\n")
            f.write(
                f"- Observed MLD range: {summary['obs_mld_min']:.3f}m "
                f"to {summary['obs_mld_max']:.3f}m\n\n"
            )
        f.write("## Interpretation\n")
        f.write(
            "- These datasets are not production model artifacts. They are controlled "
            "coverage experiments for grouped validation.\n"
        )
        f.write(
            "- Compare benchmark results against the all-source and Argo+WOD baselines "
            "before deciding whether ERDDAP should enter the main candidate mix.\n"
        )


def main() -> None:
    base = load_sources()
    summaries = []
    for variant in VARIANTS:
        balanced = cap_erddap(
            base,
            cell_degree=float(variant["erddap_cell_degree"]),
            cap=int(variant["erddap_cap"]),
        )
        out_path = BASE_DIR / f"training_data_balanced_rtofs_2024_2025_{variant['name']}.csv"
        balanced.to_csv(out_path, index=False)
        summaries.append(summarize(str(variant["name"]), str(variant["description"]), balanced, out_path))
    write_report(summaries)
    for summary in summaries:
        print(
            f"{summary['variant']}: rows={summary['rows']} "
            f"sources={summary['source_families']} half_degree_cells={summary['cell05']}"
        )
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
