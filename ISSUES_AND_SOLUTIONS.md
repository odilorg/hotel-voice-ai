# Issues and Solutions - Hotel Voice AI Booking Agent

## Overview
This document details all issues encountered during development and deployment of the LiveKit hotel voice booking agent, including symptoms, root causes, debugging steps, and solutions.

---

## Issue #1: DeepSeek API Not Responding

### Symptoms
- Agent connected successfully to LiveKit room
- No voice responses from agent
- Logs showed: "speech scheduling is paused"
- User reported: "technical issue could not check"

### Environment
- LiveKit Agents Framework v1.2.15
- Attempted LLM: DeepSeek API (deepseek-chat model)
- STT: Deepgram Nova-2
- TTS: OpenAI Alloy

### Root Cause
DeepSeek API incompatible with LiveKit function calling pattern. The LiveKit framework relies on OpenAI-compatible function calling format, and DeepSeek implementation does not match perfectly.

### Solution
Reverted to OpenAI GPT-4-turbo-preview

### User Feedback
"technical issue" -> "no greetings" -> Eventually worked after GPT-4 switch

### Lesson Learned
Stick with OpenAI GPT-4 for LiveKit function calling. DeepSeek may work for basic chat but not for function tools.

---

## Issue #2: Agent Not Greeting Users

### Symptoms
- Connection established successfully
- No initial greeting played
- Agent silent until issue fixed
- User: "no greetings" / "check she is not talking"

### Root Cause
Incorrect async/await pattern. Attempted to call session.say() before the session was fully started.

### Solution
Properly await session start with delay before greeting

### Lesson Learned
Always fully await session.start() before attempting any session operations.

---

## Issue #3: Wrong Dates / Past Years (2023 instead of 2025)

### Symptoms
- User said: "December 1st"
- Availability check failed with 422 error
- Laravel validation rejected: "check_in_date must be after_or_equal:today"
- Debug log showed: 2023-12-01 instead of 2025-12-01

### Root Cause
GPT-4 knowledge cutoff is January 2025, but it does not automatically know the current date. Without context, it defaults to training data patterns (often 2023).

### Solution
Added current date context to system prompt:
"Today is 2025-10-18 (October 2025). When guests say December 1st they mean December 1st 2025"

### Lesson Learned
Always provide current date context in system prompts for LLMs, especially for booking systems.

---

## Issue #4: Booking Creation 422 Error (MAIN ISSUE)

### Symptoms
- Availability checking worked perfectly
- Booking creation failed with 422 Unprocessable Content
- User: "could not book room but checked avail successfully"

### Root Cause
Voice agent was sending hotel_name (string) and room_type (string) but Laravel API expected room_id (integer) and property_id (integer).

### Investigation Process
1. Read Telegram bot code (ProcessBookingMessage.php)
2. Discovered it uses RoomUnitMapping to get room_id and property_id as integers
3. Read VoiceAgentController.php to confirm Laravel validation
4. Identified the parameter mismatch

### The Problem
Voice agent sent:
- hotel_name: "Jahongir Hotel" (STRING)
- room_type: "Standard Double" (STRING)

Laravel API expected:
- room_id: 12345 (INTEGER - Beds24 room type ID)
- property_id: 41097 (INTEGER - Beds24 property ID)

### Solution Implementation
1. Updated check_availability() to include IDs in response format: "RoomID:12345 PropertyID:41097"
2. Changed create_booking() parameters from hotel_name/room_type to room_id/property_id (integers)
3. Updated system prompt with extraction instructions for GPT-4
4. Added debug logging

### User Feedback
"could not book room but checked avail successfully" -> "working good"

### Files Changed
/opt/voice-agent/hotel_booking_agent.py (1 file, 61 insertions, 16 deletions)

### Git Commit
Commit bd3512d: "Fix booking creation to use room_id and property_id integers"

### Lesson Learned
1. Always check API validation requirements - Read the Laravel controller code
2. Learn from existing implementations - Telegram bot showed the correct pattern
3. Type matters - Strings vs integers can break API validation
4. GPT-4 can extract structured data - Use clear formats like "RoomID:123"
5. Debug logging is essential - Print parameters before API calls

---

## Common Debugging Techniques

### 1. Debug Logging
Add print statements to track function calls and log all parameters, API requests, and responses.

### 2. Check Laravel Logs
Monitor Laravel application logs on server:
tail -f /var/www/jahongirnewapp/storage/logs/laravel.log

### 3. Test API Endpoints Directly
Use curl to isolate issues and test endpoints independently.

### 4. Compare Working Implementations
When stuck, read code that already works:
- Telegram bot code
- API controllers
- Database models

### 5. Monitor LiveKit Agent Logs
Watch real-time logs: tail -f /opt/voice-agent/agent.log

---

## Summary Table

| Issue | Symptom | Root Cause | Solution | Status |
|-------|---------|------------|----------|--------|
| DeepSeek API Not Responding | No voice output | DeepSeek incompatible with LiveKit | Use GPT-4 | Fixed |
| Agent Not Greeting | Silent on connection | session.say() called too early | Await session.start() properly | Fixed |
| Wrong Dates (2023) | 422 validation error | GPT-4 does not know current date | Add current date to system prompt | Fixed |
| Booking 422 Error | Availability works, booking fails | Used strings instead of integers for IDs | Extract room_id/property_id as integers | Fixed |

---

## Best Practices Going Forward

1. Always validate API contracts - Check Laravel validation rules before implementing
2. Use debug logging liberally - Print all function parameters and API responses
3. Test incrementally - Test each function independently before integration
4. Learn from existing code - Reference working implementations (Telegram bot)
5. Provide LLM context - Current date, data formats, extraction instructions
6. Monitor both sides - Watch both LiveKit agent logs AND Laravel API logs
7. Type safety - Pay attention to int vs str in function signatures
8. Keep it simple - Avoid complex workarounds when simple solutions exist

---

## Resources

- LiveKit Agents Docs: https://docs.livekit.io/agents/overview/
- Beds24 API v2: https://api.beds24.com/
- Laravel Validation: https://laravel.com/docs/10.x/validation
- GPT-4 Function Calling: https://platform.openai.com/docs/guides/function-calling

---

Last Updated: 2025-10-18
Agent Version: 1.2.15
Status: All Issues Resolved
