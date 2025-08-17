# API Server

FastAPI-based backend for the local-first agentic assistant.

## Overview

This directory will contain the main API server that handles:
- Authentication (passphrase-based)
- Agent communication
- Memory management
- Task orchestration
- Settings and preferences

## Structure (to be implemented)

```
api/
├── main.py              # FastAPI app entry point
├── auth/                # Authentication module
├── memory/              # Memory API endpoints
├── agents/              # Agent interaction endpoints
├── settings/            # User settings management
├── models/              # Pydantic models
├── middleware/          # Security, CORS, etc.
└── utils/               # Utilities
```

## Phase 1 Implementation

In Phase 1, we will implement:
- Basic FastAPI structure
- Passphrase authentication with Argon2
- HTTP-only signed cookies
- CSRF protection
- IP-based rate limiting
- Settings API for modes

See `/plans/migration-plan.md` for details.