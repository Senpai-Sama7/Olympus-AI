from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field


class PlanState(str, Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    DONE = "DONE"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


TRANSITION_TABLE: Dict[PlanState, List[PlanState]] = {
    PlanState.DRAFT: [PlanState.READY, PlanState.REJECTED],
    PlanState.READY: [PlanState.RUNNING, PlanState.PAUSED],
    PlanState.RUNNING: [PlanState.PAUSED, PlanState.DONE, PlanState.FAILED],
    PlanState.PAUSED: [PlanState.RUNNING, PlanState.DONE, PlanState.FAILED],
    PlanState.DONE: [],
    PlanState.FAILED: [],
    PlanState.REJECTED: [],
}


class CapabilityRef(BaseModel):
    namespace: str = Field(description="e.g. filesystem, browser, shell")
    tool_name: str
    function_name: str


class Guard(BaseModel):
    description: str
    preconditions: List[str] = Field(default_factory=list)
    postconditions: List[str] = Field(default_factory=list)
    on_failure: str  # e.g. "human-in-the-loop", "fail-fast", "retry"


class Budget(BaseModel):
    tokens: int = 0
    cost_usd: float = 0.0
    time_seconds: int = 0


class StepAction(BaseModel):
    tool: str = Field(
        description="Tool package name, e.g., 'filesystem', 'http', 'automation'"
    )
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


class Plan(BaseModel):
    id: str
    goal: str
    steps: List[Step] = Field(default_factory=list)
    state: PlanState = Field(default=PlanState.DRAFT)
    budget: Budget = Field(default_factory=Budget)