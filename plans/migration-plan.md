# Migration Plan: Olympus AI → Local-First Agentic Assistant

Generated: 2024-01-09

## Overview

This document outlines a phased migration strategy to transform the existing "Olympus AI" enterprise system into a local-first, cloud-fallback agentic assistant. The migration is designed to be incremental, with each phase delivering functional value while minimizing risk.

## Guiding Principles

1. **Incremental Value**: Each phase delivers working functionality
2. **Backward Compatibility**: Maintain existing system during transition
3. **Rollback Capability**: Every change must be reversible
4. **Local-First**: Prioritize local execution over cloud dependencies
5. **Security-First**: Maintain or enhance security at each step

## Phase 0: Skeleton & Development UX

**Duration**: 3-5 days  
**Goal**: Establish new monorepo structure and development workflow

### Tasks
1. Create new directory structure alongside existing code
2. Set up monorepo tooling (workspace management)
3. Implement Makefile with dev commands
4. Configure pre-commit hooks
5. Create `infra/init.sh` for environment setup
6. Install and configure Ollama locally
7. Set up SQLite database initialization

### Deliverables
- `/apps/desktop/` (placeholder)
- `/apps/api/` (placeholder)
- `/apps/worker/` (placeholder)
- `/packages/*` (all package directories)
- `/infra/init.sh` (working script)
- `Makefile` with `make dev`, `make test`
- `.pre-commit-config.yaml`
- `.env.example` with new variables

### Success Criteria
- `./infra/init.sh` successfully sets up local environment
- Ollama installed and accessible
- SQLite database created
- Pre-commit hooks working

## Phase 1: Auth, Modes, Settings

**Duration**: 1 week  
**Goal**: Implement new authentication model and agent modes

### Tasks
1. Create FastAPI base for new `/apps/api`
2. Implement passphrase-based authentication (Argon2)
3. Add signed HTTP-only cookies
4. Implement CSRF protection
5. Add IP-based rate limiting
6. Create settings API for modes and preferences
7. Define Observe/Draft/Autopilot mode logic

### Deliverables
- `/apps/api/main.py` with auth endpoints
- `/apps/api/auth/` module with passphrase handling
- `/apps/api/settings/` module for user preferences
- `/packages/shared/models.py` with mode definitions
- Migration script for existing users (optional)

### Success Criteria
- Passphrase login working
- Modes can be set and retrieved
- Rate limiting prevents abuse
- CSRF protection active

## Phase 2: Memory & Vector Search

**Duration**: 1.5 weeks  
**Goal**: Implement SQLite-based memory with vector search

### Tasks
1. Design SQLite schema for conversations, tasks, insights
2. Implement sqlite-vec or SQLite-Vector integration
3. Create embedding pipeline with sentence-transformers
4. Build ingestion system for documents
5. Implement ANN search with MMR
6. Create memory API endpoints
7. Migrate existing pgvector data

### Deliverables
- `/packages/memory/schema.sql`
- `/packages/memory/embeddings.py`
- `/packages/memory/search.py`
- `/packages/memory/ingest.py`
- `/apps/api/memory/` endpoints
- Data migration scripts

### Success Criteria
- Documents can be ingested and embedded
- Vector search returns relevant results
- Search latency < 150ms for 1k chunks
- Existing data successfully migrated

## Phase 3: Plan DSL & Executor

**Duration**: 2 weeks  
**Goal**: Implement plans-as-code system with execution engine

### Tasks
1. Define Pydantic models for Plan/Step
2. Implement precondition/postcondition checking
3. Create rollback mechanism
4. Build idempotence tracking system
5. Implement dry-run simulator
6. Create plan storage and retrieval
7. Build basic plan executor in worker

### Deliverables
- `/packages/plan/models.py` (Plan, Step, Condition)
- `/packages/plan/simulator.py`
- `/packages/plan/executor.py`
- `/packages/plan/storage.py`
- `/apps/worker/planner.py`
- Plan examples and tests

### Success Criteria
- Plans can be defined in code
- Dry-run shows accurate diffs
- Rollback works on failure
- Idempotence prevents duplicate actions

## Phase 4: Code Interpreter (Local)

**Duration**: 1.5 weeks  
**Goal**: Enhanced sandboxed code execution with iterative refinement

### Tasks
1. Refactor existing exec-service into worker
2. Add iterative execution loop
3. Implement workspace file management
4. Add artifact packaging (zip)
5. Create execution context persistence
6. Add resource monitoring
7. Implement safety limits

### Deliverables
- `/apps/worker/interpreter/` module
- `/packages/tools/code_interpreter.py`
- Enhanced sandbox configuration
- Artifact storage system
- Example notebooks/scripts

### Success Criteria
- Code runs in isolated environment
- Files persist in workspace
- Iterative refinement works
- CSV→chart demo functional

## Phase 5: Web Automation

**Duration**: 1 week  
**Goal**: Enhanced Playwright automation with MCP server

### Tasks
1. Refactor webbot-service into package
2. Implement resilient selector strategies
3. Add retry/backoff logic
4. Create session persistence
5. Build MCP server adapter
6. Implement structured page state
7. Enhance audit logging

### Deliverables
- `/packages/automation/playwright_driver.py`
- `/packages/automation/mcp_server.py`
- `/packages/automation/selectors.py`
- Enhanced action definitions
- MCP protocol implementation

### Success Criteria
- Form filling demo works reliably
- MCP server provides structured state
- Sessions persist across runs
- Retries handle transient failures

## Phase 6: LLM Router & Budgets

**Duration**: 1.5 weeks  
**Goal**: Implement intelligent LLM routing with budget management

### Tasks
1. Create Ollama integration
2. Build OpenAI adapter
3. Build Anthropic adapter
4. Build Gemini adapter
5. Implement routing logic
6. Add token counting
7. Create budget tracking
8. Implement circuit breakers

### Deliverables
- `/packages/llm/router.py`
- `/packages/llm/providers/` (ollama, openai, etc.)
- `/packages/llm/budgets.py`
- `/packages/llm/tokenizer.py`
- Configuration system
- Usage tracking database

### Success Criteria
- Local Ollama works by default
- Fallback to cloud providers works
- Budgets enforced (tokens/time)
- Circuit breaker prevents runaway costs

## Phase 7: Flow Builder (MVP)

**Duration**: 2 weeks  
**Goal**: Visual flow builder with natural language compilation

### Tasks
1. Design flow node types (Search, Generate, Automate)
2. Create React flow builder UI
3. Implement drag-and-drop interface
4. Build NL→flow compiler
5. Create flow→plan converter
6. Add preview functionality
7. Implement flow persistence

### Deliverables
- `/apps/desktop/src/components/FlowBuilder/`
- `/packages/flows/compiler.py`
- `/packages/flows/models.py`
- Flow serialization format
- Example flows

### Success Criteria
- Three node types working
- Drag-drop creates valid flows
- NL description generates flow
- Flows compile to executable plans

## Phase 8: Observability & Golden Path

**Duration**: 1.5 weeks  
**Goal**: Polish, monitoring, and complete example workflow

### Tasks
1. Create unified dashboard
2. Implement TSR/FAP metrics
3. Add intervention tracking
4. Build weekly report generator
5. Implement job application workflow
6. Add comprehensive logging
7. Create user documentation

### Deliverables
- `/apps/desktop/src/pages/Dashboard/`
- `/packages/metrics/` module
- `/docs/user-guide.md`
- `/docs/runbook.md`
- Golden path implementation
- Weekly report template

### Success Criteria
- Dashboard shows key metrics
- Job application demo works E2E
- Weekly report generates
- Documentation complete

## Migration Timeline

```
Week 1:  Phase 0 (3d) + Phase 1 start
Week 2:  Phase 1 complete
Week 3:  Phase 2
Week 4:  Phase 2 complete + Phase 3 start
Week 5:  Phase 3
Week 6:  Phase 3 complete + Phase 4 start
Week 7:  Phase 4 complete + Phase 5
Week 8:  Phase 6
Week 9:  Phase 6 complete + Phase 7 start
Week 10: Phase 7
Week 11: Phase 7 complete + Phase 8
Week 12: Phase 8 complete + Testing/Polish
```

## Risk Mitigation

### Technical Risks
1. **Vector DB Performance**: Test both sqlite-vec and SQLite-Vector early
2. **LLM Latency**: Implement aggressive caching
3. **Desktop Packaging**: Prototype Tauri/Electron in Phase 0

### Data Risks
1. **Migration Failures**: Keep full backups before each phase
2. **Schema Changes**: Use versioned migrations
3. **User Data**: Implement export/import functionality

### Rollback Strategy
- Each phase tagged in git
- Database migrations reversible
- Feature flags for new functionality
- Old system remains operational

## Success Metrics

1. **Phase 0-2**: Dev environment setup, new auth working
2. **Phase 3-4**: Plans execute successfully, code interpreter functional
3. **Phase 5-6**: Automation reliable, LLM routing efficient
4. **Phase 7-8**: UI intuitive, golden path demonstrates value

## Post-Migration

1. **Deprecation Timeline**: 30 days after Phase 8
2. **Data Retention**: Keep old system data for 90 days
3. **Support Transition**: Documentation and training
4. **Performance Optimization**: Based on real usage

## Conclusion

This phased approach minimizes risk while delivering incremental value. Each phase builds on the previous, with clear success criteria and rollback options. The 12-week timeline is aggressive but achievable with focused effort.