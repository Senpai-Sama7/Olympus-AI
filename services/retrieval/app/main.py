from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os, asyncpg
from .embed import embed

app = FastAPI(title="Retrieval Service", version="1.0.0")
DSN = os.environ.get("POSTGRES_DSN", "postgresql://postgres:postgres@cp-postgres:5432/cognitive")

class SearchRequest(BaseModel):
    query: str
    k: int = 5

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/v1/retrieval/search")
async def search(req: SearchRequest):
    if req.k <= 0 or req.k > 1000:
        raise HTTPException(400, "k must be 1..1000")
    qvec = embed(req.query)
    conn = await asyncpg.connect(DSN)
    try:
        rows = await conn.fetch(
            """
            SELECT d.title, c.doc_id, c.chunk_no, c.text,
                   (c.embedding <-> $1::vector) AS distance
            FROM doc_chunks c
            JOIN raw_docs d ON d.id = c.doc_id
            ORDER BY c.embedding <-> $1::vector
            LIMIT $2;
            """,
            qvec, req.k
        )
        results = [{
            "title": r["title"],
            "doc_id": r["doc_id"],
            "chunk_no": r["chunk_no"],
            "text": r["text"],
            "distance": float(r["distance"]),
        } for r in rows]
        return {"k": req.k, "results": results}
    finally:
        await conn.close()
