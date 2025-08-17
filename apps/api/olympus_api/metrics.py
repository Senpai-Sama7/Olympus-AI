from fastapi import APIRouter, Response
from prometheus_client import REGISTRY, Counter, Gauge, Histogram, exposition

try:
    from olympus_worker.health import read_last_heartbeat
except Exception:  # pragma: no cover
    read_last_heartbeat = None

requests_total = Counter(
    "requests_total", "Total HTTP requests", ["path", "method", "status"]
)
request_duration_seconds = Histogram(
    "request_duration_seconds", "Request duration", ["path", "method", "status"]
)
worker_heartbeat_timestamp = Gauge(
    "worker_heartbeat_timestamp", "Last worker heartbeat timestamp (unix seconds)"
)

router = APIRouter()


@router.get("/metrics")
async def metrics() -> Response:
    if read_last_heartbeat is not None:
        try:
            last = read_last_heartbeat()
            if last is not None:
                worker_heartbeat_timestamp.set(last.timestamp())
        except Exception:
            pass
    # Expose Prometheus text format
    data = exposition.generate_latest(REGISTRY)
    return Response(content=data, media_type=exposition.CONTENT_TYPE_LATEST)
