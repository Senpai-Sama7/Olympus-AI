import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from olympus_api.settings import get_settings


def read_last_heartbeat() -> Optional[datetime]:
	settings = get_settings()
	p = Path(settings.WORKER_HEARTBEAT_PATH)
	if not p.exists():
		return None
	try:
		data = json.loads(p.read_text(encoding="utf-8"))
		return datetime.fromisoformat(data.get("ts"))
	except Exception:
		return None
