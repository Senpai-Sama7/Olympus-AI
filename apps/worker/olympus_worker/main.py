import asyncio
import json
import logging
import random
import signal
from datetime import datetime, timezone
from pathlib import Path

from olympus_api.logging import configure_json_logging
from olympus_api.settings import get_settings


def _utc_iso() -> str:
	return datetime.now(timezone.utc).isoformat()


async def write_heartbeat(path: Path) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	payload = {"ts": _utc_iso()}
	path.write_text(json.dumps(payload), encoding="utf-8")


async def run_worker(stop_event: asyncio.Event) -> None:
	settings = get_settings()
	configure_json_logging(component="worker", level=settings.LOG_LEVEL)
	logger = logging.getLogger("worker")
	heartbeat_path = Path(settings.WORKER_HEARTBEAT_PATH)
	backoff = 1.0
	while not stop_event.is_set():
		try:
			await write_heartbeat(heartbeat_path)
			logger.info("heartbeat written")
			backoff = 1.0
			await asyncio.wait_for(stop_event.wait(), timeout=5.0)
		except asyncio.TimeoutError:
			continue
		except Exception as e:
			logger.error(f"worker error: {e}")
			await asyncio.sleep(backoff + random.uniform(0, 0.5))
			backoff = min(30.0, backoff * 2)


def main() -> None:
	loop = asyncio.new_event_loop()
	asyncio.set_event_loop(loop)
	stop_event = asyncio.Event()

	def _signal_handler(signum, frame):
		stop_event.set()

	signal.signal(signal.SIGINT, _signal_handler)
	signal.signal(signal.SIGTERM, _signal_handler)
	try:
		loop.run_until_complete(run_worker(stop_event))
	finally:
		loop.stop()
		loop.close()


if __name__ == "__main__":
	main()
