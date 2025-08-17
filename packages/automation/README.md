# Automation Package

Playwright-based web automation with MCP server support.

## Overview

This package provides:
- Resilient web automation with Playwright
- Smart selector strategies
- Retry and backoff mechanisms
- Session persistence
- MCP (Model Context Protocol) server
- Structured page state extraction

## Components

### Playwright Driver
- Headless browser automation
- Multiple browser support
- Cookie and storage management
- Screenshot and PDF generation
- Download/upload handling

### Resilient Selectors
- Multiple fallback strategies
- Visual recognition fallback
- Semantic selector generation
- Auto-healing selectors

### MCP Server
- LLM-friendly page state
- Structured action interface
- Context preservation
- Error recovery suggestions

## Usage Example

```python
from packages.automation import WebAutomation

automation = WebAutomation()
result = await automation.execute([
    {"type": "goto", "url": "https://example.com"},
    {"type": "fill", "selector": "#email", "value": "user@example.com"},
    {"type": "click", "selector": "button[type=submit]"},
    {"type": "extract", "selector": ".result"}
])
```

## Phase 5 Implementation

See `/plans/migration-plan.md` for implementation timeline.