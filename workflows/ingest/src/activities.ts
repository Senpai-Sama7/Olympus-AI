import { Pool } from 'pg';
import { embed } from './embed.js';

const dsn = process.env.POSTGRES_DSN || 'postgresql://postgres:postgres@cp-postgres:5432/cognitive';
const pool = new Pool({ connectionString: dsn });

export async function fetchDocs(sourceId: string): Promise<{id:number,title:string,body:string}[]> {
  const client = await pool.connect();
  try {
    const res = await client.query('SELECT id, title, body FROM raw_docs WHERE source_id=$1 AND embedded=false', [sourceId]);
    return res.rows;
  } finally {
    client.release();
  }
}

export async function chunk(doc: {id:number,title:string,body:string}) {
  const maxLen = 500;
  const sentences = doc.body.split(/(?<=[.!?])\s+/);
  const chunks: {doc_id:number,chunk_no:number,text:string}[] = [];
  let current = '';
  let no = 0;
  for (const s of sentences) {
    if ((current + ' ' + s).trim().length > maxLen && current.length > 0) {
      chunks.push({ doc_id: doc.id, chunk_no: no++, text: current.trim() });
      current = s;
    } else {
      current = (current ? current + ' ' : '') + s;
    }
  }
  if (current.trim().length > 0) {
    chunks.push({ doc_id: doc.id, chunk_no: no++, text: current.trim() });
  }
  return chunks;
}

export async function embedBatch(texts: string[]): Promise<number[][]> {
  return texts.map(t => embed(t));
}

export async function upsert(chunks: {doc_id:number,chunk_no:number,text:string}[], vectors: number[][]) {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    for (let i=0; i<chunks.length; i++) {
      const c = chunks[i];
      const v = vectors[i];
      await client.query(
        'INSERT INTO doc_chunks (doc_id, chunk_no, text, embedding) VALUES ($1,$2,$3,$4::vector)',
        [c.doc_id, c.chunk_no, c.text, v]
      );
    }
    await client.query('UPDATE raw_docs SET embedded=true WHERE id=ANY($1::bigint[])', [chunks.map(c=>c.doc_id)]);
    await client.query('COMMIT');
  } catch (e) {
    await client.query('ROLLBACK');
    throw e;
  } finally {
    client.release();
  }
}
