from datetime import datetime
import time
from fastapi import FastAPI, Request, Response, HTTPException
import uvicorn
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
import asyncpg
import redis.asyncio as redis
from typing import List, Optional, Dict, Any
import json
import os
import re


REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP Requests (excluding /metrics)',
    ['method', 'endpoint', 'status_code']
)

SUCCESS_REQUEST_COUNT = Counter(
    'http_requests_success_total',
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

CACHE_HITS = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)


app = FastAPI(
    title="DateTime Service", 
    description="Service that provides current date, time, and holiday information"
)

db_pool: Optional[asyncpg.Pool] = None
redis_client: Optional[redis.Redis] = None


@app.on_event("startup")
async def startup():
    global db_pool, redis_client
    
    db_pool = await asyncpg.create_pool(
        dsn=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/holidays_db"),
        min_size=10,
        max_size=200,
        max_inactive_connection_lifetime=60,
        timeout=60,
        max_queries=50000,
        max_cached_statement_lifetime=0,
    )

    redis_client = redis.Redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True
    )


@app.on_event("shutdown")
async def shutdown():
    if db_pool:
        await db_pool.close()
    if redis_client:
        await redis_client.close()


def normalize_endpoint_for_metrics(endpoint: str) -> str:
    normalized = re.sub(r'/\d+', '', endpoint)
    if normalized.endswith('/') and len(normalized) > 1:
        normalized = normalized.rstrip('/')
    return normalized or '/'


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    endpoint = request.url.path
    normalized_endpoint = normalize_endpoint_for_metrics(endpoint)
    method = request.method
    start_time = time.time()

    if endpoint != "/metrics":
        REQUEST_COUNT.labels(method=method, endpoint=normalized_endpoint, status_code=None).inc()

    response = await call_next(request)

    if endpoint != "/metrics":
        duration = time.time() - start_time
        REQUEST_LATENCY.labels(method=method, endpoint=normalized_endpoint).observe(duration)
        LAST_REQUEST_TIMESTAMP.labels(method=method, endpoint=normalized_endpoint).set(time.time())
        if response.status_code == 200:
            SUCCESS_REQUEST_COUNT.labels(method=method, endpoint=normalized_endpoint, status_code=response.status_code).inc()

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
            "/holidays/{month}/{day}/{hour}": "Get holidays for specific day with monthly summary (no cache)",
            "/holidays/{month}/{day}/{hour}/cached": "Get holidays for specific day with monthly summary (with cache)",
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


async def get_db_connection():
    if db_pool is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return db_pool


async def fetch_day_holidays_with_month_summary(month: int, day: int, query_type: str) -> Dict[str, Any]:
    async with (await get_db_connection()).acquire() as connection:
        result = await connection.fetchrow("""
            WITH monthly_summary AS (
                SELECT 
                    COUNT(*) as total_holidays,
                    COUNT(CASE WHEN is_day_off = true THEN 1 END) as day_off_count
                FROM holidays 
                WHERE month = $1
            ),
            day_holidays AS (
                SELECT 
                    name,
                    description,
                    is_day_off,
                    is_fixed_date
                FROM holidays 
                WHERE month = $1 AND day = $2
                ORDER BY name
            ),
            all_month_holidays AS (
                SELECT 
                    name,
                    description,
                    day,
                    is_day_off,
                    is_fixed_date
                FROM holidays 
                WHERE month = $1
                ORDER BY day, name
            )
            SELECT 
                ms.total_holidays,
                ms.day_off_count,
                ARRAY_AGG(DISTINCT jsonb_build_object(
                    'name', dh.name,
                    'description', dh.description,
                    'is_day_off', dh.is_day_off,
                    'is_fixed_date', dh.is_fixed_date
                )) FILTER (WHERE dh.name IS NOT NULL) as day_holidays,
                ARRAY_AGG(DISTINCT jsonb_build_object(
                    'name', amh.name,
                    'description', amh.description,
                    'day', amh.day,
                    'is_day_off', amh.is_day_off,
                    'is_fixed_date', amh.is_fixed_date
                )) as all_month_holidays
            FROM monthly_summary ms
            CROSS JOIN LATERAL (
                SELECT * FROM day_holidays
            ) dh
            CROSS JOIN LATERAL (
                SELECT * FROM all_month_holidays
            ) amh
            GROUP BY ms.total_holidays, ms.day_off_count
        """, month, day)
        
    return {
        "month": month,
        "day": day,
        "monthly_summary": {
            "total_holidays": result['total_holidays'] if result else 0,
            "day_off_count": result['day_off_count'] if result else 0
        },
        "day_holidays": result['day_holidays'] if result else [],
        "all_month_holidays": result['all_month_holidays'] if result else []
    }


@app.get("/holidays/{month}/{day}/{hour}")
async def get_holidays(month: int, day: int, hour: int):
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    if day < 1 or day > 31:
        raise HTTPException(status_code=400, detail="Day must be between 1 and 31")
    if hour < 1 or hour > 24:
        raise HTTPException(status_code=400, detail="Hour must be between 1 and 24")
    
    return await fetch_day_holidays_with_month_summary(month, day, query_type="holidays_by_day_month")


@app.get("/holidays/{month}/{day}/{hour}/cached")
async def get_holidays_cached(month: int, day: int, hour: int):
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    if day < 1 or day > 31:
        raise HTTPException(status_code=400, detail="Day must be between 1 and 31")
    if hour < 1 or hour > 24:
        raise HTTPException(status_code=400, detail="Hour must be between 1 and 24")
    
    cache_key = f"holidays:{month}:{day}:{hour}"
    
    if redis_client:
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            CACHE_HITS.labels(cache_type="holidays").inc()
            return json.loads(cached_data)
    
    CACHE_MISSES.labels(cache_type="holidays").inc()
    
    response_data = await fetch_day_holidays_with_month_summary(month, day, query_type="holidays_by_day_month_cached")
    
    if redis_client:
        await redis_client.setex(cache_key, 3600, json.dumps(response_data))
    
    return response_data


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(REGISTRY), media_type="text/plain")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)