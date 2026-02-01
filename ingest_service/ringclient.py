import os
import getpass
import asyncio
import json
from pathlib import Path
from pprint import pprint
from time import sleep
from typing import Callable
from ring_doorbell import Auth, AuthenticationError, Requires2FAError, Ring, RingEventListener, RingEvent

user_agent = "Ring-Ingest-Service"
cache_file = Path(f"./data/{user_agent}.token.cache")
otp_file = Path(f"./data/otpcode.txt")

client_healthy = True

def get_creds():
    username = os.getenv("RING_USERNAME")
    password = os.getenv("RING_PASSWORD")

    if username and password:
        return username, password
    
    username = input("Username: ")
    password = getpass.getpass("Password: ")

    return username, password

def token_updated(token):
    cache_file.write_text(json.dumps(token))


def otp_callback():
    while not otp_file.exists:
        sleep(1)

    auth_code = otp_file.read_text()
    return auth_code

async def do_auth():
    username, password = get_creds()

    auth = Auth(user_agent, None, token_updated)

    try:
        await auth.async_fetch_token(username, password)
    except Requires2FAError:
        await auth.async_fetch_token(username, password, otp_callback())
    return auth

def notification_handler(event: RingEvent):
    pprint(event)

async def create_ring_object() -> Ring:
    if cache_file.is_file():  # auth token is cached
        auth = Auth(user_agent, json.loads(cache_file.read_text()), token_updated)
        ring = Ring(auth)
        try:
            await ring.async_create_session()  # auth token still valid
        except AuthenticationError:  # auth token has expired
            auth = await do_auth()
    else:
        auth = await do_auth()  # Get new auth token
        ring = Ring(auth)

    await ring.async_update_data()

    return ring, auth

async def create_ring_listener(ring: Ring, callback: Callable[[RingEvent], None]) -> RingEventListener:
    event_listener = RingEventListener(ring)

    event_listener.add_notification_callback(callback)
    return event_listener


async def start_ring_listener(ring: Ring, auth: Auth, event_listener: RingEventListener):
    try:
        await event_listener.start()
    except RuntimeError:
        print("Event listener could not be started!")
        return

    assert event_listener.subscribed is True # necessary to function
    assert event_listener.started is True # also necessary to function lol

    print("Event listener registered!")

    devices = ring.devices()
    pprint(devices)

    print("Listening for events")

async def shutdown(event_listener: RingEventListener, auth: Auth):
    print("Shutting Ring Client down!")

    await event_listener.stop()
    await auth.async_close()