import { proxyActivities } from '@temporalio/workflow';
const { fetchDocs, chunk, embedBatch, upsert } = proxyActivities<{
  fetchDocs(sourceId: string): Promise<{id:number,title:string,body:string}[]>,
  chunk(doc: {id:number,title:string,body:string}): Promise<{doc_id:number, chunk_no:number, text:string}[]>,
  embedBatch(texts: string[]): Promise<number[][]>,
  upsert(chunks: {doc_id:number,chunk_no:number,text:string}[], vectors: number[][]): Promise<void>,
}>({ startToCloseTimeout: '10 minutes' });

export async function ingestWorkflow({ sourceId }: { sourceId: string }) {
  const docs = await fetchDocs(sourceId);
  for (const doc of docs) {
    const chunks = await chunk(doc);
    const vectors = await embedBatch(chunks.map(c => c.text));
    await upsert(chunks, vectors);
  }
  return { processed: docs.length };
}
