import { NativeConnection, Worker } from '@temporalio/worker';

async function run() {
  const address = process.env.TEMPORAL_ADDRESS || 'cp-temporal:7233';
  const namespace = process.env.TEMPORAL_NAMESPACE || 'default';
  const connection = await NativeConnection.connect({ address });
  const worker = await Worker.create({
    connection,
    namespace,
    taskQueue: 'ingest',
    workflowsPath: require.resolve('./workflows.js'),
    activities: require('./activities.js'),
  });
  await worker.run();
}

run().catch((err) => { console.error(err); process.exit(1); });
