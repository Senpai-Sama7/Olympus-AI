---

# 0) Master “Chief Engineer” audit & fix

```
ROLE: Chief Engineer (ruthless). I own correctness, security, operability.
SCOPE: Entire repo. Python, TS/JS, Docker, CI, desktop, services.
MODE: Read → Plan → Execute → PR(s). No partial fixes. Keep changes documented

GOALS (hard gates):
- All targets build & start locally. All tests pass. Lints clean.
- Type-check clean (mypy/pyright). Ruff style ok. Prettier ok. Hadolint ok.
- No HIGH/CRITICAL vulns (pip-audit, npm audit, grype). No secrets (detect-secrets).
- 80%+ line coverage in core packages/apps; never lower existing coverage.
- SBOM published. Reproducible build instructions validated.
- Observability: /metrics exports RED/USE; alerts config syntactically valid.
- Smoke: plan submit→run (fs.write→fs.read) green; consent gate enforced.

PLAN:
1) Inventory + dependency graph; detect dead code & cycles.
2) Static checks, types, formatting; auto-fix safe items.
3) Security & supply chain (audit, SBOM, license, secrets).
4) Tests: run + fill obvious holes; add missing unit tests for planners/tools.
5) Runtime: boot API; run smoke; exercise /metrics; validate alerts; archive logs.
6) CI: create/update GitHub Actions to enforce above.
7) Docs: minimal operator runbook + Make targets.

COMMANDS (run in zsh, fail fast if any step fails):
- Python: ruff check --fix . ; black . ; mypy apps packages services ; pytest -q --maxfail=1 --disable-warnings --cov=packages --cov=apps
- JS/TS: npm i --prefix client ; npm run -s lint --prefix client ; npm audit --audit-level=high --prefix client ; same for server/
- Security: pip-audit ; bandit -q -r apps packages services ; detect-secrets scan > .secrets.baseline ; trivy fs . || true
- Containers: docker build -f services/retrieval/Dockerfile . ; hadolint **/Dockerfile || true ; syft dir:. -o spdx-json=sbom.spdx.json ; grype dir:. --fail-on High
- Observability: start uvicorn apps.api.olympus_api.main:app ; curl /healthz ; curl /metrics ; promtool check rules alerts.yml
- Smoke: POST /v1/plan/submit (fs.write→fs.read), then POST /v1/plan/{id}/run, assert DONE.
- CI: ensure .github/workflows/ci.yml enforces same gates; fail build on any HIGH vuln or test failure.

OUTPUTS:
- Summary table of failures; list of fixes applied with diffs.
- Open PRs: “lint+types”, “security+sbom”, “ci+smoke”, “docs+runbook”.
- If any high-risk refactor needed, open issue with RFC template + rollback plan.

DO IT.
```

---

# 1) Repo sanity, builds, and dead code

```
Scan Olympus AI for build drift and dead code. Generate a file-by-file table:
[path] [lang] [build target] [last ref] [dead?] [owner guess]

Then:
- Add `make fmt lint type test smoke` delegating to per-language tools.
- Remove or quarantine dead code into `deadcode/YYMMDD/` with a README listing reasons and restore command.

Commands to run:
make fmt ; make lint ; make type ; make test ; make smoke

Produce a PR “build: unify make targets + dead code quarantine” with CI green.
```

---

# 2) Static analysis (ruff/black/mypy/pyright/prettier) – auto-fix

```
Run & auto-fix:
- Python: ruff check --fix ., black ., mypy apps packages services
- TypeScript/JS: npm run -s lint --prefix client && npm run -s lint --prefix server ; prettier -w .

Open PR: “style+types: repo-wide ruff/black/mypy + prettier”. Include short summary of noteworthy type fixes.
```

---

# 3) Security: secrets, deps, containers, licenses

```
1) Secrets: detect-secrets scan → .secrets.baseline ; fail CI if new secrets appear.
2) Python deps: pip-audit ; bandit -q -r apps packages services ; safety check (if installed).
3) Node deps: npm audit --omit=dev --audit-level=high in client/ and server/.
4) SBOM: syft dir:. -o spdx-json=sbom.spdx.json ; attach artifact to CI.
5) Container vulns: grype dir:. --fail-on High ; hadolint **/Dockerfile.
6) Licenses: generate license report; fail on restricted licenses.

Deliverables:
- PR “sec: secrets baseline + audits + SBOM + license report”.
- Update CI to fail on HIGH/CRITICAL findings; allow override via `SECURITY_DEBT_APPROVED=true` label only.
```

---

# 4) Tests & coverage (raise floor to 80%+ in core)

```
Run `pytest -q --maxfail=1 --disable-warnings --cov=packages --cov=apps --cov-report=term-missing`.

If coverage <80% for packages/{plan,memory,llm,tools} or apps/{api,worker}:
- Add missing unit tests for: Plan DAG validation, Executor retries/backoff, FS sandbox escape prevention, Router budget enforcement.
- Add snapshot tests for /v1/plan submit/run and /v1/act consent errors.
- Don’t mock what you can run cheaply.

Open PR: “test: raise coverage to 80%+ core paths” with coverage diff.
```

---

# 5) Runtime smoke, invariants, and metrics

```
Boot API (uvicorn apps.api.olympus_api.main:app). Validate:
- /healthz JSON has ask_before_doing flag.
- /metrics exposes requests_total, errors_total, request_duration_seconds, queue_depth.
- Submit fs.write→fs.read plan; assert final state == DONE within 3s.
- POST /v1/act without consent must 403 OLY-ACT-401; with consent token/scopes must succeed.

Publish a short log tail and a jq filter for correlation IDs. PR: “ops: smoke + invariants + metrics docs”.
```

---

# 6) Observability & alerts (prometheus + alert rules)

```
Validate prom config + rules:
- promtool check rules alerts.yml
- curl /metrics and confirm non-empty histograms and counters increment during smoke.

If missing, create alerts.yml with:
- CircuitOpen, ErrorRateSpike, HighLatencyP95, QueueBacklogGrowing

Update docker-compose.prom.yml to run Prometheus+Grafana locally. PR: “obs: alert rules + local prom/grafana compose”.
```

---

# 7) Planner/executor correctness (DAG, retries, consent)

```
Prove these properties with tests + code instrumented counters:
- DAG: cycle detection works (expect ValueError).
- Executor: retry with jitter triggers on failing tool; stops on deadline; emits step.failed events.
- Consent: REQUIRE_CONSENT=true blocks fs.write; CONSENT=auto allows in dev; act route enforces scopes.

Add tests asserting event transcript order: plan.created → plan.started → step.started → step.done → plan.done.
PR: “plan/executor: property tests + transcript assertions”.
```

---

# 8) LLM router (offline-first, budgeted fallback)

```
Set OLY_ENABLE_CLOUD=false and prove failures bubble if Ollama down; with true and budget set (e.g., $0.05), prove single fallback then budget ceiling blocks further calls.

Add tests:
- cache hit on identical prompt
- budget exceed raises BudgetExceeded
PR: “llm: cache+budget tests; offline-first guards”.
```

---

# 9) Security-hard FS tool (path escape, symlink)

```
Fuzz tests for fs._normalize:
- Reject ../, absolute paths outside SANDBOX_ROOT, symlink traversal.
- Ensure list/read/write/delete with explicit consent scopes only.

PR: “tools/fs: fuzz & policy tests; tightened path normalization”.
```

---

# 10) Desktop packaging readiness (smoke installer)

```
If desktop/ exists:
- Build minimal Tauri/Electron shell to hit local API; add “Consent Prompt” modal.
- Ensure “offline mode” toggle connects to OLLAMA_URL and disables cloud fallback envs.

PR: “desktop: shell + consent UI + offline toggle”, plus a README “How to package Mac/Win/Linux”.
```

---

# 11) Release + CI gates (enterprise bar)

```
Add `.github/workflows/ci.yml` that gates on:
- lint, type, test, coverage >= 80% (fail if drops)
- pip-audit/bandit/safety: no HIGH/CRITICAL
- npm audit (client/server): no HIGH
- grype: no High in images or filesystem
- promtool check rules
- smoke passes

Artifacts: uvicorn.log, sbom.spdx.json, coverage.xml. PR: “ci: enforce enterprise gates + artifacts”.
```

---

# 12) Chaos & resilience (optional but valuable)

```
Introduce controlled failures:
- Flip APP_USE_FLAKY_DEP=true (or inject a toy flaky tool).
- Confirm breaker metrics and alerts fire; ensure recovery within 10s.

PR: “resilience: chaos toggles + breaker alert check”.
```

---


---



