import Redis from 'ioredis';
import { Connection, Client } from '@temporalio/client';

const redisUrl = process.env.REDIS_URL || 'redis://cp-redis:6379';
const temporalAddress = process.env.TEMPORAL_ADDRESS || 'cp-temporal:7233';
const namespace = process.env.TEMPORAL_NAMESPACE || 'default';

const stream = 'ingest:requests';
const group = 'orchestrators';
const consumer = 'bridge-' + Math.random().toString(36).slice(2,8);

async function ensureGroup(r) {
  try {
    await r.xgroup('CREATE', stream, group, '0', 'MKSTREAM');
  } catch (e) {
    if (!String(e).includes('BUSYGROUP')) throw e;
  }
}

function fieldsToMap(arr) {
  const m = {};
  for (let i=0; i<arr.length; i+=2) m[String(arr[i])] = String(arr[i+1]);
  return m;
}

async function run() {
  const r = new Redis(redisUrl);
  await ensureGroup(r);
  const connection = await Connection.connect({ address: temporalAddress });
  const client = new Client({ connection, namespace });

  console.log('ingest-bridge ready. stream=%s group=%s consumer=%s', stream, group, consumer);
  while (true) {
    const res = await r.xreadgroup('GROUP', group, consumer, 'BLOCK', 5000, 'COUNT', 10, 'STREAMS', stream, '>');
    if (!res) continue;
    for (const [sname, entries] of res) {
      for (const [id, kv] of entries) {
        const map = fieldsToMap(kv);
        const wf = map['wf'] || 'unknown';
        const sourceId = map['source_id'] || 'demo';
        try {
          const handle = await client.workflow.start('ingestWorkflow', {
            taskQueue: 'ingest',
            args: [{ sourceId }],
            workflowId: wf,
          });
          await r.xadd('tasks:events', '*', 'wf', wf, 'phase', 'started', 'note', `ingest started source_id=${sourceId}`);
          const result = await handle.result();
          await r.xadd('tasks:events', '*', 'wf', wf, 'phase', 'completed', 'note', `ingest done processed=${result.processed}`);
          await r.xack(stream, group, id);
        } catch (e) {
          await r.xadd('tasks:events', '*', 'wf', wf, 'phase', 'error', 'note', String(e));
        }
      }
    }
  }
}

run().catch(e => { console.error(e); process.exit(1); });
