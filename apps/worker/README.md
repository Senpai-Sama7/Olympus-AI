# Agent Worker

Python async daemon for executing plans, tools, and automation.

## Overview

This directory will contain the worker service that handles:
- Plan execution
- Code Interpreter (sandboxed Python)
- Tool orchestration
- Web automation via Playwright
- Resource management

## Structure (to be implemented)

```
worker/
├── main.py              # Worker entry point
├── planner.py           # Plan executor
├── interpreter/         # Code Interpreter module
├── tools/               # Tool implementations
├── automation/          # Playwright automation
├── sandbox/             # Sandboxing utilities
└── utils/               # Utilities
```

## Phase 3-4 Implementation

The worker will be built in phases:
- Phase 3: Plan executor
- Phase 4: Code Interpreter
- Phase 5: Web automation integration

See `/plans/migration-plan.md` for details.