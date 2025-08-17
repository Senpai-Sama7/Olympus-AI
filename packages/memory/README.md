# Memory Package

SQLite-based memory system with vector search capabilities.

## Overview

This package provides:
- SQLite schema for conversations, documents, and embeddings
- Vector index using sqlite-vec or SQLite-Vector
- Local embeddings with sentence-transformers
- ANN search with MMR (Maximal Marginal Relevance)
- Document ingestion pipeline

## Components

### Schema
- Conversations and messages
- Documents and chunks
- Embeddings and metadata
- Tasks and insights

### Embeddings
- Local sentence-transformers models
- Batch processing
- Incremental updates

### Search
- Vector similarity search
- Hybrid search (vector + keyword)
- MMR for diversity
- Faceted filtering

## Phase 2 Implementation

See `/plans/migration-plan.md` for implementation timeline.