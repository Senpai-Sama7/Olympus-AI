# Architecture

Olympus AI is built with a modular, service-oriented architecture. This allows for flexibility, scalability, and easy development of new features.

## System Overview

The system is composed of several services and packages that work together to provide the assistant's functionality.

```
+-----------------+      +-----------------+      +-----------------+
|   Desktop App   |----->|      API        |----->|      Worker     |
+-----------------+      +-----------------+      +-----------------+
        |                      |                      |
        |                      |                      v
        |                      |              +-----------------+
        |                      |              |      Tools      |
        |                      |              +-----------------+
        |                      |
        |                      v
        |              +-----------------+
        |              |   LLM Router    |
        |              +-----------------+
        |
        v
+-----------------+
|     Memory      |
+-----------------+
        |
        v
+-----------------+
|    Retrieval    |
+-----------------+
```

## Components

### Services

-   **`apps/api`**: The main entry point for interacting with the assistant. It exposes a REST API for submitting plans, checking their status, and performing actions. It also handles user authentication and consent management.
-   **`apps/worker`**: This service is responsible for executing plans. It subscribes to a queue of plans and executes them one by one. It uses the tool adapter to interact with the different tools.
-   **`services/retrieval`**: This service provides retrieval and search functionality. It uses a PostgreSQL database with the pgvector extension to store and search for embeddings.

### Packages

-   **`packages/plan`**: This package contains the data models for plans and steps. A plan is a sequence of steps that the assistant needs to execute to achieve a goal.
-   **`packages/memory`**: This package provides the memory stack for the assistant. It includes schemas for events, facts, embeddings, entities, and relations. It also includes a migration system for managing the database schema.
-   **`packages/llm`**: This package contains the LLM router, which is responsible for interacting with large language models. It supports multiple providers, budget management, and caching.
-   **`packages/tools`**: This package contains the tools that the assistant can use to interact with the outside world. It includes tools for file system operations, network requests, and code execution. It also includes a consent management system to ensure that the user has given their permission before performing any sensitive operations.

### Desktop App

The desktop app is the main user interface for interacting with the assistant. It is built with `pywebview`, which allows for a cross-platform UI built with web technologies. The desktop app provides a way to manage settings, view the task queue, and see the artifacts produced by the assistant. It also provides the consent prompts for the "ask-before-doing" gate.