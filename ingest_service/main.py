import os
import getpass
import asyncio
import json
from pathlib import Path
from pprint import pprint
from ring_doorbell import Auth, AuthenticationError, Requires2FAError, Ring, RingEventListener, RingEvent

user_agent = "Ring-Ingest-Service"
cache_file = Path(f"./data/{user_agent}.token.cache")

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
    auth_code = os.getenv("RING_OTP_CODE") or input("2FA code: ")
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

async def main():
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

    event_listener = RingEventListener(ring)

    event_listener.add_notification_callback(notification_handler)
    try:
        await event_listener.start()
    except RuntimeError:
        await auth.async_close()
        return

    assert event_listener.subscribed is True # necessary to function
    assert event_listener.started is True # also necessary to function lol

    print("Event listener registered!")

    devices = ring.devices()
    pprint(devices)

    print("Listening for events")

    try:
        while True:
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        pass

    print("Shutting down!")

    await event_listener.stop()
    await auth.async_close()

if __name__ == "__main__":
    asyncio.run(main())
    