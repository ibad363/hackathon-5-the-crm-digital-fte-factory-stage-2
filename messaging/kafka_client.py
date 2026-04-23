"""Kafka client utilities for the TaskVault CRM.

The production code only needs a **singleton producer** that can be used from any
FastAPI endpoint to publish events to the `fte.tickets.incoming` topic.
"""

import os
import json
import asyncio
import logging
from typing import Any, Dict, Optional

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

TOPICS = {
    "incoming": "fte.tickets.incoming",
    "metrics": "fte.metrics",
}

class KafkaClient:
    """Singleton wrapper for Kafka Producer."""
    _producer: Optional[AIOKafkaProducer] = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_producer(cls) -> AIOKafkaProducer:
        if cls._producer is not None:
            return cls._producer
        async with cls._lock:
            if cls._producer is None:
                logger.info("🚀 Initialising Kafka producer (bootstrap=%s)", KAFKA_BOOTSTRAP_SERVERS)
                cls._producer = AIOKafkaProducer(
                    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )
                await cls._producer.start()
        return cls._producer

    @classmethod
    async def publish(cls, topic_key: str, payload: Dict[str, Any]) -> None:
        """Publish payload to the configured Kafka topic."""
        try:
            producer = await cls.get_producer()
            topic = TOPICS.get(topic_key, topic_key)
            await producer.send_and_wait(topic, payload)
            logger.info(f"✅ Kafka publish → {topic}")
        except Exception as exc:
            logger.error(f"❌ Kafka publish failed for {topic_key}: {exc}")

    @classmethod
    async def get_consumer(cls, group_id: str = "fte-consumer", topics: list = None) -> AIOKafkaConsumer:
        """Create a new Kafka consumer instance for the worker."""
        if not topics:
            topics = [TOPICS["incoming"]]
            
        logger.info(f"🔧 Initialising Kafka consumer (group={group_id}, topics={topics})")
        consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id,
            enable_auto_commit=True,
            auto_offset_reset="earliest",
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        return consumer

    @classmethod
    async def shutdown(cls):
        """Close producer connection."""
        if cls._producer is not None:
            await cls._producer.stop()
            cls._producer = None
            logger.info("🔌 Kafka producer closed")

# Convenience aliases
get_kafka_producer = KafkaClient.get_producer
publish_event = KafkaClient.publish
