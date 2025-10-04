"""Run API smoke covering plan submit/run and consent gating."""
from __future__ import annotations

import json
import pathlib
import sys
import threading
import time

import httpx
from uvicorn import Config, Server

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from apps.api.olympus_api.main import app


def main() -> None:
    cfg = Config(app=app, host="127.0.0.1", port=8100, log_level="warning")
    server = Server(cfg)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    for _ in range(30):
        if server.started:
            break
        time.sleep(0.1)
    else:
        raise SystemExit("server failed to start")

    client = httpx.Client(base_url="http://127.0.0.1:8100", timeout=5.0)
    try:
        healthz = client.get("/healthz")
        print("healthz", healthz.status_code, healthz.json())

        submit_payload = {
            "title": "fs write/read",
            "steps": [
                {
                    "name": "write",
                    "capability": "fs.write",
                    "input": {"path": "audit/test.txt", "content": "hello reality"},
                    "deps": [],
                },
                {
                    "name": "read",
                    "capability": "fs.read",
                    "deps": ["0"],
                    "input": {"path": "audit/test.txt"},
                },
            ],
        }
        submit_resp = client.post("/v1/plan/submit", json=submit_payload)
        submit_body = submit_resp.json()
        print("submit", submit_resp.status_code, submit_body)
        plan_id = submit_body["plan_id"]

        run_payload = {"consent_token": "audit", "consent_scopes": ["*"]}
        run_resp = client.post(f"/v1/plan/{plan_id}/run", json=run_payload)
        print("run", run_resp.status_code, run_resp.json())

        for attempt in range(40):
            time.sleep(0.2)
            detail = client.get(f"/v1/plan/{plan_id}")
            body = detail.json()
            state = body["plan"]["state"]
            if state == "DONE":
                print("plan", state)
                print("steps", json.dumps(body["steps"], indent=2))
                break
            if state == "FAILED":
                print("plan", state, json.dumps(body, indent=2))
                break
        else:
            raise SystemExit("plan execution timeout")

        act_fail = client.post(
            "/v1/act",
            json={"capability": "fs.list", "input": {"path": "/"}},
        )
        print("act_no_consent", act_fail.status_code, act_fail.json())

        act_ok = client.post(
            "/v1/act",
            json={
                "capability": "fs.list",
                "input": {"path": "/"},
                "consent_token": "audit",
                "consent_scopes": ["*"],
            },
        )
        print("act_with_consent", act_ok.status_code, act_ok.json())
    finally:
        client.close()
        server.should_exit = True
        thread.join(timeout=5)


if __name__ == "__main__":
    main()
