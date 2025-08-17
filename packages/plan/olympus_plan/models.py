# packages/plan/olympus_plan/models.py
from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    # pydantic v2
    from pydantic import BaseModel, Field, field_validator, model_validator
    PydV2 = True
except Exception:
    # pydantic v1 fallback
    from pydantic import BaseModel, Field, validator as field_validator, root_validator as model_validator
    PydV2 = False


class StepState(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    DONE = "DONE"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class PlanState(str, Enum):
    DRAFT = "DRAFT"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class CapabilityRef(BaseModel):
    """Symbolic reference to a tool/capability. Example: fs.read, fs.write, net.http_get"""
    name: str = Field(..., description="Capability identifier, e.g., 'fs.read', 'fs.write', 'net.http_get'")
    scope: List[str] = Field(default_factory=list, description="Consent scopes required to execute this capability")


class Guard(BaseModel):
    """Execution guardrails."""
    consent_required: bool = True
    max_retries: int = 2
    retry_backoff_ms: int = 250  # base
    retry_backoff_jitter_ms: int = 200  # added random jitter
    deadline_ms: Optional[int] = None  # relative per-step deadline
    budget_tokens: Optional[int] = None  # LLM tokens budget for this step
    budget_usd: Optional[float] = None  # LLM $ budget for this step (router enforces)


class Budget(BaseModel):
    """Plan-level budget that the router/tooling must respect."""
    token_limit: Optional[int] = None
    usd_limit: Optional[float] = None


class Step(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    capability: CapabilityRef
    input: Dict[str, Any] = Field(default_factory=dict)
    deps: List[str] = Field(default_factory=list, description="IDs of steps that must complete first")
    guard: Guard = Field(default_factory=Guard)

    state: StepState = StepState.PENDING
    attempts: int = 0
    started_at: Optional[int] = None  # epoch ms
    ended_at: Optional[int] = None    # epoch ms
    error: Optional[str] = None
    output: Optional[Dict[str, Any]] = None

    @field_validator("deps", mode="before")
    def _dedup_deps(cls, v: Any) -> Any:
        if not v:
            return []
        return list(dict.fromkeys(v))  # order-preserving dedup

    def mark_running(self) -> None:
        self.state = StepState.RUNNING
        self.started_at = self.started_at or int(time.time() * 1000)

    def mark_done(self, output: Optional[Dict[str, Any]] = None) -> None:
        self.state = StepState.DONE
        self.output = output
        self.ended_at = int(time.time() * 1000)

    def mark_failed(self, err: str) -> None:
        self.state = StepState.FAILED
        self.error = err
        self.ended_at = int(time.time() * 1000)

    def can_run(self, completed: Set[str]) -> bool:
        if self.state not in (StepState.PENDING, StepState.BLOCKED):
            return False
        return all(dep in completed for dep in self.deps)


class Plan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    created_at: int = Field(default_factory=lambda: int(time.time() * 1000))
    updated_at: int = Field(default_factory=lambda: int(time.time() * 1000))
    state: PlanState = PlanState.DRAFT
    budget: Budget = Field(default_factory=Budget)
    steps: List[Step] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_dag(self) -> "Plan":
        # ensure no cycles in deps
        graph: Dict[str, List[str]] = {s.id: list(s.deps) for s in self.steps}
        seen: Set[str] = set()
        stack: Set[str] = set()

        def dfs(node: str) -> None:
            if node in stack:
                raise ValueError(f"Cycle detected at step {node}")
            if node in seen:
                return
            stack.add(node)
            for d in graph.get(node, []):
                dfs(d)
            stack.remove(node)
            seen.add(node)

        for sid in graph.keys():
            dfs(sid)
        return self

    def index(self) -> Dict[str, Step]:
        return {s.id: s for s in self.steps}

    def runnable_steps(self) -> List[Step]:
        idx = self.index()
        completed = {s.id for s in self.steps if s.state == StepState.DONE}
        blocked_or_pending = [s for s in self.steps if s.state in (StepState.PENDING, StepState.BLOCKED)]
        return [s for s in blocked_or_pending if s.can_run(completed)]

    def all_done(self) -> bool:
        return all(s.state in (StepState.DONE, StepState.SKIPPED) for s in self.steps)

    def any_failed(self) -> bool:
        return any(s.state == StepState.FAILED for s in self.steps)

    def touch(self) -> None:
        self.updated_at = int(time.time() * 1000)


# Lightweight event shapes the worker/API use to persist a transcript.
class PlanEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ts: int = Field(default_factory=lambda: int(time.time() * 1000))
    type: str  # e.g., plan.created, step.started, step.done, step.failed
    plan_id: str
    step_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
