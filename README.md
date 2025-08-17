# Olympus AI

Olympus AI is a sophisticated AI assistant designed to be a powerful and flexible tool for a wide range of tasks. It is built with a modular architecture that allows for easy extension and customization.

## Architecture

The architecture of Olympus AI is described in detail in the [ARCHITECTURE.md](ARCHITECTURE.md) file.

## Getting Started

### Prerequisites

- Docker
- Docker Compose
- Python 3.11+
- Node.js (for the client)

### Installation

1.  Clone the repository:

    ```bash
    git clone https://github.com/your-username/olympus-ai.git
    cd olympus-ai
    ```

2.  Install the Python dependencies:

    ```bash
    pip install -r requirements-dev.txt
    ```

3.  Install the client dependencies:

    ```bash
    cd client
    npm install
    cd ..
    ```

### Running the Application

1.  Start the infrastructure services (PostgreSQL, Redis, etc.):

    ```bash
    docker-compose -f docker-compose.infra.yml up -d
    ```

2.  Run the database migrations:

    ```bash
    python -m olympus_memory.db
    ```

3.  Start the backend services:

    ```bash
    # Start the API service
    uvicorn olympus_api.main:app --host 0.0.0.0 --port 8000 &

    # Start the worker service
    python -m olympus_worker.main &

    # Start the retrieval service
    uvicorn services.retrieval.app.main:app --host 0.0.0.0 --port 8001 &
    ```

4.  Start the client:

    ```bash
    cd client
    npm run dev
    ```

5.  Start the desktop app:

    ```bash
    python desktop/app/main.py
    ```

## Services

-   **`apps/api`**: The main API for interacting with the assistant.
-   **`apps/worker`**: The worker that executes plans.
-   **`services/retrieval`**: The service that provides retrieval and search functionality.

## Packages

-   **`packages/plan`**: Contains the models for plans and steps.
-   **`packages/memory`**: Provides the memory stack for the assistant.
-   **`packages/llm`**: The LLM router for interacting with language models.
-   **`packages/tools`**: Contains the tools that the assistant can use.