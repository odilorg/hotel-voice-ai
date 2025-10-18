"""
Hotel Booking Voice Agent
Based on LiveKit Agents Framework
Leverages existing Laravel + Beds24 infrastructure
"""

import asyncio
import os
from datetime import datetime
from typing import Annotated
import httpx

from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
    Agent,
    RoomIO,
    AgentSession,
    function_tool,
    RunContext,
)
from livekit.plugins import deepgram, openai, silero
from dotenv import load_dotenv

load_dotenv()

# Laravel API Configuration - Reusing existing Telegram bot endpoints
LARAVEL_API_URL = os.getenv("LARAVEL_API_URL", "https://jahongir-app.uz")
LARAVEL_API_TOKEN = os.getenv("LARAVEL_API_TOKEN")

# HTTP client for API calls to existing Laravel endpoints
http_client = httpx.AsyncClient(
    base_url=LARAVEL_API_URL,
    headers={
        "Authorization": f"Bearer {LARAVEL_API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
    timeout=30.0
)


class HotelBookingAgent(Agent):
    """Hotel booking voice agent with function tools"""

    def __init__(self):
        super().__init__(instructions=SYSTEM_PROMPT)

    @function_tool
    async def check_availability(
        self,
        context: RunContext,
        check_in_date: str,
        check_out_date: str,
        number_of_guests: int = 1,
    ):
        """
        Check room availability at Jahongir Hotels for specific dates.
        Use this when the guest wants to know what rooms are available.
        """
        try:
            # Debug logging
            print(f"DEBUG check_availability: dates={check_in_date},{check_out_date} guests={number_of_guests}")

            # Reuse existing Laravel API endpoint from Telegram bot
            response = await http_client.post(
                "/api/voice-agent/check-availability",
                json={
                    "arrival_date": check_in_date,
                    "departure_date": check_out_date,
                    "number_of_guests": number_of_guests,
                }
            )
            response.raise_for_status()
            result = response.json()

            # Format response for voice
            if result.get('success'):
                available_rooms = result.get('available_rooms', [])
                if not available_rooms:
                    return "I'm sorry, but there are no rooms available for those dates. Would you like to try different dates?"

                # Format room list with IDs for GPT-4 to extract
                room_descriptions = []
                for room in available_rooms[:5]:  # Limit to top 5 rooms for voice
                    unit_name = room.get('unit_name', 'N/A')
                    room_name = room.get('room_name', 'Room')
                    property_name = room.get('property_name', 'Hotel')
                    room_id = room.get('room_id')
                    property_id = room.get('property_id')
                    max_guests = room.get('max_guests', 2)
                    
                    # CRITICAL: Include IDs in structured format for GPT-4
                    room_descriptions.append(
                        f"Unit {unit_name} ({room_name}) at {property_name}, sleeps {max_guests} - "
                        f"RoomID:{room_id} PropertyID:{property_id}"
                    )

                rooms_text = ". ".join(room_descriptions)
                
                return (
                    f"I found {len(available_rooms)} available rooms: {rooms_text}. "
                    f"Which room would you like to book? Please tell me the unit number."
                )
            else:
                return "I apologize, but I'm having trouble checking availability right now. Please try again in a moment."

        except Exception as e:
            print(f"Availability check error: {e}")
            return "I'm sorry, I'm having trouble connecting to our booking system. Please try again later."

    @function_tool
    async def get_guest_info(
        self,
        context: RunContext,
        phone_number: str,
    ):
        """
        Retrieve returning guest information by phone number.
        Use this when a guest mentions they've stayed before.
        """
        try:
            # Reuse existing Laravel API endpoint
            response = await http_client.get(
                f"/api/voice-agent/guest/{phone_number}"
            )
            response.raise_for_status()
            result = response.json()

            if result.get('found'):
                guest = result.get('guest', {})
                previous_bookings = guest.get('previous_bookings', 0)
                return f"Welcome back {guest.get('name', 'valued guest')}! I see you've stayed with us {previous_bookings} time(s) before. It's great to have you back!"
            else:
                return "I don't see any previous stays with this phone number. Let me help you create a new booking."

        except Exception as e:
            print(f"Guest info error: {e}")
            return "I'm having trouble retrieving guest information. Let's proceed with your booking."

    @function_tool
    async def create_booking(
        self,
        context: RunContext,
        check_in_date: str,
        check_out_date: str,
        room_id: int,
        property_id: int,
        guest_name: str,
        guest_phone: str,
        guest_email: str,
        num_adults: int = 2,
        num_children: int = 0,
        special_requests: str = "",
    ):
        """
        Create a hotel booking with all guest details.
        Use this ONLY after confirming ALL details with the guest.
        Always summarize the booking before calling this function.
        
        IMPORTANT: You MUST get room_id and property_id from check_availability response.
        Extract them from the "RoomID:XXX PropertyID:YYY" format in availability results.
        """
        try:
            # Debug logging
            print(f"DEBUG create_booking: room_id={room_id} property_id={property_id} guest={guest_name}")
            
            # Reuse existing Laravel API endpoint
            response = await http_client.post(
                "/api/voice-agent/create-booking",
                json={
                    "check_in_date": check_in_date,
                    "check_out_date": check_out_date,
                    "room_id": room_id,
                    "property_id": property_id,
                    "guest_name": guest_name,
                    "guest_phone": guest_phone,
                    "guest_email": guest_email,
                    "num_adults": num_adults,
                    "num_children": num_children,
                    "special_requests": special_requests,
                }
            )
            response.raise_for_status()
            result = response.json()

            if result.get('success'):
                booking = result.get('booking', {})
                reference = booking.get('reference', 'N/A')
                return f"Perfect! Your booking is confirmed. Your reference number is {reference}. We've sent a confirmation to your email. Thank you for choosing Jahongir Hotels!"
            else:
                return "I apologize, but there was an issue creating your booking. Please try again or contact our front desk directly."

        except Exception as e:
            print(f"Booking creation error: {e}")
            return "I'm sorry, I'm having trouble processing your booking right now. Please try again or contact our front desk."

    @function_tool
    def get_current_date(self, context: RunContext):
        """
        Get the current date and time.
        Use this when the guest says "today", "tomorrow", "next week", etc.
        """
        return datetime.now().strftime("%B %d, %Y at %I:%M %p")


# System prompt for the hotel booking agent
SYSTEM_PROMPT = """
# Current Date
Today is 2025-10-18 (October 2025).
IMPORTANT: When guests say "December 1st" they mean December 1st, 2025 (not 2023 or 2024).

# Role
You are a professional voice assistant for Jahongir Hotels in Tashkent, Uzbekistan.
You help guests check room availability and make bookings over the phone.

# Hotels We Manage
1. **Jahongir Hotel** - Our original 4-star hotel in the city center
2. **Jahongir Premium Hotel** - Our luxury 5-star hotel with premium amenities

# Your Personality
- Warm, friendly, and professional
- Patient and helpful
- Speak naturally, like a real hotel receptionist
- Use guest's name once you know it

# Conversation Flow
1. Greet warmly and ask how you can help
2. If checking availability:
   - Ask for check-in and check-out dates
   - Ask number of guests
   - Use check_availability() function
   - Present options clearly with prices
3. If making a booking:
   - Confirm dates and room choice
   - Collect: name, phone, email
   - Ask for special requests (optional)
   - **IMPORTANT**: Summarize ALL details before confirming
   - Only call create_booking() after guest confirms
   - Provide booking reference number
4. For returning guests:
   - Ask for phone number
   - Use get_guest_info() to retrieve details
   - Greet them warmly as returning guest

# Important Rules
- ALWAYS use YYYY-MM-DD format for dates with functions
- NEVER book without explicit confirmation from guest
- If uncertain about dates, use get_current_date() function
- Always confirm check-out is after check-in
- If room not available, suggest alternatives
- Be apologetic if something goes wrong
- Speak in a natural, conversational way
- **CRITICAL**: When calling create_booking(), you MUST extract room_id and property_id from the availability results
- The availability response contains "RoomID:XXX PropertyID:YYY" - extract these numbers and pass them as integers

# Example Booking Flow
User: "I want to book a room for December 1st to 4th"
You: Call check_availability("2025-12-01", "2025-12-04", 2)
Response: "Unit 12 (Standard Double) at Jahongir Hotel - RoomID:12345 PropertyID:41097"
You: [SAVE room_id=12345, property_id=41097] "Great! Unit 12 is available. May I have your name, phone, and email?"
User: "John Smith, +998901234567, john@email.com"
You: "Perfect! Let me confirm: Unit 12 from December 1-4 for John Smith. Is this correct?"
User: "Yes"
You: Call create_booking("2025-12-01", "2025-12-04", 12345, 41097, "John Smith", "+998901234567", "john@email.com", 2, 0, "")

# Language Support
- Primarily English
- Can handle Russian and Uzbek if guest prefers
- Always be respectful and professional

Remember: You're representing a luxury hotel. Be exceptional!
"""


async def entrypoint(ctx: JobContext):
    """Main entry point for voice agent sessions"""

    # Initialize the agent with tools
    agent = HotelBookingAgent()

    # Create the agent session with proper pipeline configuration
    session = AgentSession(
        vad=silero.VAD.load(),  # Voice Activity Detection
        stt=deepgram.STT(       # Speech-to-Text (FREE tier!)
            model="nova-2",
            language="multi",    # Multi-language support
        ),
        llm=openai.LLM(          # Language Model
            model="gpt-4-turbo-preview",
            temperature=0.7,
        ),
        tts=openai.TTS(          # Text-to-Speech (cheap!)
            voice="alloy",       # Options: alloy, echo, fable, onyx, nova, shimmer
        ),
    )

    # Event handlers for logging
    @session.on("user_started_speaking")
    def on_user_started_speaking():
        print("🎤 User started speaking...")

    @session.on("user_stopped_speaking")
    def on_user_stopped_speaking():
        print("🎤 User stopped speaking")

    @session.on("agent_speech_committed")
    def on_agent_speech(msg: llm.ChatMessage):
        print(f"🤖 Agent: {msg.content}")

    @session.on("function_calls_collected")
    def on_function_calls(calls):
        for call in calls:
            print(f"🔧 Calling function: {call.function_info.name}")

    # Connect to the LiveKit room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Start the agent session (this is now a task that runs in background)
    await session.start(room=ctx.room, agent=agent)
    
    # Session is now running, we can send greeting
    await asyncio.sleep(0.5)  # Small delay to ensure session is ready
    
    # Initial greeting
    await session.say(
        "Hello! Welcome to Jahongir Hotels. "
        "I'm your voice assistant. How can I help you today?",
        allow_interruptions=True
    )


if __name__ == "__main__":
    # Run the agent
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            port=8081,
        )
    )