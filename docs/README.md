# Documentation

Welcome to the Local-First Agentic Assistant documentation.

## Quick Links

- [Migration Plan](/plans/migration-plan.md) - Phased approach to transform the system
- [Repository Audit](/reports/repo-audit.md) - Analysis of existing codebase
- [Gap Analysis](/reports/gap-analysis.md) - What needs to change
- [User Guide](User-Guide.md) - End-user documentation

## Architecture Documents

- [Original Architecture](../ARCHITECTURE.md) - Current system design
- [Target Architecture](/plans/migration-plan.md#architecture) - Where we're going

## Development Guides

### Getting Started
1. Clone the repository
2. Copy `.env.example` to `.env` and configure
3. Run `./infra/init.sh` to set up environment
4. Run `make dev` to start development

### Package Documentation
- [Plan DSL](/packages/plan/README.md) - Workflow definition
- [Memory System](/packages/memory/README.md) - Vector search and storage
- [LLM Router](/packages/llm/README.md) - Model management
- [Tools](/packages/tools/README.md) - Extensible tool system
- [Automation](/packages/automation/README.md) - Web automation

### Application Documentation
- [API Server](/apps/api/README.md) - Backend services
- [Worker](/apps/worker/README.md) - Task execution
- [Desktop App](/apps/desktop/README.md) - User interface

## Security & Compliance

- Passphrase-based authentication
- Allow-listed directories and domains
- Comprehensive audit logging
- Local-first data storage

## Contributing

See `.pre-commit-config.yaml` for code style and quality standards.