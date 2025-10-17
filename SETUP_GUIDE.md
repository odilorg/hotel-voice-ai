# Voice Booking Agent - Setup Guide

## Phase 1: Environment Setup

### 1. Required API Keys

You need to add these to your `.env` file:

#### OpenAI API Key
Add to your main Laravel `.env` file:
```env
OPENAI_API_KEY=sk-your_openai_key_here
```

#### LiveKit API Keys
You need to generate these from your LiveKit server:
```bash
# On your server, generate API keys
cd /opt/livekit
./livekit-server generate-keys
```

#### Laravel Sanctum Token
Generate a token for the voice agent:
```bash
cd /var/www/jahongirnewapp
php artisan tinker
>>> $user = User::find(1);
>>> $token = $user->createToken('voice-agent')->plainTextToken;
>>> echo $token;
```

### 2. Update Voice Agent .env

Update `C:\xampp8-2\htdocs\voice-booking-agent\.env` with your actual values:

```env
# LiveKit Configuration
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=your_generated_api_key
LIVEKIT_API_SECRET=your_generated_secret

# OpenAI Configuration
OPENAI_API_KEY=sk-your_actual_openai_key

# Deepgram Configuration
DEEPGRAM_API_KEY=5c159a77bb02a8a82cc51510209cf5b38e634870

# Laravel API Configuration
LARAVEL_API_URL=https://jahongir-app.uz
LARAVEL_API_TOKEN=your_generated_sanctum_token

# Agent Settings
LOG_LEVEL=INFO
```

## Phase 2: Laravel API Endpoints

We need to create voice-specific API endpoints that reuse your existing Telegram bot logic.

### Create VoiceAgentController

**File:** `C:\xampp8-2\htdocs\jahongirnewapp\app\Http\Controllers\VoiceAgentController.php`

```php
<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Services\Beds24BookingService;
use App\Models\RoomUnitMapping;

class VoiceAgentController extends Controller
{
    public function checkAvailability(Request $request)
    {
        // Reuse existing availability logic from Telegram bot
        $validated = $request->validate([
            'arrival_date' => 'required|date',
            'departure_date' => 'required|date|after:arrival_date',
            'number_of_guests' => 'integer|min:1',
        ]);

        $beds24Service = app(Beds24BookingService::class);

        // Get all room IDs
        $roomIds = RoomUnitMapping::pluck('room_id')->toArray();

        // Check availability using existing method
        $availability = $beds24Service->checkAvailability(
            $validated['arrival_date'],
            $validated['departure_date'],
            $roomIds
        );

        // Get available rooms
        $bookedRoomIds = $availability['bookedRoomIds'] ?? [];
        $availableRooms = RoomUnitMapping::whereNotIn('room_id', $bookedRoomIds)->get();

        return response()->json([
            'success' => true,
            'available_rooms' => $availableRooms,
            'total_available' => $availableRooms->count(),
            'total_rooms' => count($roomIds),
        ]);
    }

    public function createBooking(Request $request)
    {
        // Reuse existing booking creation logic
        $validated = $request->validate([
            'check_in_date' => 'required|date',
            'check_out_date' => 'required|date|after:check_in_date',
            'hotel_name' => 'required|string',
            'room_type' => 'required|string',
            'guest_name' => 'required|string',
            'guest_phone' => 'required|string',
            'guest_email' => 'required|email',
            'number_of_guests' => 'integer|min:1',
            'special_requests' => 'nullable|string',
        ]);

        $beds24Service = app(Beds24BookingService::class);

        // Use existing createBooking method
        $result = $beds24Service->createBooking($validated);

        return response()->json($result);
    }

    public function getGuestByPhone($phone)
    {
        // Reuse existing guest lookup logic
        // This should match your Telegram bot's guest lookup

        return response()->json([
            'found' => false,
            'message' => 'Guest lookup not implemented yet',
        ]);
    }
}
```

### Add API Routes

**File:** `C:\xampp8-2\htdocs\jahongirnewapp\routes\api.php`

```php
// Voice Agent API Routes
Route::middleware('auth:sanctum')->prefix('voice-agent')->group(function () {
    Route::post('/check-availability', [VoiceAgentController::class, 'checkAvailability']);
    Route::post('/create-booking', [VoiceAgentController::class, 'createBooking']);
    Route::get('/guest/{phone}', [VoiceAgentController::class, 'getGuestByPhone']);
});
```

## Phase 3: Deployment

### 1. Install Python Dependencies

```bash
cd /opt/voice-agent
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Test Voice Agent

```bash
# Terminal 1: LiveKit server
cd /opt/livekit
./livekit-server --config livekit.yaml

# Terminal 2: Voice agent
cd /opt/voice-agent
source venv/bin/activate
python hotel_booking_agent.py start
```

### 3. Production Deployment

Create supervisor config:

```ini
# /etc/supervisor/conf.d/voice-agent.conf
[program:voice-agent]
command=/opt/voice-agent/venv/bin/python /opt/voice-agent/hotel_booking_agent.py start
directory=/opt/voice-agent
autostart=true
autorestart=true
user=www-data
redirect_stderr=true
stdout_logfile=/var/log/voice-agent.log
```

## Testing

### Test API Endpoints

```bash
curl -X POST https://jahongir-app.uz/api/voice-agent/check-availability \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "arrival_date": "2025-01-02",
    "departure_date": "2025-01-03",
    "number_of_guests": 2
  }'
```

### Test Voice Agent

Use the LiveKit CLI to test voice conversations:

```bash
cd /opt/voice-agent
python hotel_booking_agent.py connect --console
```

## Next Steps

1. **Add OpenAI API key** to your main Laravel `.env` file
2. **Generate LiveKit API keys** on your server
3. **Create Laravel Sanctum token** for voice agent
4. **Implement voice agent API endpoints** in Laravel
5. **Test end-to-end conversation flow**