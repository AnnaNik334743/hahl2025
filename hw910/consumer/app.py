from fastapi import FastAPI
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
import json
import threading
import time
import logging
from prometheus_fastapi_instrumentator import Instrumentator


app = FastAPI()
logger = logging.getLogger(__name__)

Instrumentator().instrument(app).expose(app)


def consume_messages():
    while True:
        try:
            consumer = KafkaConsumer(
                'test_topic',
                bootstrap_servers='kafka:9092',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id='my-consumer-group',
            )
            logger.info("Successfully connected to Kafka")
            for message in consumer:
                logger.info(f"Received: {message.value}")
        except NoBrokersAvailable:
            logger.error("Kafka brokers are not available, retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Error: {e}, retrying in 5 seconds...")
            time.sleep(5)


consumer_thread = threading.Thread(target=consume_messages)
consumer_thread.daemon = True
consumer_thread.start()


@app.get("/health")
def health_check():
    return {"status": "healthy"}
