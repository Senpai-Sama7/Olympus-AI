import asyncpg
from .embed import embed

async def ingest_facts(dsn: str):
    conn = await asyncpg.connect(dsn)
    try:
        facts = await conn.fetch("SELECT id, content FROM facts")
        for fact in facts:
            embedding = embed(fact['content'])
            await conn.execute(
                """
                INSERT INTO embeddings (id, fact_id, vector, model)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (id) DO NOTHING
                """,
                f"emb_{fact['id']}",
                fact['id'],
                embedding,
                "text-embedding-ada-002"  # Replace with actual model name
            )
    finally:
        await conn.close()
