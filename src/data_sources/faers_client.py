"""
AMS Intelligence — FAERS Data Client

Fetches FDA Adverse Event Reporting System data for antimicrobial agents.
Supports aggregate reaction counts (fast, single API call) and temporal
year-by-year breakdowns for trend analysis.
"""

from __future__ import annotations
import json
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import date

from config import FAERS_API_URL, FAERS_API_KEY, FAERS_START_YEAR

# Reactions to exclude (FAERS data artifacts)
EXCLUDE_REACTIONS = {"no adverse event", "off label use", "drug use for unknown indication"}

# AMS-relevant reaction groupings
AMS_REACTION_GROUPS = {
    "Treatment Failure": [
        "therapeutic failure", "drug ineffective", "treatment failure",
        "clinical failure", "bacterial infection worsened",
    ],
    "C. difficile": [
        "clostridium difficile infection", "pseudomembranous colitis",
        "clostridium difficile colitis",
    ],
    "Allergy / Hypersensitivity": [
        "anaphylaxis", "drug hypersensitivity", "anaphylactic reaction",
        "urticaria", "rash", "angioedema",
    ],
    "Nephrotoxicity": [
        "acute kidney injury", "renal failure", "renal impairment",
        "blood creatinine increased", "nephrotoxicity",
    ],
    "Resistance": [
        "drug resistance", "multidrug resistance", "antibiotic resistance",
        "treatment emergent infection",
    ],
    "Mortality": [
        "death", "sudden death", "cardiac arrest",
    ],
}


def _date_filter(start_year: int, end_year: int | None) -> str:
    s = f"{start_year}0101"
    e = f"{end_year or date.today().year}1231"
    return f"receivedate:[{s}+TO+{e}]"


def _search_param(drug_name: str, start_year: int, end_year: int | None) -> str:
    term = drug_name.lower().replace(" ", "+")
    df   = _date_filter(start_year, end_year)
    return f'patient.drug.medicinalproduct:"{term}"+AND+{df}'


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "ams-intelligence/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {}
        raise


def fetch_reaction_counts(
    drug_name: str,
    start_year: int = FAERS_START_YEAR,
    end_year: int | None = None,
    limit: int = 200,
) -> Counter:
    """Aggregate reaction PT counts for a drug — single fast API call."""
    search = _search_param(drug_name, start_year, end_year)
    key_part = f"&api_key={FAERS_API_KEY}" if FAERS_API_KEY else ""
    url = f"{FAERS_API_URL}?search={search}&count=patient.reaction.reactionmeddrapt.exact&limit={limit}{key_part}"

    data = _get(url)
    counts: Counter = Counter()
    for item in data.get("results", []):
        term = item.get("term", "").lower().strip()
        if term and term not in EXCLUDE_REACTIONS:
            counts[term] = item.get("count", 0)
    return counts


def fetch_total_reports(
    drug_name: str,
    start_year: int = FAERS_START_YEAR,
    end_year: int | None = None,
) -> int:
    """Total FAERS report count for a drug in the date range."""
    search   = _search_param(drug_name, start_year, end_year)
    key_part = f"&api_key={FAERS_API_KEY}" if FAERS_API_KEY else ""
    url      = f"{FAERS_API_URL}?search={search}&limit=1{key_part}"
    data     = _get(url)
    return data.get("meta", {}).get("results", {}).get("total", 0)


def fetch_yearly_counts(
    drug_name: str,
    reactions_of_interest: list[str],
    start_year: int = 2015,
    end_year: int | None = None,
) -> dict[int, dict[str, int]]:
    """Year-by-year reaction counts for temporal trend analysis."""
    end = end_year or date.today().year
    yearly: dict[int, dict[str, int]] = {}
    for year in range(start_year, end + 1):
        counts = fetch_reaction_counts(drug_name, start_year=year, end_year=year)
        yearly[year] = {r: counts.get(r.lower(), 0) for r in reactions_of_interest}
        time.sleep(0.3)
    return yearly


def categorize_reactions(counts: Counter) -> dict[str, int]:
    """Map raw FAERS PTs → AMS reaction category totals."""
    totals: dict[str, int] = {cat: 0 for cat in AMS_REACTION_GROUPS}
    for pt, n in counts.items():
        for cat, terms in AMS_REACTION_GROUPS.items():
            if any(t in pt for t in terms):
                totals[cat] += n
                break
    return totals
