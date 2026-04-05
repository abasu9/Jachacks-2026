"""
Orchestrator
Runs the 4-agent pipeline per-user sequentially:

For each employee:
  1. (Data already fetched in bulk by data_agent)
  2. Math Agent   → compute ranking (0-1)
  3. GitHub Agent → collect GitHub data, AI score, calculate ROI
  4. Update Agent → persist ranking + roi to DB (waits for success)

Only moves to the next employee after the DB write succeeds.
"""

import logging
import time
from typing import Any, Dict, List

from agents import data_agent, math_agent, github_agent, update_agent

logger = logging.getLogger(__name__)


def run_pipeline() -> Dict[str, Any]:
    """Execute the full agentic pipeline and return a result summary."""
    t0 = time.time()
    results: Dict[str, Any] = {
        "status": "running",
        "total": 0,
        "processed": 0,
        "failed": 0,
        "skipped": 0,
        "employees": [],
    }

    # ── Step 1: Bulk data collection ─────────────────────────────────────
    logger.info("═══ Step 1: Data Agent — fetching all employees ═══")
    employees = data_agent.run()
    results["total"] = len(employees)

    if not employees:
        logger.warning("No employees found — pipeline aborted.")
        results["status"] = "empty"
        return results

    logger.info("═══ Processing %d employees one-by-one ═══", len(employees))

    # ── Process each employee sequentially ───────────────────────────────
    for i, emp in enumerate(employees, 1):
        name = emp.get("name", "Unknown")
        logger.info("── [%d/%d] Processing: %s ──", i, len(employees), name)

        try:
            # Step 2: Math Agent — compute ranking
            logger.info("  Step 2: Math Agent")
            math_agent.compute_ranking(emp)

            # Step 3: GitHub Agent — collect data, AI score, ROI
            logger.info("  Step 3: GitHub Agent")
            github_agent.run(emp)

            # Step 4: Update Agent — write to DB (waits for success)
            logger.info("  Step 4: Update Agent")
            update_agent.run(emp)

            emp["pipeline_status"] = "success"
            results["processed"] += 1
            logger.info("  ✓ %s done (ranking=%.4f, roi=%.4f)",
                        name,
                        emp.get("ranking", 0),
                        emp.get("roi", 0))

        except Exception as exc:
            logger.error("  ✗ %s FAILED: %s", name, exc)
            emp["pipeline_status"] = f"failed: {exc}"
            results["failed"] += 1

        # Add summary to results (strip large data for response)
        results["employees"].append({
            "id": emp.get("id"),
            "name": name,
            "ranking": emp.get("ranking"),
            "roi": emp.get("roi"),
            "github_score": emp.get("github_score"),
            "verdict": emp.get("_math_details", {}).get("verdict"),
            "pipeline_status": emp.get("pipeline_status"),
        })

    elapsed = round(time.time() - t0, 2)
    results["status"] = "completed"
    results["elapsed_seconds"] = elapsed

    logger.info("═══ Pipeline finished in %.2fs — %d/%d processed, %d failed ═══",
                elapsed, results["processed"], results["total"], results["failed"])
    return results
