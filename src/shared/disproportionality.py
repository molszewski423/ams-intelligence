"""
AMS Intelligence — Disproportionality Statistics

PRR (Proportional Reporting Ratio) and ROR (Reporting Odds Ratio) with
95% confidence intervals and chi-squared test for signal detection.

Evans criteria: PRR ≥ 2.0 AND N ≥ 3 AND chi² ≥ 4.0 (all required).
"""

from __future__ import annotations
import math
from collections import Counter
from dataclasses import dataclass


@dataclass
class SignalResult:
    reaction_pt: str
    drug_cases: int
    bg_cases: int
    prr: float
    prr_ci_lo: float
    prr_ci_hi: float
    ror: float
    ror_ci_lo: float
    ror_ci_hi: float
    chi2: float
    signal: bool
    continuity_corrected: bool = False
    signal_strength: str = ""   # "strong" / "moderate" / "threshold" / "none"


def _chi2_yates(a: float, b: float, c: float, d: float) -> float:
    n = a + b + c + d
    if n == 0:
        return 0.0
    num   = n * (abs(a * d - b * c) - n / 2) ** 2
    denom = (a + b) * (c + d) * (a + c) * (b + d)
    return num / denom if denom > 0 else 0.0


def _prr_with_ci(a: float, b: float, c: float, d: float) -> tuple[float, float, float]:
    if a == 0 or (a + c) == 0 or (b + d) == 0 or b == 0:
        return 0.0, 0.0, float("inf")
    prr = (a / (a + c)) / (b / (b + d))
    se  = math.sqrt(1/a - 1/(a + c) + 1/b - 1/(b + d))
    return prr, prr * math.exp(-1.96 * se), prr * math.exp(1.96 * se)


def _ror_with_ci(a: float, b: float, c: float, d: float) -> tuple[float, float, float]:
    if b == 0 or c == 0:
        return 0.0, 0.0, float("inf")
    ror = (a * d) / (b * c)
    if a == 0:
        return ror, 0.0, float("inf")
    se  = math.sqrt(1/a + 1/b + 1/c + 1/d)
    return ror, ror * math.exp(-1.96 * se), ror * math.exp(1.96 * se)


def _strength(prr: float, n: int) -> str:
    if prr >= 5.0 and n >= 10:
        return "strong"
    if prr >= 3.0 and n >= 5:
        return "moderate"
    if prr >= 2.0 and n >= 3:
        return "threshold"
    return "none"


def compute_signals(
    drug_reactions: Counter,
    drug_total: int,
    bg_reactions: Counter,
    bg_total: int,
    min_drug_cases: int = 1,
) -> list[SignalResult]:
    """
    Compute PRR, ROR, chi² for every reaction PT seen in drug or background.

    Contingency table per PT:
              Drug    Background
    PT          a         b
    Other       c         d
    """
    all_pts = set(drug_reactions.keys()) | set(bg_reactions.keys())
    results: list[SignalResult] = []

    for pt in all_pts:
        a = float(drug_reactions.get(pt, 0))
        b = float(bg_reactions.get(pt, 0))
        if a < min_drug_cases:
            continue

        c = max(0.5, float(drug_total) - a)
        d = float(bg_total) - b
        corrected = False

        if b == 0:
            b, d = 0.5, d + 0.5
            corrected = True
        if d <= 0:
            d = 0.5

        prr, prr_lo, prr_hi = _prr_with_ci(a, b, c, d)
        ror, ror_lo, ror_hi = _ror_with_ci(a, b, c, d)
        chi2 = _chi2_yates(a, b, c, d)

        results.append(SignalResult(
            reaction_pt=pt,
            drug_cases=int(a),
            bg_cases=int(drug_reactions.get(pt, 0) + bg_reactions.get(pt, 0)),
            prr=round(prr, 3),
            prr_ci_lo=round(prr_lo, 3),
            prr_ci_hi=round(prr_hi, 3),
            ror=round(ror, 3),
            ror_ci_lo=round(ror_lo, 3),
            ror_ci_hi=round(ror_hi, 3),
            chi2=round(chi2, 2),
            signal=(prr >= 2.0 and int(a) >= 3 and chi2 >= 4.0),
            continuity_corrected=corrected,
            signal_strength=_strength(prr, int(a)),
        ))

    results.sort(key=lambda r: r.prr, reverse=True)
    return results


def temporal_compare(
    pre_signals: list[SignalResult],
    post_signals: list[SignalResult],
) -> list[dict]:
    """
    Compare PRR between two time periods for each reaction PT.
    Returns list of {pt, pre_prr, post_prr, delta, direction}.
    """
    pre_map  = {s.reaction_pt: s for s in pre_signals}
    post_map = {s.reaction_pt: s for s in post_signals}
    all_pts  = set(pre_map) | set(post_map)
    rows = []
    for pt in all_pts:
        pre_prr  = pre_map[pt].prr  if pt in pre_map  else 0.0
        post_prr = post_map[pt].prr if pt in post_map else 0.0
        delta    = post_prr - pre_prr
        rows.append({
            "reaction_pt":   pt,
            "pre_prr":       pre_prr,
            "post_prr":      post_prr,
            "delta":         round(delta, 3),
            "direction":     "↑ Increased" if delta > 0.2 else ("↓ Decreased" if delta < -0.2 else "→ Stable"),
            "pre_signal":    pt in pre_map and pre_map[pt].signal,
            "post_signal":   pt in post_map and post_map[pt].signal,
        })
    rows.sort(key=lambda r: abs(r["delta"]), reverse=True)
    return rows
