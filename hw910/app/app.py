from fastapi import FastAPI, HTTPException
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import NoBrokersAvailable
import json
import time
import logging
import threading
from prometheus_fastapi_instrumentator import Instrumentator
from typing import Optional
import atexit


app = FastAPI()
producer: Optional[KafkaProducer] = None
consumer: Optional[KafkaConsumer] = None
logger = logging.getLogger(__name__)
consumer_thread_running = False

logging.basicConfig(level=logging.INFO)

Instrumentator().instrument(app).expose(app)


def get_kafka_producer():
    global producer
    if producer is None:
        try:
            producer = KafkaProducer(
                bootstrap_servers='kafka:9092',
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                api_version=(2, 0, 2)
            )
            logger.info("Connected to Kafka producer")
        except NoBrokersAvailable:
            logger.error("Kafka brokers unavailable")
            producer = None
            raise
    return producer


def get_kafka_consumer(max_retries=5, retry_delay=2):
    global consumer
    if consumer is not None:
        return consumer
    
    retries = 0
    while retries < max_retries:
        try:
            consumer = KafkaConsumer(
                'test_topic',
                bootstrap_servers='kafka:9092',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id='cg',
                enable_auto_commit=False,
                auto_offset_reset='earliest',
                api_version=(2, 0, 2)
            )
            logger.info("Connected to Kafka consumer")
            return consumer
        except Exception as e:
            retries += 1
            logger.error(f"Failed to connect to Kafka (attempt {retries}/{max_retries}): {e}")
            if retries >= max_retries:
                raise
            time.sleep(retry_delay)
    raise Exception("Max retries exceeded for Kafka connection")


@app.get("/sync")
def sync_endpoint():
    time.sleep(0.3)
    return {"status": "done"}


@app.get("/async")
def async_endpoint():
    try:
        producer = get_kafka_producer()
        producer.send('test_topic', value={"message": "Hello, Kafka!"})
        producer.flush()
        return {"status": "message sent"}
    except Exception as e:
        logger.error(f"Failed to send: {e}")
        raise HTTPException(status_code=500, detail="Send failed")


@app.get("/health")
def health_check():
    try:
        if producer:
            producer.list_topics(timeout=1)
        if consumer:
            consumer.topics()
        return {"status": "healthy", "producer": producer is not None, "consumer": consumer is not None}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


def consume_messages():
    global consumer_thread_running
    consumer_thread_running = True
    
    while consumer_thread_running:
        try:
            consumer_instance = get_kafka_consumer()
            logger.info("Starting message consumption")
            
            for message in consumer_instance:
                if not consumer_thread_running:
                    break
                    
                try:
                    logger.info(f"Received message: {message.value}")

                    # Manually commit the offset after processing
                    consumer_instance.commit()
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
        except Exception as e:
            logger.error(f"Consumer error: {e}")
            time.sleep(5)
    
    logger.info("Consumer thread stopped")


def shutdown_consumer():
    global consumer, consumer_thread_running
    consumer_thread_running = False
    
    if consumer:
        try:
            consumer.wakeup()
            consumer.close()
            logger.info("Kafka consumer closed")
        except Exception as e:
            logger.error(f"Error closing consumer: {e}")
        finally:
            consumer = None
    
    if producer:
        try:
            producer.close()
            logger.info("Kafka producer closed")
        except Exception as e:
            logger.error(f"Error closing producer: {e}")


consumer_thread = threading.Thread(target=consume_messages, daemon=True)
consumer_thread.start()

atexit.register(shutdown_consumer)
