"""
AMS Intelligence — ATLAS Data Client

Pfizer ATLAS (Antimicrobial Testing Leadership and Surveillance) dataset.
Global in vitro susceptibility data for key pathogens.

Dataset: https://www.pfizer.com/science/clinical-trials/atlas-dataset
Download the public CSV and place in data/atlas/atlas_antibiotics.csv

Falls back to demo data when file is absent.
"""

from __future__ import annotations
import random
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from config import DATA_DIR

ATLAS_DIR  = DATA_DIR / "atlas"
ATLAS_FILE = ATLAS_DIR / "atlas_antibiotics.csv"


@dataclass
class ATLASRecord:
    year: int
    species: str
    antibiotic: str
    country: str
    region: str
    mic_50: float | None   # MIC50 (µg/mL)
    mic_90: float | None   # MIC90 (µg/mL)
    pct_susceptible: float
    n_isolates: int
    source: str


# Demo MIC distributions based on published ATLAS summaries
_DEMO_MIC_DATA: dict[tuple[str, str], dict] = {
    ("Escherichia coli",       "cefazolin"):     {"mic50": 4.0,   "mic90": 32.0,   "pct_s": 0.78},
    ("Escherichia coli",       "cefepime"):      {"mic50": 0.06,  "mic90": 0.25,   "pct_s": 0.92},
    ("Klebsiella pneumoniae",  "cefazolin"):     {"mic50": 8.0,   "mic90": 64.0,   "pct_s": 0.68},
    ("Klebsiella pneumoniae",  "meropenem"):     {"mic50": 0.06,  "mic90": 0.25,   "pct_s": 0.94},
    ("Staphylococcus aureus",  "cefazolin"):     {"mic50": 0.5,   "mic90": 1.0,    "pct_s": 0.97},
    ("Staphylococcus aureus",  "vancomycin"):    {"mic50": 1.0,   "mic90": 2.0,    "pct_s": 0.999},
    ("Pseudomonas aeruginosa", "ceftazidime"):   {"mic50": 2.0,   "mic90": 32.0,   "pct_s": 0.78},
    ("Pseudomonas aeruginosa", "meropenem"):     {"mic50": 1.0,   "mic90": 16.0,   "pct_s": 0.82},
    ("Acinetobacter baumannii","colistin"):      {"mic50": 0.5,   "mic90": 2.0,    "pct_s": 0.88},
    ("Enterococcus faecium",   "linezolid"):     {"mic50": 2.0,   "mic90": 4.0,    "pct_s": 0.99},
}


def _demo_atlas(species: str, antibiotic: str, start_year: int, end_year: int) -> list[ATLASRecord]:
    key  = (species, antibiotic)
    base = _DEMO_MIC_DATA.get(key, {"mic50": 4.0, "mic90": 16.0, "pct_s": 0.80})
    rng  = random.Random(hash(key) % 2**31)
    recs = []
    for year in range(start_year, end_year + 1):
        # MIC creep: slight annual increase
        mic_drift = 1.02 ** (year - start_year)
        n         = rng.randint(200, 1200)
        recs.append(ATLASRecord(
            year=year, species=species, antibiotic=antibiotic,
            country="Global (Demo)", region="Global",
            mic_50=round(base["mic50"] * mic_drift * rng.uniform(0.9, 1.1), 3),
            mic_90=round(base["mic90"] * mic_drift * rng.uniform(0.9, 1.1), 3),
            pct_susceptible=round(max(0, base["pct_s"] - 0.005 * (year - start_year) + rng.gauss(0, 0.01)), 3),
            n_isolates=n, source="demo",
        ))
    return recs


def load_atlas_data(
    species: str,
    antibiotic: str,
    start_year: int = 2015,
    end_year: int = 2023,
) -> list[ATLASRecord]:
    """Load ATLAS susceptibility data. Falls back to demo if file absent."""
    if not ATLAS_FILE.exists():
        return _demo_atlas(species, antibiotic, start_year, end_year)

    records: list[ATLASRecord] = []
    try:
        df = pd.read_csv(ATLAS_FILE, low_memory=False)
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        sp_col  = next((c for c in df.columns if "species" in c or "organism" in c), None)
        abx_col = next((c for c in df.columns if "antibiotic" in c or "drug" in c), None)
        yr_col  = next((c for c in df.columns if "year" in c), None)
        s_col   = next((c for c in df.columns if "susceptible" in c or "%s" in c), None)
        mic50   = next((c for c in df.columns if "mic50" in c or "mic_50" in c), None)
        mic90   = next((c for c in df.columns if "mic90" in c or "mic_90" in c), None)

        if not all([sp_col, abx_col, yr_col]):
            return _demo_atlas(species, antibiotic, start_year, end_year)

        mask = (
            df[sp_col].str.lower().str.contains(species.lower(), na=False) &
            df[abx_col].str.lower().str.contains(antibiotic.lower(), na=False)
        )
        for _, row in df[mask].iterrows():
            yr = int(row[yr_col])
            if not (start_year <= yr <= end_year):
                continue
            records.append(ATLASRecord(
                year=yr, species=species, antibiotic=antibiotic,
                country=str(row.get("country", "Unknown")),
                region=str(row.get("region", "Unknown")),
                mic_50=float(row[mic50]) if mic50 else None,
                mic_90=float(row[mic90]) if mic90 else None,
                pct_susceptible=float(row[s_col]) / 100.0 if s_col else 0.0,
                n_isolates=int(row.get("n", row.get("total", 0))),
                source="file",
            ))
    except Exception:
        return _demo_atlas(species, antibiotic, start_year, end_year)

    return records or _demo_atlas(species, antibiotic, start_year, end_year)
