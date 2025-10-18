#!/usr/bin/env python3
"""
Simple LiveKit token generator for self-hosted server
"""

from livekit import api

# Your LiveKit credentials from .env
API_KEY = "APInAyNPEv4qgz"
API_SECRET = "2wM6pXq4zR7wB9xG0vH2yJ5mM8pBq1tD3eF6hJ9nL2rT5wY7aC4dF7iJ0lN3oP6"

# Token configuration
ROOM_NAME = "jahongir-hotel-voice-agent"
PARTICIPANT_IDENTITY = "guest-demo"

# Generate token using LiveKit Python SDK
token = api.AccessToken(API_KEY, API_SECRET) \
    .with_identity(PARTICIPANT_IDENTITY) \
    .with_name("Hotel Guest") \
    .with_grants(api.VideoGrants(
        room_join=True,
        room=ROOM_NAME,
    ))

jwt_token = token.to_jwt()

print(f"Generated LiveKit Token:")
print(f"Token: {jwt_token}")
print(f"Room: {ROOM_NAME}")
print(f"Participant: {PARTICIPANT_IDENTITY}")
print(f"URL: ws://localhost:7880")
print(f"\nCopy this token to use in your frontend!")