from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StepAction(BaseModel):
    tool: str = Field(description="Tool package name, e.g., 'filesystem', 'http', 'automation'")
    name: str = Field(description="Action name")
    params: Dict[str, Any] = Field(default_factory=dict)


class Step(BaseModel):
    id: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    preconditions: List[str] = Field(default_factory=list)
    action: StepAction
    postconditions: List[str] = Field(default_factory=list)
    rollback: Optional[StepAction] = None
    idem_key: Optional[str] = None


class PlanBudget(BaseModel):
    tokens: int = 0
    seconds: int = 0


class Plan(BaseModel):
    id: str
    goal: str
    steps: List[Step] = Field(default_factory=list)
    mode: str = Field(default="Draft")  # Observe|Draft|Autopilot
    budget: PlanBudget = Field(default_factory=PlanBudget)
