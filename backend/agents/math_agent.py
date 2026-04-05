"""
Agent 2 - Math Agent
Calculates a composite ranking score (0–1) for each employee
from their APR (jsonb) and PIP count (integer).

Ranking Formula (output: 0.0 to 1.0)
─────────────────────────────────────
APR values use 1.0 as the baseline:
  > 1.0  → above satisfactory (good)
  = 1.0  → exactly satisfactory
  < 1.0  → underperforming

1. APR Normalized (0–1):
   - Weighted average of yearly APR values (recent years weighted higher).
   - Divided by APR_MAX (2.0) to normalize into 0–1 range.
   - APR of 1.0 → 0.50, APR of 2.0 → 1.0, APR of 0.5 → 0.25

2. PIP Penalty (0–1):
   - pip_factor = 0.80 ^ pip
   - 0 PIPs = 1.0, 1 PIP = 0.80, 2 PIPs = 0.64, 3 PIPs = 0.512

3. Consistency Bonus:
   - Low variance in APR → up to +5% boost.

4. Final Ranking = clamp(apr_norm × pip_factor × consistency, 0, 1)

Verdicts:
   ≥ 0.50 → safe  (APR ≥ 1.0 with no PIPs maps to exactly 0.50)
   0.30–0.49 → at_risk
   < 0.30 → critical
"""

import logging
import math
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# --- tuning knobs -----------------------------------------------------------
PIP_PENALTY_BASE = 0.80          # 20% compounding penalty per PIP
CONSISTENCY_BONUS_MAX = 0.05     # max +5% for consistent performers
APR_MAX = 2.0                    # ceiling for normalization (APR 2.0 → 1.0)
# -----------------------------------------------------------------------------


def _weighted_avg(values: List[float]) -> float:
    """Linearly-weighted average (recent values weighted higher)."""
    n = len(values)
    weights = list(range(1, n + 1))          # [1, 2, ..., n]
    total = sum(v * w for v, w in zip(values, weights))
    return total / sum(weights)


def _variance(values: List[float]) -> float:
    """Population variance of a list of floats."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return sum((v - mean) ** 2 for v in values) / len(values)


def _extract_apr_values(apr_raw: Any) -> List[float]:
    """Extract float values from apr (jsonb dict or list)."""
    values: List[float] = []
    if isinstance(apr_raw, dict):
        # Sort by key (year) so most recent is last → gets highest weight
        for key in sorted(apr_raw.keys()):
            try:
                values.append(float(apr_raw[key]))
            except (ValueError, TypeError):
                pass
    elif isinstance(apr_raw, list):
        for v in apr_raw:
            try:
                values.append(float(v))
            except (ValueError, TypeError):
                pass
    return values


def compute_ranking(employee: Dict[str, Any]) -> Dict[str, Any]:
    """Compute ranking (0-1) for a single employee dict (mutates & returns it)."""
    apr_raw = employee.get("apr")
    pip = employee.get("pip", 0)

    # --- APR score (normalized 0-1) ------------------------------------------
    apr_values = _extract_apr_values(apr_raw)

    if not apr_values:
        apr_norm = 0.0
        raw_avg = 0.0
        employee["apr_valid"] = False
        logger.warning(
            "[MathAgent] %s has null/empty APR - score set to 0.", employee["name"]
        )
    else:
        raw_avg = _weighted_avg(apr_values)
        # Normalize: clamp to [0, APR_MAX] then scale to 0-1
        apr_norm = min(max(raw_avg, 0.0), APR_MAX) / APR_MAX
        employee["apr_valid"] = True

    # --- PIP penalty (0-1) ---------------------------------------------------
    pip_factor = math.pow(PIP_PENALTY_BASE, pip)

    # --- Consistency modifier ------------------------------------------------
    var = _variance(apr_values) if apr_values else 0.0
    if var < 0.1 and apr_values:
        consistency = 1.0 + CONSISTENCY_BONUS_MAX * (1.0 - var / 0.1)
    else:
        consistency = 1.0

    # --- composite (clamped 0-1) ---------------------------------------------
    ranking = round(min(1.0, max(0.0, apr_norm * pip_factor * consistency)), 4)

    employee["ranking"] = ranking
    employee["_math_details"] = {
        "apr_norm": round(apr_norm, 4),
        "apr_raw_avg": round(raw_avg, 4),
        "apr_values": apr_values,
        "pip_count": pip,
        "pip_factor": round(pip_factor, 4),
        "consistency": round(consistency, 4),
        "variance": round(var, 4),
        "verdict": (
            "safe" if ranking >= 0.50
            else "at_risk" if ranking >= 0.30
            else "critical"
        ),
    }
    return employee


def run(employees: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run the math agent on every employee. Returns the enriched list."""
    logger.info("[MathAgent] Computing rankings for %d employees...", len(employees))

    for emp in employees:
        compute_ranking(emp)

    # sort descending by ranking for convenience
    employees.sort(key=lambda e: e["ranking"], reverse=True)

    logger.info("[MathAgent] Rankings computed. Top: %s (%.4f)",
                employees[0]["name"] if employees else "N/A",
                employees[0]["ranking"] if employees else 0)
    return employees
