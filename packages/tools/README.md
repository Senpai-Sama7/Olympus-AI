# Tools Package

Secure, extensible tools for file I/O, HTTP, and external integrations.

## Overview

This package provides:
- File I/O with allow-listed directories
- HTTP client with domain restrictions
- Email, calendar, and sheets connectors
- JSON Schema contracts for all tools
- Comprehensive audit logging

## Tool Categories

### File System
- Read/write with path validation
- Directory operations
- Archive creation/extraction
- Metadata operations

### Network
- HTTP/HTTPS requests
- Domain allow-listing
- Request/response validation
- Retry and timeout handling

### External Services
- Email (SMTP/IMAP)
- Calendar (CalDAV/Google)
- Spreadsheets (Google Sheets, Excel)
- Cloud storage (S3-compatible)

## Security Model

All tools enforce:
- Allow-listed paths/domains
- Size and rate limits
- Input validation
- Audit trails
- Confirmation for sensitive operations

## Phase 4-5 Implementation

Tools will be implemented alongside Code Interpreter and automation features.