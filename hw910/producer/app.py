from fastapi import FastAPI, HTTPException
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
import json
import time
import logging
from prometheus_fastapi_instrumentator import Instrumentator


app = FastAPI()
producer = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Instrumentator().instrument(app).expose(app)


def get_kafka_producer():
    global producer
    if producer is None:
        try:
            producer = KafkaProducer(
                bootstrap_servers='kafka:9092',
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logger.info("Successfully connected to Kafka")
        except NoBrokersAvailable:
            logger.error("Kafka brokers are not available")
            producer = None
            raise
    return producer


@app.post("/sync")
def sync_endpoint():
    time.sleep(0.5)  # Имитация работы
    logger.info("Sync endpoint processed")
    return {"status": "done"}


@app.post("/async")
def async_endpoint():
    try:
        producer = get_kafka_producer()
        producer.send('test_topic', value={"message": "Hello, Kafka!"})
        logger.info("Message sent to Kafka")
        return {"status": "message sent"}
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")


@app.get("/health")
def health_check():
    return {"status": "healthy"}
