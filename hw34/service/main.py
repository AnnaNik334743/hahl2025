from datetime import datetime
import time
from fastapi import FastAPI, Request, Response
import uvicorn
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY


REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP Requests (excluding /metrics)',
    ['method', 'endpoint', 'status_code']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP Request latency in seconds (excluding /metrics)',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

LAST_REQUEST_TIMESTAMP = Gauge(
    'http_last_request_timestamp',
    'Unix timestamp of the last request (excluding /metrics)',
    ['method', 'endpoint']
)


app = FastAPI(
    title="DateTime Service", 
    description="Service that provides current date and time information"
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    endpoint = request.url.path
    method = request.method
    start_time = time.time()

    response = await call_next(request)

    if endpoint != "/metrics":
        duration = time.time() - start_time
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
        LAST_REQUEST_TIMESTAMP.labels(method=method, endpoint=endpoint).set(time.time())
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=response.status_code).inc()

    return response


@app.get("/")
def root():
    return {
        "message": "DateTime Service is running",
        "endpoints": {
            "/": "This info",
            "/date": "Current date information",
            "/time": "Current time information",
            "/datetime": "Complete datetime info",
            "/metrics": "Prometheus metrics (for monitoring)"
        }
    }


@app.get("/datetime")
def get_datetime():
    now = datetime.now()
    current_time = time.time()
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "year": now.year,
        "month": now.month,
        "month_name": now.strftime("%B"),
        "day": now.day,
        "day_of_week": now.strftime("%A"),
        "day_of_year": now.strftime("%j"),
        "hour": now.hour,
        "minute": now.minute,
        "second": now.second,
        "microsecond": now.microsecond,
        "unix_timestamp": int(current_time),
        "unix_timestamp_ms": int(current_time * 1000),
        "iso_format": now.isoformat(),
        "timezone": now.astimezone().tzname()
    }


@app.get("/date")
def get_date():
    now = datetime.now()
    return {
        "date": now.strftime("%Y-%m-%d"),
        "year": now.year,
        "month": now.month,
        "month_name": now.strftime("%B"),
        "day": now.day,
        "day_of_week": now.strftime("%A"),
        "day_of_year": now.strftime("%j"),
        "is_leap_year": now.year % 4 == 0 and (now.year % 100 != 0 or now.year % 400 == 0),
        "week_number": now.strftime("%U"),
        "iso_date": now.date().isoformat()
    }


@app.get("/time")
def get_time():
    now = datetime.now()
    return {
        "time": now.strftime("%H:%M:%S"),
        "hour": now.hour,
        "minute": now.minute,
        "second": now.second,
        "microsecond": now.microsecond,
        "hour_12": now.strftime("%I"),
        "am_pm": now.strftime("%p"),
        "timezone": now.astimezone().tzname(),
        "iso_time": now.time().isoformat(),
        "utc_offset": now.astimezone().utcoffset().total_seconds() / 3600 if now.astimezone().utcoffset() else 0
    }


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(REGISTRY), media_type="text/plain")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)