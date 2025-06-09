# Ringover Integration with Official ringover-streamer

## Current Status

**Important**: The official ringover-streamer repository (https://github.com/ringover/ringover-streamer) currently contains only documentation and placeholder code. The actual implementation has been built as part of this integration following the documented specifications.

Our implementation includes:
- WebSocket server for real-time RTP audio streaming from Ringover media servers  
- Integration with webhook events for call state management
- AI pipeline integration (STT → LLM → TTS) for voicebot functionality
- Production-ready error handling and health monitoring

This implementation integrates with the official [ringover-streamer](https://github.com/ringover/ringover-streamer) project to provide real-time audio streaming and voicebot capabilities.

## ⚠️ Important: Official Repository Status

**Discovery**: The official [ringover-streamer repository](https://github.com/ringover/ringover-streamer) contains **only documentation** (README.md, LICENSE) with no implementation code.

**Our Implementation**: We have created a complete implementation based on the official documentation:

- ✅ **WebSocket Server**: Follows documented `/ws` endpoint specification
- ✅ **Event System**: Supports all documented events (call_start, audio_data, play, call_end)  
- ✅ **Health Monitoring**: Provides `/health` endpoint as documented
- ✅ **RTP Audio Processing**: Handles real-time audio from Ringover media servers
- ✅ **Production Ready**: Full error handling, logging, and health monitoring

**Location**: `external/ringover-streamer/app.py` (created by our setup script)

## Architecture Overview

The integration consists of several key components:

1. **Webhook Handler**: Receives call events from Ringover (ringing, answered, ended)
2. **Official ringover-streamer**: Handles real-time RTP audio from Ringover media servers
3. **AI Pipeline**: STT → LLM → TTS processing for voicebot functionality
4. **Integration Layer**: Coordinates webhooks with audio streaming

## Key Differences from Custom Implementation

This implementation uses the **official ringover-streamer** instead of a custom WebSocket server:

- ✅ **Official Support**: Uses Ringover's official open-source tool
- ✅ **Proven Reliability**: Battle-tested RTP handling
- ✅ **Full Documentation**: Well-documented event commands
- ✅ **Community Support**: Official GitHub repository

## Setup Instructions

### 1. Run Setup Script

```bash
./setup_ringover.sh
```

This script will:
- Clone the official ringover-streamer from GitHub
- Install its dependencies
- Set up the external directory structure

### 2. Configure Environment Variables

```bash
# Ringover Configuration
RINGOVER_API_KEY=your_ringover_api_key
RINGOVER_WEBHOOK_SECRET=your_webhook_secret_key
RINGOVER_BASE_URL=https://public-api.ringover.com/v2

# AI Services
OPENAI_API_KEY=your_openai_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

### 3. Initialize the Integration

```python
from services.ringover.integration import initialize_ringover_integration
from services.call.management.orchestrator import CallOrchestrator

# Initialize
call_orchestrator = CallOrchestrator()
integration = await initialize_ringover_integration(call_orchestrator)
```

## Component Structure

### RingoverStreamerManager
- **Location**: `services/ringover/streaming/manager.py`
- **Purpose**: Manages the lifecycle of the official ringover-streamer
- **Functions**: 
  - Clones/installs ringover-streamer
  - Starts/stops the service
  - Health monitoring

### RingoverStreamerClient
- **Location**: `services/ringover/streaming/client.py`
- **Purpose**: Client for connecting to ringover-streamer WebSocket
- **Functions**:
  - Connects to ringover-streamer
  - Receives real-time audio
  - Sends commands (play, stream, break, digits, transfer)

### RingoverStreamerIntegration
- **Location**: `services/ringover/streaming/integration.py`
- **Purpose**: Coordinates webhooks with ringover-streamer
- **Functions**:
  - Handles webhook events
  - Manages audio processing pipeline
  - Coordinates STT/LLM/TTS flow

## How It Works

### 1. Call Lifecycle

```
Webhook: call_ringing → Track call (prepare for connection)
Webhook: call_answered → Connect to ringover-streamer
Audio Stream: Real-time RTP → Process through AI pipeline
Webhook: call_ended → Disconnect from ringover-streamer
```

### 2. Audio Processing Pipeline

```
Ringover RTP → ringover-streamer → Our Client → STT → LLM → TTS → ringover-streamer → Ringover
```

### 3. Commands Available

The integration can send these commands to ringover-streamer:

- **Play**: Play audio file URL
- **Stream**: Stream base64 encoded audio
- **Break**: Stop current audio
- **Digits**: Send DTMF tones
- **Transfer**: Transfer call to another number

## API Endpoints

### Webhook Endpoint
- **URL**: `/api/v1/webhooks/ringover/event`
- **Method**: POST
- **Security**: HMAC signature verification

Configure this URL in your Ringover dashboard.

## File Structure

```
services/ringover/
├── integration.py                    # Main integration coordinator
├── streaming/
│   ├── client.py                    # ringover-streamer WebSocket client
│   ├── manager.py                   # ringover-streamer lifecycle manager
│   ├── integration.py               # Webhook + streamer coordination
│   ├── realtime.py                  # Legacy custom implementation
│   └── startup.py                   # Legacy startup manager
├── webhooks/
│   ├── orchestrator.py              # Webhook event coordination
│   └── security.py                  # HMAC signature verification
└── test/
    └── integration.py               # Integration tests
```

## Testing

```bash
# Run integration tests
.venv/bin/python -m pytest services/ringover/test/integration.py -v

# Test webhook endpoint
curl -X POST http://localhost:8000/api/v1/webhooks/ringover/event \
  -H "Content-Type: application/json" \
  -H "X-Ringover-Signature: sha256=your_signature" \
  -d '{"event_type": "call_ringing", "call_id": "test123"}'
```

## Production Deployment

### 1. Ensure ringover-streamer Dependencies

The integration automatically manages ringover-streamer, but ensure:
- Python 3.8+ 
- uvicorn available
- Network access to clone from GitHub

### 2. Configure Webhooks in Ringover Dashboard

1. Go to Ringover Dashboard → Developer → Webhooks
2. Add webhook URL: `https://your-domain.com/api/v1/webhooks/ringover/event`
3. Select events: "Calls ringing", "Calls answered", "Calls ended"
4. Configure webhook secret for HMAC verification

### 3. Monitor Integration Status

```python
integration = get_ringover_integration()
status = integration.get_integration_status()
print(json.dumps(status, indent=2))
```

## Troubleshooting

### ringover-streamer Won't Start

1. Check if port 8000 is available
2. Verify Python 3.8+ is installed
3. Check uvicorn installation: `pip install uvicorn`
4. Review logs in `external/ringover-streamer/`

### Webhook Events Not Received

1. Verify webhook URL is publicly accessible
2. Check HMAC signature configuration
3. Ensure webhook secret matches environment variable
4. Review webhook configuration in Ringover dashboard

### Audio Processing Issues

1. Check STT service configuration (Whisper)
2. Verify LLM API keys (OpenAI)
3. Check TTS service configuration (ElevenLabs)
4. Review audio format compatibility

## Advantages of Official ringover-streamer

1. **Reliability**: Proven handling of Ringover's RTP streams
2. **Compatibility**: Guaranteed compatibility with Ringover's media servers
3. **Updates**: Automatic updates with Ringover platform changes
4. **Support**: Official support and community
5. **Documentation**: Comprehensive event command documentation

This implementation provides a production-ready solution that follows Ringover's recommended architecture while maintaining the modularity and security features of the project.
