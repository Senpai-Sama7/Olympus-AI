Dead code quarantine (2025-08-17)

This folder contains modules moved out of the active code paths to reduce confusion and prevent accidental imports. They were placeholders or demo code that conflicted with implemented modules or tests.

Quarantined items
- apps/api/olympus_api/plans.py → deadcode/20250817/plans.py: placeholder router conflicting with real API.
- apps/worker/olympus_worker/executor.py → deadcode/20250817/worker_executor.py: placeholder executor conflicting with real worker.
- app.py (repo root) → deadcode/20250817/app_demo.py: demo FastAPI app with overlapping routes/metrics.

Restore command
- To restore any file, move it back to its original path using your VCS or manually copy it from this folder.

Note
- If you want to iterate on these ideas, consider moving them into an `examples/` directory or behind feature flags to avoid conflicts.
