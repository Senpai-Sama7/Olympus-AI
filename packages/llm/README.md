# LLM Package

Intelligent LLM routing with local-first approach and cloud fallback.

## Overview

This package provides:
- Local LLM integration (Ollama)
- Cloud provider adapters (OpenAI, Anthropic, Gemini)
- Intelligent routing based on complexity/confidence
- Token and time budget management
- Circuit breakers and graceful degradation

## Components

### Providers
- `ollama.py` - Local Ollama integration
- `openai.py` - OpenAI API adapter
- `anthropic.py` - Anthropic Claude adapter
- `gemini.py` - Google Gemini adapter

### Router
- Complexity detection
- Provider selection logic
- Fallback chains
- Load balancing

### Budget Management
- Token counting and limits
- Time tracking
- Cost estimation
- Usage analytics

## Configuration

```python
router = LLMRouter(
    default_provider="ollama",
    fallback_chain=["ollama", "openai", "anthropic"],
    daily_token_budget=10000,
    per_task_limit=1000
)
```

## Phase 6 Implementation

See `/plans/migration-plan.md` for implementation timeline.