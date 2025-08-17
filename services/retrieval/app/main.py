from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import asyncpg
from .embed import embed
from .ingest import ingest_facts
from olympus_api.logging import configure_json_logging, JsonRequestLogger

configure_json_logging(component="retrieval-service", level=os.environ.get("LOG_LEVEL", "INFO"))

app = FastAPI(title="Retrieval Service", version="1.0.0")
app.add_middleware(JsonRequestLogger, component="retrieval-service")

DSN = os.environ.get(
    "POSTGRES_DSN", "postgresql://postgres:postgres@cp-postgres:5432/cognitive"
)


class SearchRequest(BaseModel):
    query: str
    k: int = 5


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/v1/retrieval/ingest")
async def ingest():
    await ingest_facts(DSN)
    return {"status": "ingestion complete"}


@app.post("/v1/retrieval/search")
async def search(req: SearchRequest):
    if req.k <= 0 or req.k > 1000:
        raise HTTPException(400, "k must be 1..1000")
    qvec = embed(req.query)
    conn = await asyncpg.connect(DSN)
    try:
        rows = await conn.fetch(
            """
            SELECT f.source, f.content,
                   (e.vector <-> $1::vector) AS distance
            FROM embeddings e
            JOIN facts f ON f.id = e.fact_id
            ORDER BY e.vector <-> $1::vector
            LIMIT $2;
            """,
            qvec,
            req.k,
        )
        results = [
            {
                "source": r["source"],
                "content": r["content"],
                "distance": float(r["distance"]),
            }
            for r in rows
        ]
        return {"k": req.k, "results": results}
    finally:
        await conn.close()
