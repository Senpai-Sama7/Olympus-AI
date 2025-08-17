# Plan Package

Plans-as-code DSL for defining executable workflows with rollback support.

## Overview

This package provides:
- Pydantic models for Plans and Steps
- Precondition/postcondition checking
- Rollback mechanisms
- Idempotence tracking
- Dry-run simulator showing diffs

## Core Concepts

### Plan Structure
```python
Plan:
  - id: unique identifier
  - goal: human-readable description
  - steps: ordered list of Steps
  - mode: execution mode (observe/draft/autopilot)
  - budget: resource limits

Step:
  - id: unique step identifier
  - inputs: required parameters
  - preconditions: list of checks before execution
  - action: tool invocation details
  - postconditions: expected state after execution
  - rollback: compensation action if needed
  - idempotence_key: prevents duplicate execution
```

## Phase 3 Implementation

See `/plans/migration-plan.md` for implementation timeline.