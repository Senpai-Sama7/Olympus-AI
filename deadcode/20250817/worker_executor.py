import asyncio
from typing import Dict, Any

class ToolAdapter:
    async def execute(self, tool: str, name: str, params: Dict[str, Any]) -> Any:
        await asyncio.sleep(0.1)
        return {"result": "quarantined"}

