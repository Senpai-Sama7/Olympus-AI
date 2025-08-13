CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS raw_docs (
  id BIGSERIAL PRIMARY KEY,
  source_id TEXT NOT NULL,
  title TEXT,
  body TEXT NOT NULL,
  embedded BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS doc_chunks (
  id BIGSERIAL PRIMARY KEY,
  doc_id BIGINT REFERENCES raw_docs(id) ON DELETE CASCADE,
  chunk_no INT,
  text TEXT,
  embedding vector(768)
);

DROP INDEX IF EXISTS doc_chunks_embedding_hnsw;
CREATE INDEX doc_chunks_embedding_hnsw
  ON doc_chunks USING hnsw (embedding vector_cosine_ops)
  WITH (m = 24, ef_construction = 200);
