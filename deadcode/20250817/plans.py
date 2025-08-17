from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

try:
    from olympus_plan.models import Plan  # placeholder import
except Exception:
    Plan = object  # type: ignore

router = APIRouter()

@router.post("/v1/plan/submit", response_model=Plan)
async def submit_plan(plan: Plan) -> Plan:  # type: ignore
    raise HTTPException(501, "quarantined placeholder")

