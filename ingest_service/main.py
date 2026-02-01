import os
import getpass
import asyncio
import json
from pprint import pprint
from ringclient import create_ring_listener, create_ring_object, start_ring_listener, shutdown
from kafka import KafkaProducer
from ring_doorbell import RingEvent

client_id = "Ring-Ingest-Service"

kafka_server = os.getenv("KAFKA_BOOTSTRAP_SERVERS") or "localhost:29092"

producer = KafkaProducer(
    bootstrap_servers=kafka_server,
    client_id=client_id,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    transactional_id=client_id
)

def ring_event_handler(event: RingEvent):
    kafka_topic = os.getenv("KAFKA_TOPIC")

    producer.init_transactions()
    producer.begin_transaction()

    future = producer.send(
        kafka_topic, 
        { 
            "event_id": event.get("id"),
            "doorbot_id": event.get("doorbot_id"),
            "device_name": event.get("device_name"),
            "device_kind": event.get("device_kind"),
            "event_time": event.get("now"),
            "expires_in": event.get("expires_in"),
            "kind": event.get("kind"),
            "state": event.get("state"),
            "is_update": event.get("is_update")
        }
    )

    future.get()
    producer.commit_transaction()


async def main():
    ring, auth = await create_ring_object()
    event_listener = await create_ring_listener(ring, ring_event_handler)

    await start_ring_listener(ring, auth, event_listener)

    try:
        while True:
            await asyncio.sleep(10)
    except asyncio.CancelledError:
        shutdown()
    

if __name__ == "__main__":
    asyncio.run(main())
    