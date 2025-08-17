from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from olympus_plan.models import Plan

# Placeholder for consent middleware
def consent_middleware(plan: Plan) -> bool:
    # In a real implementation, this would check for user consent
    return True

# Placeholder for budget checks
def budget_checks(plan: Plan) -> bool:
    # In a real implementation, this would check if the plan is within budget
    return True


router = APIRouter()


@router.post("/v1/plan/submit", response_model=Plan)
async def submit_plan(plan: Plan) -> Plan:
    if not consent_middleware(plan):
        raise HTTPException(status_code=403, detail="Consent not given")
    if not budget_checks(plan):
        raise HTTPException(status_code=402, detail="Budget exceeded")
    # In a real implementation, this would save the plan to a database
    return plan


@router.get("/v1/plan/{id}", response_model=Plan)
async def get_plan(id: str) -> Plan:
    # In a real implementation, this would retrieve the plan from a database
    return Plan(id=id, goal="Dummy plan")


@router.post("/v1/act")
async def act(payload: Dict[str, Any]) -> Dict[str, Any]:
    # In a real implementation, this would perform an action based on the payload
    return {"status": "action performed"}
