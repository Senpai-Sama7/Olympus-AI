use std::pin::Pin;
use std::time::{SystemTime, UNIX_EPOCH};
use tonic::{transport::Server, Request, Response, Status};
use tokio_stream::{wrappers::ReceiverStream, Stream};
use tracing::{info, Level};
use uuid::Uuid;
use redis::AsyncCommands;
use serde::Deserialize;

pub mod pb {
    tonic::include_proto!("cognitive.v1");
}
use pb::task_service_server::{TaskService, TaskServiceServer};
use pb::{SubmitTaskRequest, SubmitTaskResponse, GetTaskResultRequest, TaskResult, TaskEventsRequest, TaskEvent};

#[derive(Default)]
pub struct TaskSvc;

type EventStream = Pin<Box<dyn Stream<Item = Result<TaskEvent, Status>> + Send + 'static>>;

#[derive(Deserialize)]
struct IngestPayload { source_id: String }

#[tonic::async_trait]
impl TaskService for TaskSvc {
    async fn submit_task(
        &self,
        req: Request<SubmitTaskRequest>,
    ) -> Result<Response<SubmitTaskResponse>, Status> {
        let r = req.into_inner();
        let wf = Uuid::new_v4().to_string();
        let task_type = r.task_type.to_lowercase();

        let redis_url = std::env::var("REDIS_URL").unwrap_or("redis://cp-redis:6379".into());
        let client = redis::Client::open(redis_url).map_err(to_status)?;
        let mut conn = client.get_async_connection().await.map_err(to_status)?;

        match task_type.as_str() {
            "ingest" => {
                let p: IngestPayload = serde_json::from_slice(&r.payload)
                    .map_err(|e| Status::invalid_argument(format!("bad payload: {}", e)))?;

                let _: String = redis::cmd("XADD")
                    .arg("ingest:requests").arg("*")
                    .arg("wf").arg(&wf)
                    .arg("source_id").arg(&p.source_id)
                    .query_async(&mut conn).await.map_err(to_status)?;

                let _: String = redis::cmd("XADD")
                    .arg("tasks:events").arg("*")
                    .arg("wf").arg(&wf)
                    .arg("phase").arg("submitted")
                    .arg("note").arg(format!("ingest request for source_id={}", p.source_id))
                    .query_async(&mut conn).await.map_err(to_status)?;

                Ok(Response::new(SubmitTaskResponse { workflow_id: wf }))
            },
            other => Err(Status::invalid_argument(format!("unknown task_type {}", other)))
        }
    }

    async fn get_task_result(
        &self,
        req: Request<GetTaskResultRequest>,
    ) -> Result<Response<TaskResult>, Status> {
        let id = req.into_inner().workflow_id;
        let msg = format!("Results stream via events for workflow_id={}", id);
        Ok(Response::new(TaskResult { status: "SEE_EVENTS".into(), data: msg.into_bytes(), error: "".into() }))
    }

    type StreamTaskEventsStream = EventStream;
    async fn stream_task_events(
        &self,
        req: Request<TaskEventsRequest>,
    ) -> Result<Response<Self::StreamTaskEventsStream>, Status> {
        let wf = req.into_inner().workflow_id;
        let (tx, rx) = tokio::sync::mpsc::channel(32);
        let redis_url = std::env::var("REDIS_URL").unwrap_or("redis://cp-redis:6379".into());
        tokio::spawn(async move {
            let client = match redis::Client::open(redis_url) { Ok(c)=>c, Err(_)=>return };
            let mut conn = match client.get_async_connection().await { Ok(c)=>c, Err(_)=>return };

            let mut last_id = "0-0".to_string();
            loop {
                let res: redis::RedisResult<redis::Value> = redis::cmd("XREAD")
                    .arg("BLOCK").arg(5000)
                    .arg("COUNT").arg(50)
                    .arg("STREAMS").arg("tasks:events").arg(&last_id)
                    .query_async(&mut conn).await;

                if let Ok(redis::Value::Bulk(values)) = res {
                    for v in values {
                        if let redis::Value::Bulk(streams) = v {
                            if streams.len() < 2 { continue; }
                            if let (redis::Value::Data(_name), redis::Value::Bulk(entries)) = (&streams[0], &streams[1]) {
                                for entry in entries {
                                    if let redis::Value::Bulk(entry_parts) = entry {
                                        if entry_parts.len() != 2 { continue; }
                                        let id = match &entry_parts[0] { redis::Value::Data(b) => String::from_utf8_lossy(b).into_owned(), _=>continue };
                                        let fields = &entry_parts[1];
                                        let mut wf_field = String::new();
                                        let mut phase = String::new();
                                        let mut note = String::new();
                                        if let redis::Value::Bulk(kvs) = fields {
                                            let mut it = kvs.iter();
                                            while let (Some(k), Some(val)) = (it.next(), it.next()) {
                                                let key = match k { redis::Value::Data(b) => String::from_utf8_lossy(b).into_owned(), _=>String::new() };
                                                let value = match val { redis::Value::Data(b) => String::from_utf8_lossy(b).into_owned(), _=>String::new() };
                                                match key.as_str() {
                                                    "wf" => wf_field = value,
                                                    "phase" => phase = value,
                                                    "note" => note = value,
                                                    _ => {}
                                                }
                                            }
                                        }
                                        last_id = id.clone();
                                        if wf_field == wf {
                                            let _ = tx.send(Ok(TaskEvent {
                                                at: now_string(),
                                                phase,
                                                note,
                                            })).await;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        });

        Ok(Response::new(Box::pin(ReceiverStream::new(rx))))
    }
}

fn now_string() -> String {
    let ms = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_millis();
    format!("{}", ms)
}

fn to_status<E: std::fmt::Display>(e: E) -> Status { Status::internal(e.to_string()) }

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt()
        .with_max_level(Level::INFO)
        .with_env_filter("info")
        .init();

    let addr = "0.0.0.0:50051".parse()?;
    let svc = TaskSvc::default();
    info!("control-plane listening on {}", addr);
    Server::builder()
        .add_service(TaskServiceServer::new(svc))
        .serve(addr)
        .await?;
    Ok(())
}
