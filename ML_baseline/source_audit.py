"""
Direct provider source audit for MLD training data.

This script intentionally avoids Aquaview.  It checks provider availability and,
when requested, can extract WOD profile counts inside the GoM bbox before those
sources are promoted into `data_builder.py` defaults.
"""
from __future__ import annotations

import argparse
import csv
import io
import logging
import ssl
import sys
import urllib.parse
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ML_baseline.wod_source import WOD_CACHE_DIR, WOD_S3_BASE, extract_wod_profiles

logger = logging.getLogger(__name__)

DEFAULT_BBOX = [-98.0, 18.0, -80.0, 31.0]
DEFAULT_YEARS = [2023, 2024]
DEFAULT_INSTRUMENTS = ["xbt", "gld", "ctd", "pfl", "mrb", "drb", "apb"]
DEFAULT_OUTPUT = Path(__file__).with_name("source_audit_results.csv")
DEFAULT_ERDDAP_SERVERS = [
    "https://gliders.ioos.us/erddap",
    "https://erddap.secoora.org/erddap",
    "https://erddap.gcoos.org/erddap",
]
DEFAULT_ARGO_INDEX_URL = "https://data-argo.ifremer.fr/ar_index_global_prof.txt"

ssl_ctx = ssl._create_unverified_context()


@dataclass
class SourceAuditRow:
    provider: str
    source_key: str
    year: int | str
    instrument: str
    url: str
    status: str
    remote_size_mb: float | str
    cached: bool
    gom_profiles: int | str
    usable_profiles: int | str
    notes: str


def _wod_url(year: int, instrument: str) -> str:
    return f"{WOD_S3_BASE}/{year}/wod_{instrument}_{year}.nc"


def _remote_size_mb(url: str, timeout_seconds: int = 30) -> tuple[str, float | str]:
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds, context=ssl_ctx) as resp:
            size = resp.headers.get("Content-Length")
            if size:
                return "available", round(int(size) / 1_000_000, 2)
            return "available", "unknown"
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return "missing", ""
        return f"http_{exc.code}", ""
    except Exception as exc:
        return "error", type(exc).__name__


def _fetch_text(url: str, timeout_seconds: int = 60) -> str:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout_seconds, context=ssl_ctx) as resp:
        return resp.read().decode("utf-8", errors="replace")


def audit_wod(
    years: list[int],
    instruments: list[str],
    bbox: list[float],
    count_profiles: bool,
) -> list[SourceAuditRow]:
    rows: list[SourceAuditRow] = []
    for year in years:
        for instrument in instruments:
            instrument = instrument.lower()
            url = _wod_url(year, instrument)
            local_path = WOD_CACHE_DIR / f"wod_{instrument}_{year}.nc"
            status, size_mb = _remote_size_mb(url)
            gom_profiles: int | str = ""
            usable_profiles: int | str = ""
            notes = ""

            if count_profiles:
                if status == "available" or local_path.exists():
                    try:
                        profiles = extract_wod_profiles(year, instrument, bbox)
                        usable_profiles = len(profiles)
                        gom_profiles = len(profiles)
                    except FileNotFoundError:
                        status = "missing"
                    except Exception as exc:
                        status = "count_error"
                        notes = f"{type(exc).__name__}: {exc}"
                else:
                    notes = "Skipped count because source is not available."

            rows.append(
                SourceAuditRow(
                    provider="NOAA_NCEI_WOD",
                    source_key=f"WOD_{instrument.upper()}_{year}",
                    year=year,
                    instrument=instrument,
                    url=url,
                    status=status,
                    remote_size_mb=size_mb,
                    cached=local_path.exists(),
                    gom_profiles=gom_profiles,
                    usable_profiles=usable_profiles,
                    notes=notes,
                )
            )
    return rows


def _erddap_search_url(server: str, search_for: str, items_per_page: int) -> str:
    query = urllib.parse.urlencode(
        {
            "page": 1,
            "itemsPerPage": items_per_page,
            "searchFor": search_for,
        }
    )
    return f"{server.rstrip('/')}/search/index.csv?{query}"


def _erddap_info_url(server: str, dataset_id: str) -> str:
    return f"{server.rstrip('/')}/info/{urllib.parse.quote(dataset_id)}/index.csv"


def _dataset_variables(server: str, dataset_id: str) -> tuple[set[str], str]:
    try:
        text = _fetch_text(_erddap_info_url(server, dataset_id))
    except Exception as exc:
        return set(), f"info_error={type(exc).__name__}"

    variables: set[str] = set()
    try:
        for row in csv.DictReader(io.StringIO(text)):
            variable = (row.get("Variable Name") or "").strip()
            row_type = (row.get("Row Type") or "").strip()
            if row_type == "variable" and variable:
                variables.add(variable.lower())
    except Exception as exc:
        return variables, f"info_parse_error={type(exc).__name__}"
    return variables, ""


def audit_erddap_gliders(
    servers: list[str],
    search_terms: list[str],
    bbox: list[float],
    items_per_page: int,
) -> list[SourceAuditRow]:
    rows: list[SourceAuditRow] = []
    seen: set[tuple[str, str]] = set()
    required_any_temp = ("temperature", "sea_water_temperature")
    required_any_depth = ("depth", "pressure", "pres")

    for server in servers:
        for search_for in search_terms:
            url = _erddap_search_url(server, search_for, items_per_page)
            try:
                text = _fetch_text(url)
                search_status = "available"
            except Exception as exc:
                rows.append(
                    SourceAuditRow(
                        provider="ERDDAP_GLIDER",
                        source_key=server,
                        year="",
                        instrument="glider",
                        url=url,
                        status="search_error",
                        remote_size_mb="",
                        cached=False,
                        gom_profiles="",
                        usable_profiles="",
                        notes=f"{type(exc).__name__}: {exc}",
                    )
                )
                continue

            for row in csv.DictReader(io.StringIO(text)):
                dataset_id = (row.get("Dataset ID") or "").strip()
                if not dataset_id:
                    continue
                key = (server, dataset_id)
                if key in seen:
                    continue
                seen.add(key)

                title = (row.get("Title") or "").strip()
                institution = (row.get("Institution") or "").strip()
                variables, info_note = _dataset_variables(server, dataset_id)
                has_temp = any(v in variables for v in required_any_temp) or any("temp" in v for v in variables)
                has_depth = any(v in variables for v in required_any_depth) or any("depth" in v or "pres" in v for v in variables)
                has_time = "time" in variables
                has_position = ("latitude" in variables or "lat" in variables) and ("longitude" in variables or "lon" in variables)
                candidate = has_temp and has_depth and has_time and has_position
                status = "profile_candidate" if candidate else "metadata_only"
                notes = "; ".join(
                    part
                    for part in [
                        f"search={search_for}",
                        f"search_status={search_status}",
                        f"title={title[:120]}",
                        f"institution={institution[:80]}",
                        f"variables={','.join(sorted(list(variables))[:30])}",
                        info_note,
                    ]
                    if part
                )

                rows.append(
                    SourceAuditRow(
                        provider="ERDDAP_GLIDER",
                        source_key=dataset_id,
                        year="",
                        instrument="glider",
                        url=f"{server.rstrip('/')}/tabledap/{urllib.parse.quote(dataset_id)}.html",
                        status=status,
                        remote_size_mb="",
                        cached=False,
                        gom_profiles="candidate" if candidate else "",
                        usable_profiles="",
                        notes=notes,
                    )
                )
    return rows


def audit_argo_index(
    index_url: str,
    bbox: list[float],
    start_yyyymmdd: str,
    end_yyyymmdd: str,
) -> list[SourceAuditRow]:
    west, south, east, north = bbox
    try:
        text = _fetch_text(index_url, timeout_seconds=120)
    except Exception as exc:
        return [
            SourceAuditRow(
                provider="ARGO_GDAC_INDEX",
                source_key="ar_index_global_prof",
                year=f"{start_yyyymmdd}-{end_yyyymmdd}",
                instrument="pfl",
                url=index_url,
                status="index_error",
                remote_size_mb="",
                cached=False,
                gom_profiles="",
                usable_profiles="",
                notes=f"{type(exc).__name__}: {exc}",
            )
        ]

    header: list[str] | None = None
    total_rows = 0
    gom_rows = 0
    dac_counts: dict[str, int] = {}
    sample_files: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if header is None:
            header = [v.strip() for v in line.split(",")]
            continue

        values = [v.strip() for v in line.split(",")]
        if len(values) < len(header):
            continue
        item = dict(zip(header, values))
        total_rows += 1
        try:
            lat = float(item.get("latitude", "nan"))
            lon = float(item.get("longitude", "nan"))
            date = item.get("date", "")[:8]
        except ValueError:
            continue

        if not (start_yyyymmdd <= date <= end_yyyymmdd):
            continue
        if not (south <= lat <= north and west <= lon <= east):
            continue

        gom_rows += 1
        file_name = item.get("file", "")
        dac = file_name.split("/", 1)[0] if "/" in file_name else "unknown"
        dac_counts[dac] = dac_counts.get(dac, 0) + 1
        if len(sample_files) < 10:
            sample_files.append(file_name)

    notes = f"total_index_rows={total_rows}; dac_counts={dac_counts}; sample_files={sample_files}"
    return [
        SourceAuditRow(
            provider="ARGO_GDAC_INDEX",
            source_key="ar_index_global_prof",
            year=f"{start_yyyymmdd}-{end_yyyymmdd}",
            instrument="pfl",
            url=index_url,
            status="available",
            remote_size_mb="",
            cached=False,
            gom_profiles=gom_rows,
            usable_profiles="not_counted_profile_index_only",
            notes=notes,
        )
    ]


def write_rows(path: Path, rows: list[SourceAuditRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(rows[0]).keys()) if rows else [])
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit direct in-situ source availability.")
    parser.add_argument("--years", default=",".join(str(y) for y in DEFAULT_YEARS))
    parser.add_argument("--instruments", default=",".join(DEFAULT_INSTRUMENTS))
    parser.add_argument("--bbox", default=",".join(str(v) for v in DEFAULT_BBOX))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--skip-wod", action="store_true")
    parser.add_argument("--audit-erddap-gliders", action="store_true")
    parser.add_argument("--erddap-servers", default=",".join(DEFAULT_ERDDAP_SERVERS))
    parser.add_argument("--erddap-search", default="Gulf of Mexico glider,GoM glider,glider temperature depth")
    parser.add_argument("--erddap-items-per-page", type=int, default=1000)
    parser.add_argument("--audit-argo-index", action="store_true")
    parser.add_argument("--argo-index-url", default=DEFAULT_ARGO_INDEX_URL)
    parser.add_argument("--argo-start", default="20230101")
    parser.add_argument("--argo-end", default="20241231")
    parser.add_argument(
        "--count-profiles",
        action="store_true",
        help="Download/cache WOD files and count usable GoM profiles. Without this, only HEAD availability is checked.",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args()
    years = [int(v) for v in args.years.split(",") if v.strip()]
    instruments = [v.strip().lower() for v in args.instruments.split(",") if v.strip()]
    bbox = [float(v) for v in args.bbox.split(",") if v.strip()]
    output = Path(args.output)
    rows: list[SourceAuditRow] = []

    if not args.skip_wod:
        logger.info(
            "Auditing direct WOD sources years=%s instruments=%s bbox=%s count_profiles=%s",
            years,
            instruments,
            bbox,
            args.count_profiles,
        )
        rows.extend(audit_wod(years, instruments, bbox, args.count_profiles))

    if args.audit_erddap_gliders:
        servers = [v.strip() for v in args.erddap_servers.split(",") if v.strip()]
        search_terms = [v.strip() for v in args.erddap_search.split(",") if v.strip()]
        logger.info("Auditing ERDDAP gliders servers=%s search_terms=%s", servers, search_terms)
        rows.extend(audit_erddap_gliders(servers, search_terms, bbox, args.erddap_items_per_page))

    if args.audit_argo_index:
        logger.info(
            "Auditing Argo GDAC index url=%s bbox=%s date=%s/%s",
            args.argo_index_url,
            bbox,
            args.argo_start,
            args.argo_end,
        )
        rows.extend(audit_argo_index(args.argo_index_url, bbox, args.argo_start, args.argo_end))

    write_rows(output, rows)
    logger.info("Wrote %d audit rows to %s", len(rows), output)

    for row in rows:
        logger.info(
            "%s status=%s size_mb=%s cached=%s usable_profiles=%s",
            row.source_key,
            row.status,
            row.remote_size_mb,
            row.cached,
            row.usable_profiles,
        )


if __name__ == "__main__":
    main()
