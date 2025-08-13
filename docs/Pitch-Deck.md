# Olympus AI — Pitch Deck

## 1. Problem

- Enterprises struggle to harness AI at scale while controlling risk
- Automation scripts and web interactions are either unsafe or brittle
- Knowledge lives across documents; search is inconsistent and slow

## 2. Solution

A modular platform delivering:

- Secure enterprise web app for users, products, and admin
- AI data plane (ingest → embeddings → retrieval)
- Controlled broad capabilities:
  - Safe local code execution in a sandbox
  - Controlled headless web automation

## 3. Why now

- AI adoption accelerating; governance requirements intensifying
- Dev teams need secure, auditable automation and data access
- Cloud-native containers and headless browsers are mature

## 4. Product

- Web App (React + Express + MongoDB) with JWT auth, RBAC, caching, Swagger docs
- AI Data Plane: Rust control plane (gRPC), Temporal ingest worker, pgvector retrieval API
- Controlled Capabilities:
  - Exec Service: run Python/Node/Bash in secure containers with CPU/Mem/Time caps and network gating
  - WebBot Service: Playwright headless browser to navigate, fill forms, extract data, screenshot/PDF
- Security: rate limiting (Redis optional), sandboxing, API keys, auditing (SQLite), structured logs

## 5. How it works

- Containers orchestrated via Docker Compose (infra + apps)
- Shared sandbox volume for controlled file I/O
- Redis streams glue ingest and events; Temporal provides durable workflows
- CI builds and scans images (Trivy) on every push/PR

## 6. Use cases

- Ops: automated evidence collection (screenshots/PDFs) for audits
- Support: one-click diagnostics (safe scripts) scoped to a workspace
- Data: document ingestion and domain-specific search
- Finance: browser workflows for statement retrieval and reconciliation

## 7. Differentiation

- Security-first: isolation-by-default, confirmations for sensitive actions
- Auditability: every operation recorded (who/what/when/outcome)
- Modularity: swap in better embedding models; extend services independently

## 8. Business model (examples)

- Subscription per environment/tenant
- Add-ons for advanced models, RBAC integration, premium audit retention
- Professional services: onboarding, integrations, bespoke automations

## 9. Traction / roadmap

- CPU-only, fully runnable starter
- Next: managed secrets, mTLS for gRPC, Temporal SQL persistence, model upgrades
- CI enhancements: E2E tests, SAST/DAST, policy-as-code

## 10. Team

- Full-stack, systems, and security engineering experience
- Track record in enterprise compliance and platform ops

## 11. Ask

- Pilot partners for secure automation and AI retrieval
- Feedback on enterprise requirements and integrations

## 12. Contact

- Email: <enterprise@olympus-ai.company>
- GitHub Actions: CI configured for builds and security scans
