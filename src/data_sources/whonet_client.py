"""
AMS Intelligence — WHONET Data Client

WHO global antimicrobial resistance surveillance data.

WHONET is a free WHO software for AMR data management. Export files as CSV
and place in data/whonet/. Files typically named: WHONET_EXPORT_*.csv

Download: https://whonet.org/data.html (country-level public datasets)

Falls back to demo data when no files present.
"""

from __future__ import annotations
import random
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from config import DATA_DIR

WHONET_DIR = DATA_DIR / "whonet"

# Common organism / antibiotic combinations tracked in AMS
KEY_ORG_ABX: list[tuple[str, str]] = [
    ("Escherichia coli",          "cefazolin"),
    ("Escherichia coli",          "cefpodoxime"),
    ("Klebsiella pneumoniae",     "cefazolin"),
    ("Klebsiella pneumoniae",     "carbapenems"),
    ("Staphylococcus aureus",     "cefazolin"),
    ("Staphylococcus aureus",     "vancomycin"),
    ("Enterococcus faecium",      "vancomycin"),
    ("Pseudomonas aeruginosa",    "cefazolin"),
    ("Pseudomonas aeruginosa",    "carbapenems"),
    ("Acinetobacter baumannii",   "carbapenems"),
]


@dataclass
class WHONETRecord:
    organism: str
    antibiotic: str
    year: int
    country: str
    pct_resistant: float   # % of isolates resistant
    pct_intermediate: float
    pct_susceptible: float
    n_isolates: int
    source: str            # "file" or "demo"


# Approximate resistance rates for demo data (based on published surveillance)
_DEMO_BASE_RATES: dict[tuple[str, str], float] = {
    ("Escherichia coli",       "cefazolin"):    0.18,
    ("Escherichia coli",       "cefpodoxime"):  0.14,
    ("Klebsiella pneumoniae",  "cefazolin"):    0.28,
    ("Klebsiella pneumoniae",  "carbapenems"):  0.08,
    ("Staphylococcus aureus",  "cefazolin"):    0.03,   # MSSA
    ("Staphylococcus aureus",  "vancomycin"):   0.001,
    ("Enterococcus faecium",   "vancomycin"):   0.32,   # VRE
    ("Pseudomonas aeruginosa", "cefazolin"):    0.85,   # intrinsically resistant
    ("Pseudomonas aeruginosa", "carbapenems"):  0.22,
    ("Acinetobacter baumannii","carbapenems"):  0.45,
}


def _demo_whonet(organism: str, antibiotic: str, start_year: int, end_year: int) -> list[WHONETRecord]:
    key  = (organism, antibiotic)
    base = _DEMO_BASE_RATES.get(key, 0.15)
    rng  = random.Random(hash(key) % 2**31)
    recs = []
    for year in range(start_year, end_year + 1):
        trend = 0.005 * (year - start_year)   # slight annual increase
        r     = min(1.0, max(0.0, base + trend + rng.gauss(0, 0.015)))
        i     = rng.uniform(0.03, 0.08)
        s     = max(0.0, 1.0 - r - i)
        n     = rng.randint(80, 600)
        recs.append(WHONETRecord(
            organism=organism, antibiotic=antibiotic, year=year,
            country="USA (Demo)", pct_resistant=round(r, 3),
            pct_intermediate=round(i, 3), pct_susceptible=round(s, 3),
            n_isolates=n, source="demo",
        ))
    return recs


def load_whonet_data(
    organism: str,
    antibiotic: str,
    start_year: int = 2018,
    end_year: int = 2024,
) -> list[WHONETRecord]:
    """Load WHONET resistance data. Falls back to demo if no files found."""
    csv_files = sorted(WHONET_DIR.glob("*.csv"))
    if not csv_files:
        return _demo_whonet(organism, antibiotic, start_year, end_year)

    records: list[WHONETRecord] = []
    for f in csv_files:
        try:
            df = pd.read_csv(f, low_memory=False)
            df.columns = [c.strip().lower() for c in df.columns]

            org_col  = next((c for c in df.columns if "organism" in c or "species" in c), None)
            abx_col  = next((c for c in df.columns if "antibiotic" in c or "drug" in c), None)
            yr_col   = next((c for c in df.columns if "year" in c), None)
            r_col    = next((c for c in df.columns if "%r" in c or "resistant" in c), None)

            if not all([org_col, abx_col, yr_col, r_col]):
                continue

            mask = (
                df[org_col].str.lower().str.contains(organism.lower(), na=False) &
                df[abx_col].str.lower().str.contains(antibiotic.lower(), na=False)
            )
            for _, row in df[mask].iterrows():
                try:
                    yr = int(row[yr_col])
                    if not (start_year <= yr <= end_year):
                        continue
                    records.append(WHONETRecord(
                        organism=organism, antibiotic=antibiotic, year=yr,
                        country=str(row.get("country", "Unknown")),
                        pct_resistant=float(row[r_col]) / 100.0,
                        pct_intermediate=float(row.get("%i", 0)) / 100.0,
                        pct_susceptible=float(row.get("%s", 0)) / 100.0,
                        n_isolates=int(row.get("n", 0)),
                        source="file",
                    ))
                except (ValueError, KeyError):
                    continue
        except Exception:
            continue

    if not records:
        return _demo_whonet(organism, antibiotic, start_year, end_year)
    return records


def resistance_trend_summary(records: list[WHONETRecord]) -> dict:
    """Compute min/max/mean %R and annualized trend slope."""
    if not records:
        return {}
    rates = [r.pct_resistant for r in records]
    years = [r.year for r in records]
    import statistics
    mean_r = statistics.mean(rates)
    # Simple linear trend
    if len(set(years)) > 1:
        n  = len(years)
        xm = sum(years) / n
        ym = mean_r
        slope = sum((x - xm) * (y - ym) for x, y in zip(years, rates)) / \
                sum((x - xm) ** 2 for x in years)
    else:
        slope = 0.0
    return {
        "mean_pct_resistant": round(mean_r * 100, 1),
        "min_pct_resistant":  round(min(rates) * 100, 1),
        "max_pct_resistant":  round(max(rates) * 100, 1),
        "annual_trend_pct":   round(slope * 100, 2),
        "n_records":          len(records),
    }
