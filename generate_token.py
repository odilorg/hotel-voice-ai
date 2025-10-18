#!/usr/bin/env python3
"""
Simple token generator for LiveKit frontend
"""

import asyncio
from livekit import api
import os
from dotenv import load_dotenv

load_dotenv()

async def generate_token():
    # Get LiveKit credentials
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not api_key or not api_secret:
        print("Error: LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set in .env file")
        return None

    # Create token
    token = api.AccessToken(api_key, api_secret, ttl="1h")

    # Set identity
    token.identity = "guest-demo"

    # Add video grant
    grant = api.VideoGrant()
    grant.room_join = True
    grant.room = "jahongir-hotel-voice-agent"
    token.add_grant(grant)

    # Generate JWT
    jwt = token.to_jwt()

    print(f"Token: {jwt}")
    print(f"Room: jahongir-hotel-voice-agent")
    print(f"URL: ws://localhost:7880")

    return jwt

if __name__ == "__main__":
    asyncio.run(generate_token())