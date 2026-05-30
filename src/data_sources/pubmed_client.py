"""
AMS Intelligence — PubMed / NCBI E-utilities client

Queries PubMed for antimicrobial stewardship literature and retrieves
structured abstracts for use in analysis context and vault ingestion.

All endpoints are free (NCBI E-utilities public API, no key required for
moderate use; set NCBI_API_KEY in config for higher rate limits).
"""

from __future__ import annotations
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from config import NCBI_API_KEY  # "" if not set — still works, lower rate limit


EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
_DELAY = 0.34 if not NCBI_API_KEY else 0.11   # NCBI rate: 3/s without key, 10/s with


@dataclass
class PubMedArticle:
    pmid: str
    title: str
    abstract: str
    authors: str
    journal: str
    year: str
    keywords: list[str]
    mesh_terms: list[str]

    def as_text(self) -> str:
        """Full-text representation for embedding."""
        parts = [
            f"Title: {self.title}",
            f"Journal: {self.journal} ({self.year})",
            f"Authors: {self.authors}",
        ]
        if self.keywords:
            parts.append(f"Keywords: {', '.join(self.keywords)}")
        if self.mesh_terms:
            parts.append(f"MeSH: {', '.join(self.mesh_terms[:10])}")
        if self.abstract:
            parts.append(f"\nAbstract:\n{self.abstract}")
        return "\n".join(parts)

    def short_ref(self) -> str:
        return f"{self.authors.split(',')[0] if self.authors else 'Unknown'} et al. {self.journal} {self.year} (PMID {self.pmid})"


def _get(url: str) -> str:
    with urllib.request.urlopen(url, timeout=15) as r:
        return r.read().decode("utf-8")


def search_pmids(query: str, max_results: int = 50, min_year: int = 2015) -> list[str]:
    """Return list of PMIDs matching query."""
    params = {
        "db": "pubmed",
        "term": f"({query}) AND {min_year}:3000[pdat]",
        "retmax": str(max_results),
        "retmode": "json",
        "sort": "relevance",
    }
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY
    url = f"{EUTILS_BASE}/esearch.fcgi?{urllib.parse.urlencode(params)}"
    import json
    data = json.loads(_get(url))
    return data.get("esearchresult", {}).get("idlist", [])


def fetch_articles(pmids: list[str]) -> list[PubMedArticle]:
    """Fetch full article records for a list of PMIDs."""
    if not pmids:
        return []
    articles = []
    # Fetch in batches of 20
    for i in range(0, len(pmids), 20):
        batch = pmids[i:i + 20]
        params = {
            "db": "pubmed",
            "id": ",".join(batch),
            "retmode": "xml",
            "rettype": "abstract",
        }
        if NCBI_API_KEY:
            params["api_key"] = NCBI_API_KEY
        url = f"{EUTILS_BASE}/efetch.fcgi?{urllib.parse.urlencode(params)}"
        try:
            xml_text = _get(url)
            root = ET.fromstring(xml_text)
            for article_el in root.findall(".//PubmedArticle"):
                articles.append(_parse_article(article_el))
        except Exception:
            pass
        time.sleep(_DELAY)
    return articles


def _parse_article(el: ET.Element) -> PubMedArticle:
    def txt(path: str) -> str:
        node = el.find(path)
        return "".join(node.itertext()).strip() if node is not None else ""

    pmid = txt(".//PMID")
    title = txt(".//ArticleTitle")

    # Abstract — handle structured abstracts (multiple AbstractText sections)
    abs_parts = []
    for ab in el.findall(".//AbstractText"):
        label = ab.get("Label", "")
        text  = "".join(ab.itertext()).strip()
        if label:
            abs_parts.append(f"{label}: {text}")
        else:
            abs_parts.append(text)
    abstract = " ".join(abs_parts)

    # Authors
    author_els = el.findall(".//Author")
    names = []
    for a in author_els[:5]:
        ln = txt_el(a, "LastName")
        ini = txt_el(a, "Initials")
        if ln:
            names.append(f"{ln} {ini}".strip())
    authors = ", ".join(names) + (" et al." if len(author_els) > 5 else "")

    journal = txt(".//Journal/Title") or txt(".//ISOAbbreviation")
    year    = txt(".//PubDate/Year") or txt(".//PubDate/MedlineDate")[:4]

    keywords = [
        "".join(k.itertext()).strip()
        for k in el.findall(".//KeywordList/Keyword")
    ]
    mesh_terms = [
        "".join(m.findall("DescriptorName")[0].itertext()).strip()
        for m in el.findall(".//MeshHeadingList/MeshHeading")
        if m.findall("DescriptorName")
    ]

    return PubMedArticle(
        pmid=pmid, title=title, abstract=abstract,
        authors=authors, journal=journal, year=year,
        keywords=keywords, mesh_terms=mesh_terms,
    )


def txt_el(el: ET.Element, tag: str) -> str:
    node = el.find(tag)
    return "".join(node.itertext()).strip() if node is not None else ""


# ── Curated AMS query set ────────────────────────────────────────────────────

AMS_QUERIES = [
    # Core AMS
    ('"antimicrobial stewardship"[MeSH] AND (program OR intervention OR implementation)', "AMS Programs"),
    ('"antibiotic stewardship" AND (ASHP OR IDSA OR SIDP OR "core elements")', "ASHP/IDSA Guidelines"),
    # FAERS / pharmacovigilance
    ('"pharmacovigilance" AND "antimicrobial" AND (signal OR disproportionality OR PRR OR ROR)', "PV Signals"),
    # Resistance
    ('"antimicrobial resistance"[MeSH] AND (trend OR surveillance OR "drug resistance")', "Resistance Trends"),
    # Drug-specific AMS
    ('"fluoroquinolone" AND stewardship AND (restriction OR guideline OR outcome)', "FQ Stewardship"),
    ('"carbapenem" AND stewardship AND (resistance OR restriction OR "KPC" OR NDM)', "Carbapenem Stewardship"),
    ('"vancomycin" AND stewardship AND (AUC OR monitoring OR MRSA OR nephrotoxicity)', "Vancomycin Stewardship"),
    ('"cephalosporin" AND stewardship AND (formulary OR restriction OR outcome)', "Cephalosporin Stewardship"),
    # C. diff
    ('"Clostridioides difficile" AND (antibiotic OR stewardship OR risk)', "C. difficile"),
    # Utilization metrics
    ('"days of therapy" AND (DOT OR DDD OR benchmark OR NHSN)', "Utilization Metrics"),
    # ICU AMS
    ('"intensive care" AND "antimicrobial stewardship" AND (de-escalation OR outcome)', "ICU Stewardship"),
    # PK/PD
    ('"pharmacokinetics" AND "antimicrobial" AND (dosing OR optimization OR MIC)', "PK/PD Optimization"),
]


def fetch_ams_literature(max_per_query: int = 30, min_year: int = 2018) -> list[PubMedArticle]:
    """Fetch AMS literature across all curated query categories."""
    all_pmids: list[str] = []
    seen: set[str] = set()
    for query, label in AMS_QUERIES:
        try:
            pmids = search_pmids(query, max_results=max_per_query, min_year=min_year)
            new = [p for p in pmids if p not in seen]
            seen.update(new)
            all_pmids.extend(new)
            print(f"  {label}: {len(new)} articles")
            time.sleep(_DELAY)
        except Exception as e:
            print(f"  {label}: query failed — {e}")
    print(f"Fetching {len(all_pmids)} unique articles...")
    return fetch_articles(all_pmids)
