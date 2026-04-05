from fastapi import APIRouter

from agents.orchestrator import run_pipeline

router = APIRouter()


@router.post("/run")
def trigger_pipeline():
    """Trigger the full 4-agent ranking pipeline."""
    result = run_pipeline()
    return result
