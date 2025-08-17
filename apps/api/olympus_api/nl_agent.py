from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Optional, Tuple

from .planner import propose_plan, reflect_and_revise, TOOL_SCOPE
from packages.llm.olympus_llm.router import LLMRouter
from packages.plan.olympus_plan.models import Plan, PlanState


SYS = (
    "You are Olympus, a helpful local-first agent. You can: (1) ask a clarifying question, (2) produce a plan JSON to act using allowed tools, (3) directly respond in natural language.\n"
    "Always return ONLY valid JSON of the shape: {\"action\": \"ask|plan|respond\", \"message\": string, \"plan\": {title, steps[]} (when action=plan)}."
)


def _intent_prompt(user_text: str, allowed_tools: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": SYS},
        {
            "role": "user",
            "content": (
                "User message:\n" + user_text +
                "\nAllowed tools (JSON):\n" + json.dumps(allowed_tools) +
                "\nReturn only a JSON object: {action, message, plan?}."
            ),
        },
    ]


def parse_json_block(txt: str) -> Dict[str, Any]:
    try:
        i = txt.find("{"); j = txt.rfind("}")
        if i >= 0 and j > i:
            txt = txt[i:j+1]
        return json.loads(txt)
    except Exception:
        return {"action": "respond", "message": txt.strip()[:1000]}


def missing_scopes_for_plan(p: Plan, granted: Optional[List[str]]) -> List[str]:
    if not granted or "*" in granted:
        return []
    need: List[str] = []
    g = set(granted)
    for s in p.steps:
        scope = TOOL_SCOPE.get(s.capability.name)
        if scope and scope not in g and scope not in need:
            need.append(scope)
    return need


def ensure_session(session_id: Optional[str]) -> str:
    return session_id or str(uuid.uuid4())


def summarize_result_nl(plan: Plan) -> str:
    if plan.state == PlanState.DONE:
        return "Plan completed successfully."
    if plan.state == PlanState.FAILED:
        errs = [f"{s.name} -> {s.error}" for s in plan.steps if s.error]
        return "Plan failed: " + "; ".join(errs[:5])
    return f"Plan ended in state: {plan.state}"


async def handle_chat_turn(
    user_text: str,
    router: LLMRouter,
    allowed_scopes: Optional[List[str]] = None,
    consent_token: Optional[str] = None,
    max_tokens: Optional[int] = 800,
) -> Tuple[Dict[str, Any], Optional[Plan]]:
    allowed_tools = []
    from .planner import _available_tools  # reuse
    allowed_tools = _available_tools(allowed_scopes)

    # Determine intent
    try:
        intent = await router.chat(messages=_intent_prompt(user_text, allowed_tools), temperature=0.2, max_tokens=max_tokens)
    except Exception:
        prompt = "\n".join(m.get("content", "") for m in _intent_prompt(user_text, allowed_tools))
        intent = router.generate(prompt)
    data = parse_json_block(intent)
    action = str(data.get("action", "respond")).lower()
    message = str(data.get("message", "")).strip()

    if action == "ask":
        return ({"reply": message or "I need more information.", "requires_input": True}, None)

    if action == "respond" or not data.get("plan"):
        return ({"reply": message or ""}, None)

    # action == plan: propose or accept provided plan using planner
    plan = propose_plan(goal=message or user_text, router=router, context=None, temperature=0.1, max_tokens=max_tokens, allowed_scopes=allowed_scopes)
    # Check scopes vs consent
    miss = missing_scopes_for_plan(plan, allowed_scopes)
    if miss:
        return (
            {
                "reply": "This action requires additional consent scopes.",
                "requires_consent": True,
                "missing_scopes": miss,
                "proposed_plan": {"title": plan.title, "steps": [{"name": s.name, "capability": s.capability.name} for s in plan.steps]},
            },
            None,
        )

    # Execute with simple attempt (no reflection here; leave to /v1/agent/execute for longer loops)
    from packages.tools.olympus_tools.fs import ConsentToken
    consent = None
    if consent_token or (allowed_scopes and "*" not in allowed_scopes):
        consent = ConsentToken(token=consent_token or "user", scopes=allowed_scopes or ["*"])
    # Return both response and plan for controller to persist/run
    return ({"reply": f"Executing plan: {plan.title}"}, plan)

