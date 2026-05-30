"""
AMS Intelligence — NHSN Data Client

CDC National Healthcare Safety Network antimicrobial use / resistance data.

Place downloaded NHSN CSV files in data/nhsn/:
  - AU_FacilityWideInpatient_*.csv  (Antimicrobial Use — Days of Therapy)
  - AR_*.csv                         (Antimicrobial Resistance)

Data portal: https://www.cdc.gov/nhsn/datastat/index.html
Download requires facility enrollment; national aggregate data is public.

Falls back to realistic demo data when no files are present.
"""

from __future__ import annotations
import random
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from config import DATA_DIR

NHSN_DIR = DATA_DIR / "nhsn"

# Days of Therapy per 1000 patient-days — national benchmarks (approximate)
NATIONAL_BENCHMARKS: dict[str, float] = {
    "fluoroquinolones":    85.0,
    "carbapenems":         30.0,
    "cephalosporins_3g":  110.0,
    "cephalosporins_1g":   95.0,
    "vancomycin":          70.0,
    "piperacillin_tazo":   90.0,
    "azithromycin":       105.0,
    "doxycycline":         45.0,
    "trimethoprim_sulfa":  55.0,
    "metronidazole":       60.0,
}


@dataclass
class NHSNRecord:
    year: int
    quarter: int          # 1–4
    drug_class: str
    dot_per_1000: float   # Days of Therapy / 1000 patient-days
    facility_type: str    # "ICU" / "Ward" / "All"
    source: str           # "file" or "demo"


def _demo_dot_series(drug_class: str, start_year: int = 2018, end_year: int = 2024) -> list[NHSNRecord]:
    """Generate realistic DOT trend data with COVID-era perturbations."""
    baseline = NATIONAL_BENCHMARKS.get(drug_class, 60.0)
    records: list[NHSNRecord] = []
    rng = random.Random(hash(drug_class) % 2**31)

    for year in range(start_year, end_year + 1):
        for q in range(1, 5):
            # COVID-era spike in carbapenems/azithromycin 2020-2021
            covid_bump = 0.0
            if drug_class in ("carbapenems", "azithromycin") and year in (2020, 2021):
                covid_bump = baseline * 0.25
            # Fluoroquinolone restriction trend (downward since 2016 FDA warnings)
            fq_trend = 0.0
            if drug_class == "fluoroquinolones":
                fq_trend = -baseline * 0.03 * (year - 2018)

            val = baseline + covid_bump + fq_trend + rng.gauss(0, baseline * 0.05)
            records.append(NHSNRecord(
                year=year, quarter=q, drug_class=drug_class,
                dot_per_1000=max(0.0, round(val, 1)),
                facility_type="All", source="demo",
            ))
    return records


def load_nhsn_data(drug_class: str, start_year: int = 2018, end_year: int = 2024) -> list[NHSNRecord]:
    """Load NHSN AU data for a drug class. Falls back to demo if no files found."""
    csv_files = sorted(NHSN_DIR.glob("AU_FacilityWideInpatient_*.csv"))
    if not csv_files:
        return _demo_dot_series(drug_class, start_year, end_year)

    records: list[NHSNRecord] = []
    for f in csv_files:
        try:
            df = pd.read_csv(f, low_memory=False)
            # Normalize column names
            df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

            # Look for drug class rows (NHSN uses antibiotic category codes)
            class_col = next((c for c in df.columns if "antibiotic" in c or "drug" in c), None)
            dot_col   = next((c for c in df.columns if "dot" in c), None)
            year_col  = next((c for c in df.columns if "year" in c), None)
            qtr_col   = next((c for c in df.columns if "quarter" in c or "qtr" in c), None)

            if not all([class_col, dot_col, year_col]):
                continue

            mask = df[class_col].str.lower().str.contains(drug_class.lower(), na=False)
            for _, row in df[mask].iterrows():
                try:
                    records.append(NHSNRecord(
                        year=int(row[year_col]),
                        quarter=int(row[qtr_col]) if qtr_col else 0,
                        drug_class=drug_class,
                        dot_per_1000=float(row[dot_col]),
                        facility_type=str(row.get("facility_type", "All")),
                        source="file",
                    ))
                except (ValueError, KeyError):
                    continue
        except Exception:
            continue

    if not records:
        return _demo_dot_series(drug_class, start_year, end_year)

    return [r for r in records if start_year <= r.year <= end_year]


def get_national_benchmark(drug_class: str) -> float:
    return NATIONAL_BENCHMARKS.get(drug_class, 60.0)
