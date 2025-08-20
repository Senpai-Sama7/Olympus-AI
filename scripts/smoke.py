import time
import threading
import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from uvicorn import Config, Server
from apps.api.olympus_api.main import app

cfg = Config(app=app, host="127.0.0.1", port=8000, log_level="warning")
svr = Server(cfg)
thread = threading.Thread(target=lambda: sys.exit(svr.run()))
thread.daemon = True
thread.start()

time.sleep(1.0)

import httpx
with httpx.Client() as client:
    resp = client.get("http://127.0.0.1:8000/health")
    assert resp.status_code == 200
    resp = client.get("http://127.0.0.1:8000/metrics")
    assert resp.status_code == 200
print("OK")
