
# Gap Analysis Report

Generated: 2024-01-09

## Executive Summary

This report analyzes the gaps between the current "Olympus AI" system and the target "local-first, cloud-fallback agentic assistant" requirements. While the existing system provides solid foundations (auth, microservices, sandboxing), significant architectural changes and new components are required.

## Major Architectural Shifts Required

### 1. From Cloud-First to Local-First
**Current**: Distributed microservices requiring multiple containers
**Target**: Local-first with optional cloud fallback
**Gap**: Need to consolidate services and enable single-binary/minimal deployment

### 2. From Enterprise Web App to AI Assistant
**Current**: Traditional CRUD app with some AI features
**Target**: ChatGPT-like assistant with advanced capabilities
**Gap**: Complete UI overhaul, new interaction paradigms

### 3. From Service-Oriented to Agent-Oriented
**Current**: Discrete services for specific tasks
**Target**: Unified agent with plans, memory, and iterative execution
**Gap**: Need agent orchestration layer and planning system

## Component-Level Gap Analysis

### Frontend Transformation

| Component | Current State | Target State | Gap |
|-----------|--------------|--------------|-----|
| UI Framework | React with traditional pages | Chat-first UI with modes | Complete redesign |
| Main Interface | Multiple pages (login, dashboard, etc.) | Single chat box + previews | New component architecture |
| Interaction Model | Forms and lists | Conversational with modes (Observe/Draft/Autopilot) | New interaction paradigm |
| State Management | Redux for auth/products | Agent state, conversations, plans, memory | Expanded state model |
| Visual Builder | None | Drag-drop flow builder | Build from scratch |

### Backend Evolution

| Component | Current State | Target State | Gap |
|-----------|--------------|--------------|-----|
| Main API | Express with MongoDB | FastAPI with SQLite | Platform migration |
| Authentication | Email/password with JWT | Hashed passphrase | Simpler auth model |
| Data Model | Users/Products | Conversations/Tasks/Plans/Memory | Complete schema redesign |
| Execution Model | Stateless REST | Stateful agent with context | Agent runtime needed |

### New Components Required

1. **LLM Router Package** (`/packages/llm`)
   - Ollama integration
   - Cloud provider adapters (OpenAI, Anthropic, Gemini)
   - Budget management
   - Fallback logic
   - Token counting

2. **Plan DSL Package** (`/packages/plan`)
   - Pydantic models for plans/steps
   - Precondition/postcondition checking
   - Rollback mechanisms
   - Idempotence tracking
   - Dry-run simulator

3. **Memory Package** (`/packages/memory`)
   - SQLite schema design
   - Vector index integration (sqlite-vec or SQLite-Vector)
   - Embedding pipeline with sentence-transformers
   - Search APIs with MMR
   - Document ingestion

4. **Agent Worker** (`/apps/worker`)
   - Plan executor
   - Code Interpreter sandbox
   - Tool orchestration
   - Retry/compensation logic
   - Resource management

5. **Desktop App** (`/apps/desktop`)
   - Tauri or Electron wrapper
   - System tray integration
   - Local file access
   - Native notifications

### Service Consolidation

**Current Services to Merge/Transform:**
- Control Plane (Rust) → Part of main API
- Retrieval Service → Memory package
- Temporal Worker → Agent worker
- Exec Service → Code Interpreter in worker
- WebBot Service → Automation package with MCP

**Infrastructure Simplification:**
- From: MongoDB + PostgreSQL + Redis + SQLite
- To: SQLite (primary) + Redis (optional cache)

## Feature Gap Matrix

| Feature | Exists | Needs Work | Build New |
|---------|--------|------------|-----------|
| Local LLM (Ollama) | ❌ | | ✅ |
| LLM Router | ❌ | | ✅ |
| Chat UI | ❌ | | ✅ |
| Modes (O/D/A) | ❌ | | ✅ |
| Plans DSL | ❌ | | ✅ |
| Code Interpreter | ⚠️ | ✅ | |
| Web Automation | ✅ | ✅ | |
| MCP Server | ❌ | | ✅ |
| Vector Search | ⚠️ | ✅ | |
| Memory Hierarchy | ❌ | | ✅ |
| Visual Flow Builder | ❌ | | ✅ |
| Budget Management | ❌ | | ✅ |
| Passphrase Auth | ❌ | | ✅ |
| Allow-lists | ⚠️ | ✅ | |

## Migration Complexity Assessment

### High Complexity Items
1. **UI Overhaul**: Complete replacement of current multi-page app
2. **Planning System**: New architectural pattern
3. **LLM Integration**: Complex routing and fallback logic
4. **Memory Hierarchy**: Sophisticated data management

### Medium Complexity Items
1. **Code Interpreter Enhancement**: Build on existing exec service
2. **Vector Search Migration**: Switch embedding approach
3. **Authentication Simplification**: Replace JWT with passphrase
4. **Desktop Packaging**: New deployment model

### Low Complexity Items
1. **MCP Server Adapter**: Wrapper around existing Playwright
2. **Budget Tracking**: Add to LLM router
3. **Audit Enhancement**: Extend existing logging

## Resource Requirements

### Development Effort Estimate
- **Phase 0-2**: 2-3 weeks (foundation and auth)
- **Phase 3-4**: 3-4 weeks (plans and code interpreter)
- **Phase 5-6**: 2-3 weeks (automation and LLM)
- **Phase 7-8**: 3-4 weeks (UI and polish)
- **Total**: 10-14 weeks for full transformation

### Technical Dependencies
- Ollama for local LLM
- sqlite-vec or SQLite-Vector
- sentence-transformers
- Playwright (existing)
- Tauri/Electron for desktop
- Modern Python (3.11+) for FastAPI

## Risk Analysis

### Technical Risks
1. **Performance**: Local LLM may be slow on weak hardware
2. **Compatibility**: Vector extensions may have platform issues
3. **Security**: Broader attack surface with desktop app

### Migration Risks
1. **Data Loss**: Need careful migration from MongoDB
2. **Feature Parity**: Some enterprise features may be lost
3. **User Experience**: Dramatic shift in interaction model

## Recommendations

1. **Incremental Migration**: Keep old system running during transition
2. **Feature Flags**: Enable gradual rollout of new components
3. **Compatibility Layer**: Temporary adapters for data migration
4. **Testing Strategy**: Comprehensive tests for each phase
5. **Fallback Plan**: Ensure rollback capability at each phase

## Conclusion

The transformation from "Olympus AI" to the target agentic assistant represents a fundamental architectural shift. While certain components (auth, sandboxing, automation) can be evolved, the core user experience and agent capabilities must be built new. The phased approach outlined in the migration plan will minimize risk while delivering value incrementally.
# Gap Analysis

## Target vs Current

- UI: Chat UI with modes (Observe/Draft/Autopilot)
  - Current: React SPA for ecommerce admin with auth and products
  - Gap: No Chat UI, modes, previews, Flow Builder, or dashboard

- Local Code Interpreter (sandboxed Python with safe I/O)
  - Current: `services/exec-service` can run code in Docker with limits
  - Gap: Not integrated into a unified API/worker; no iterative loop, artifacts packaging, or Ask-before-doing guardrails

- Web Automation (Playwright + artifacts + MCP)
  - Current: `services/webbot-service` supports actions + audit
  - Gap: No resilient selector heuristics, retry/backoff policy, MCP adapter, or integration into plan/executor

- Private Memory (SQLite + vector index)
  - Current: Retrieval service uses Postgres + pgvector; no local SQLite vector index; no conversations/tasks schema
  - Gap: Need SQLite schema, migrations, embeddings pipeline (sentence-transformers), and ANN search with sqlite-vec/SQLite-Vector

- LLM Router (local-first Ollama → cloud fallback)
  - Current: No centralized router; some docs around models
  - Gap: Need router with budgets, backoff, confidence/complexity routing, and graceful fallback

- Plans-as-code (DSL + simulator + idempotence + rollback)
  - Current: Temporal workflows exist but not the requested Plan DSL
  - Gap: Need Pydantic Plan/Step models, dry-run diffs, idempotence utilities, compensation/rollback patterns

- Visual Flow Builder
  - Current: None
  - Gap: Canvas + nodes + NL→plan compile + save/load as Plan JSON

- Security & Modes
  - Current: JWT auth (server), rate-limit, helmet; no cookie sessions/CSRF; no allow-list enforcement for writes/domains
  - Gap: Hashed passphrase login, signed HTTP-only cookies, CSRF, per-IP rate limit at API, ask-before-doing ON, allow-lists

- Observability and Acceptance Tests
  - Current: Some tracing infra (otel/jaeger), no unified metrics dashboard for TSR/FAP, no acceptance tests for features
  - Gap: Dashboard and test suites per acceptance criteria

## Dev Experience / Monorepo

- Current: Mixed stacks and multiple docker-compose files; no unified Python workspace or Makefile for dev
- Gap: Monorepo layout with `/apps/*` and `/packages/*`, `make dev`, `make test`, pre-commit hooks, `.env.example`, and `infra/init.sh`

