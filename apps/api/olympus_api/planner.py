from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional
import requests

from packages.plan.olympus_plan.models import CapabilityRef, Plan, Step
from packages.llm.olympus_llm.router import LLMRouter


SYSTEM_PROMPT = (
    "You are a precise planning agent. Given a high-level goal and a list of available tools, "
    "produce a minimal JSON plan with steps to achieve the goal. Output ONLY valid JSON."
)


def build_context_for_goal(goal: str, max_chars: int = 4000) -> Optional[str]:
    """Lightweight context builder: scan common files for keywords in the goal and return snippets.
    This is a simple local heuristic to avoid requiring the external retrieval service.
    """
    # Try retrieval service first (if configured)
    try:
        base = os.getenv("RETRIEVAL_URL", "http://127.0.0.1:8081").rstrip("/")
        r = requests.post(f"{base}/v1/retrieval/search", json={"query": goal, "k": 5}, timeout=2.0)
        if r.status_code == 200:
            data = r.json()
            results = data.get("results") or data.get("data", {}).get("results")
            if results:
                parts = []
                total = 0
                for item in results:
                    src = str(item.get("source") or item.get("meta", {}).get("source") or "retrieval")
                    content = str(item.get("content") or item.get("text") or "")
                    block = f"RETRIEVED FROM: {src}\n{content}\n\n"
                    if total + len(block) > max_chars:
                        break
                    parts.append(block)
                    total += len(block)
                if parts:
                    return "".join(parts)
    except Exception:
        pass
    try:
        import os
        import re
        root = os.getcwd()
        kws = [w.lower() for w in re.findall(r"[a-zA-Z0-9_]{3,}", goal)][:8]
        paths: List[str] = []
        for base, dirs, files in os.walk(root):
            if any(seg.startswith('.') for seg in base.split(os.sep)):
                continue
            for name in files:
                if not any(name.endswith(ext) for ext in ('.py', '.md', '.toml', '.yaml', '.yml', '.json', '.js', '.ts')):
                    continue
                p = os.path.join(base, name)
                try:
                    with open(p, 'rb') as f:
                        data = f.read(8192)
                    text = data.decode(errors='ignore').lower()
                    if any(kw in text or kw in name.lower() for kw in kws):
                        paths.append(p)
                        if len(paths) >= 8:
                            raise StopIteration
                except Exception:
                    continue
    except StopIteration:
        pass
    except Exception:
        return None
    snippets = []
    total = 0
    for p in paths[:8]:
        try:
            with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(max(512, min(2048, max_chars - total)))
            block = f"FILE: {os.path.relpath(p)}\n" + content
            snippets.append(block)
            total += len(block)
            if total >= max_chars:
                break
        except Exception:
            continue
    return "\n\n".join(snippets) if snippets else None


TOOL_SCOPE = {
    "fs.read": "read_fs",
    "fs.write": "write_fs",
    "fs.delete": "delete_fs",
    "fs.list": "list_fs",
    "fs.glob": "list_fs",
    "fs.search": "search_fs",
    "shell.run": "exec_shell",
    "git.status": "git_ops",
    "git.add": "git_ops",
    "git.commit": "git_ops",
    "net.http_get": "net_get",
}


def _available_tools(allowed_scopes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    # Mirrors the tools registered in the worker; optionally filter by consent scopes.
    all_tools = [
        {"name": "fs.read", "desc": "Read a file from sandbox"},
        {"name": "fs.write", "desc": "Write a file to sandbox"},
        {"name": "fs.delete", "desc": "Delete a file or directory in sandbox"},
        {"name": "fs.list", "desc": "List directory entries"},
        {"name": "fs.glob", "desc": "Glob files under a start path"},
        {"name": "fs.search", "desc": "Regex search within a file"},
        {"name": "shell.run", "desc": "Run a shell command in sandbox"},
        {"name": "git.status", "desc": "Git status"},
        {"name": "git.add", "desc": "Git add paths"},
        {"name": "git.commit", "desc": "Git commit message"},
        {"name": "net.http_get", "desc": "HTTP GET a URL (consent-gated)"},
    ]
    if not allowed_scopes or "*" in allowed_scopes:
        return all_tools
    allowed = set(allowed_scopes)
    filtered = []
    for t in all_tools:
        scope = TOOL_SCOPE.get(t["name"]) or "*"
        if scope in allowed:
            filtered.append(t)
    return filtered


def _plan_schema_hint() -> str:
    return (
        "{"
        "\n  \"title\": \"short title\","
        "\n  \"steps\": ["
        "\n    {\"name\": \"step-name\", \"capability\": \"tool.name\", \"deps\": [], \"input\": {}}"
        "\n  ]"
        "\n}"
    )


def _mk_prompt(goal: str, context: Optional[str], allowed_tools: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, str]]:
    tools = json.dumps(allowed_tools or _available_tools(), ensure_ascii=False)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Goal:\n" + goal +
                ("\n\nContext:\n" + context if context else "") +
                "\n\nAvailable tools (JSON) — you MUST only use tools from this allowlist:\n" + tools +
                "\n\nRespond with ONLY valid JSON exactly matching this shape:\n" + _plan_schema_hint()
            ),
        },
    ]
    return messages


def propose_plan(goal: str, router: Optional[LLMRouter] = None, context: Optional[str] = None, model: Optional[str] = None, temperature: float = 0.2, max_tokens: Optional[int] = 800, allowed_scopes: Optional[List[str]] = None) -> Plan:
    router = router or LLMRouter()
    allowed_tools = _available_tools(allowed_scopes)
    ctx = context or build_context_for_goal(goal)
    messages = _mk_prompt(goal, ctx, allowed_tools)
    # Use async path via sync wrapper for compatibility: router.chat is async; generate() is sync.
    # Prefer generate() for simpler environments (fallback) by concatenating messages.
    try:
        import asyncio

        async def _go():
            return await router.chat(messages=messages, model=model, temperature=temperature, max_tokens=max_tokens)

        txt = asyncio.get_event_loop().run_until_complete(_go())
    except Exception:
        prompt = "\n".join(m.get("content", "") for m in messages)
        txt = router.generate(prompt)
    data = _parse_plan_json(txt)
    steps = []
    for st in data.get("steps", []):
        steps.append(
            Step(
                name=st["name"],
                capability=CapabilityRef(name=st["capability"], scope=[]),
                input=st.get("input", {}),
                deps=st.get("deps", []),
            )
        )
    title = data.get("title") or f"agent: {goal[:48]}"
    return Plan(title=title, steps=steps, metadata={"goal": goal})


def _parse_plan_json(txt: str) -> Dict[str, Any]:
    try:
        # find first and last braces to be robust if the model adds chatter
        start = txt.find("{")
        end = txt.rfind("}")
        if start >= 0 and end > start:
            txt = txt[start : end + 1]
        return json.loads(txt)
    except Exception as e:
        # fallback: create trivial plan
        return {
            "title": "write+read fallback",
            "steps": [
                {"name": "w", "capability": "fs.write", "input": {"path": "demo/agent.txt", "content": txt}},
                {"name": "r", "capability": "fs.read", "deps": ["0"], "input": {"path": "demo/agent.txt"}},
            ],
        }


def reflect_and_revise(goal: str, prev_plan: Plan, failure: Dict[str, Any], router: Optional[LLMRouter] = None, model: Optional[str] = None) -> Plan:
    router = router or LLMRouter()
    prev = {
        "title": prev_plan.title,
        "steps": [
            {"id": s.id, "name": s.name, "capability": s.capability.name, "deps": s.deps, "input": s.input}
            for s in prev_plan.steps
        ],
    }
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Goal:\n{goal}"},
        {"role": "user", "content": f"Previous plan JSON:\n{json.dumps(prev)}"},
        {"role": "user", "content": f"Failure summary:\n{json.dumps(failure)}\nRevise the plan JSON to fix the issue. Output ONLY valid JSON."},
    ]
    try:
        import asyncio

        async def _go():
            return await router.chat(messages=messages, model=model, temperature=0.1, max_tokens=800)

        txt = asyncio.get_event_loop().run_until_complete(_go())
    except Exception:
        prompt = "\n".join(m.get("content", "") for m in messages)
        txt = router.generate(prompt)
    data = _parse_plan_json(txt)
    steps = []
    for st in data.get("steps", []):
        steps.append(
            Step(
                name=st["name"],
                capability=CapabilityRef(name=st["capability"], scope=[]),
                input=st.get("input", {}),
                deps=st.get("deps", []),
            )
        )
    title = data.get("title") or prev_plan.title
    return Plan(title=title, steps=steps, metadata={"goal": goal, "rev": int(time.time())})
