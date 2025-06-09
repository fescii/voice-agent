# Ringover Webhooks and Real-Time Audio Integration

This document provides comprehensive setup instructions for integrating Ringover webhooks and real-time audio streaming based on the official Ringover documentation.

## Overview

This integration implements the complete Ringover solution as described in their documentation:

1. **Webhooks**: Real-time event notifications for call lifecycle events
2. **ringover-streamer**: Real-time RTP audio streaming for bidirectional voice communication
3. **Coordinated Integration**: Webhooks trigger audio streaming for seamless voicebot functionality

## Prerequisites

### Ringover Subscription Requirements

Based on the Ringover documentation, you need specific subscription plans for different features:

| Feature | Required Plan | Price (Annual) | Notes |
|---------|---------------|----------------|-------|
| REST API Access | SMART | $21/user/month | Basic integrations |
| Webhooks | BUSINESS | $44/user/month | Real-time notifications |
| Full Integration | BUSINESS+ | $44+/user/month | Complete voice agent capability |

### API Key Generation

1. Log into your Ringover Dashboard
2. Navigate to "Developer" tab (Crown icon)
3. Click "Create an API key"
4. Set appropriate permissions:
   - **Calls**: Read/Write (for call management)
   - **Contacts**: Read/Write (for caller identification)
   - **Users**: Read (for agent assignment)
   - **Numbers**: Read (for routing)

## Environment Configuration

Create or update your `.env` file with the following Ringover configuration:

```bash
# Ringover API Configuration
RINGOVER_API_KEY=your_api_key_here
RINGOVER_API_BASE_URL=https://public-api.ringover.com/v2
RINGOVER_DEFAULT_CALLER_ID=your_default_number

# Webhook Configuration
RINGOVER_WEBHOOK_SECRET=your_webhook_secret_here
RINGOVER_WEBHOOK_URL=https://your-domain.com

# Real-Time Streaming Configuration
RINGOVER_STREAMER_AUTH_TOKEN=your_streamer_token
RINGOVER_WEBSOCKET_HOST=0.0.0.0
RINGOVER_WEBSOCKET_PORT=8001

# AI Service Configuration (Required for voice responses)
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM  # Rachel voice
```

## Webhook Setup in Ringover Dashboard

### Step 1: Configure Webhook URL

1. Go to Ringover Dashboard → Developer → Webhooks
2. Set your webhook URL: `https://your-domain.com/api/v1/webhooks/ringover/event`
3. Enter your webhook secret key (use the same value as `RINGOVER_WEBHOOK_SECRET`)

### Step 2: Enable Required Events

Enable these events for complete voice agent functionality:

- ✅ **Calls ringing** - Prepares for incoming calls
- ✅ **Calls answered** - Triggers real-time audio streaming
- ✅ **Calls ended** - Cleans up audio streaming resources
- ✅ **Missed calls** - Handles missed call scenarios
- ✅ **Voicemail** - Processes voicemail notifications

### Step 3: HMAC Signature Verification

For security, ensure HMAC signature verification is enabled:
- Use SHA-256 algorithm
- Include signature in `X-Ringover-Signature` header
- Format: `sha256=<computed_hash>`

## Real-Time Audio Streaming Setup

### WebSocket Server Configuration

The integration automatically starts a WebSocket server that Ringover's media servers connect to:

```python
# Default configuration
HOST = "0.0.0.0"
PORT = 8001
URL_PATTERN = "ws://your-domain.com:8001/stream/call_{call_id}"
```

### Audio Processing Pipeline

The real-time audio streaming implements this flow:

1. **Receive RTP Audio**: Raw audio from Ringover media servers
2. **Speech-to-Text**: Transcribe caller speech using Whisper
3. **LLM Processing**: Generate AI responses using OpenAI GPT
4. **Text-to-Speech**: Convert responses to audio using ElevenLabs
5. **Stream Audio Back**: Send audio to Ringover for playback

### Supported Audio Formats

For optimal performance, configure these audio settings:

```python
# Recommended settings
SAMPLE_RATE = 16000  # 16kHz for good quality/latency balance
CHANNELS = 1         # Mono audio
FORMAT = "pcm"       # Raw PCM for real-time processing
CHUNK_SIZE = 4096    # 4KB chunks for streaming
```

## Application Integration

### Starting the Integration

Add this to your FastAPI application startup:

```python
from services.ringover.streaming.startup import initialize_ringover_streaming

@app.on_event("startup")
async def startup_event():
    await initialize_ringover_streaming()
```

### Webhook Endpoint

The webhook endpoint is automatically configured at:
```
POST /api/v1/webhooks/ringover/event
```

### Real-Time Streaming Endpoint

WebSocket endpoint for audio streaming:
```
WS /api/v1/streaming/audio/{session_id}
```

## Testing the Integration

### 1. Webhook Verification

Test webhook delivery using the test endpoint:

```bash
curl -X POST https://your-domain.com/api/v1/webhooks/ringover/test \
  -H "Content-Type: application/json" \
  -d '{"test": "webhook"}'
```

### 2. Integration Test

Run the comprehensive integration test:

```bash
cd /path/to/your/project
python -m services.ringover.test.integration
```

### 3. Real Call Test

1. Make a test call to your Ringover number
2. Check application logs for webhook events
3. Verify audio streaming initialization
4. Test voice interaction with the AI agent

## Security Considerations

### HMAC Signature Verification

Always verify webhook signatures in production:

```python
from services.ringover.webhooks.security import WebhookSecurity

security = WebhookSecurity()
is_valid = security.verify_signature(payload_bytes, signature_header)
```

### Network Security

- Use HTTPS for webhook URLs
- Restrict WebSocket server access to Ringover IP ranges
- Implement proper authentication for internal endpoints

### API Key Management

- Store API keys securely (environment variables, vault)
- Use minimum required permissions
- Rotate keys regularly
- Monitor API usage

## Troubleshooting

### Common Issues

1. **Webhook signature verification fails**
   - Check webhook secret configuration
   - Verify HMAC implementation
   - Ensure payload is read as raw bytes

2. **Real-time audio streaming not starting**
   - Verify WebSocket server is running
   - Check Ringover can reach your server
   - Confirm call events are triggering properly

3. **Audio quality issues**
   - Adjust sample rate (8kHz, 16kHz, 24kHz)
   - Optimize chunk size for latency
   - Check network bandwidth

### Log Monitoring

Monitor these log messages for proper operation:

```
✅ Ringover streaming server started on 0.0.0.0:8001
✅ Webhook signature verified for call {call_id}
✅ Real-time audio streaming started for call {call_id}
✅ Audio streamed to Ringover for call {call_id}
```

## Performance Optimization

### Low-Latency Configuration

For optimal real-time performance:

```python
# TTS Configuration
ELEVENLABS_MODEL = "eleven_flash_v2_5"  # Low-latency model
ELEVENLABS_OPTIMIZE_LATENCY = 1

# STT Configuration
WHISPER_MODEL = "whisper-1"  # Fast transcription

# LLM Configuration
OPENAI_MODEL = "gpt-3.5-turbo"  # Fast responses
OPENAI_MAX_TOKENS = 150  # Limit response length
```

### Scaling Considerations

- Use connection pooling for API calls
- Implement caching for frequent responses
- Consider load balancing for high call volumes
- Monitor resource usage (CPU, memory, bandwidth)

## Monitoring and Analytics

### Key Metrics to Track

- Webhook delivery success rate
- Audio streaming session duration
- End-to-end latency (speech → response)
- API call success rates
- User satisfaction scores

### Health Checks

Implement health checks for:
- Webhook endpoint responsiveness
- WebSocket server availability
- AI service connectivity
- Database performance

## Support and Documentation

For additional support:

1. **Ringover Documentation**: https://developer.ringover.com/
2. **Ringover Support**: Available through your dashboard
3. **Integration Issues**: Check application logs and webhook delivery status
4. **API Rate Limits**: Monitor usage in Ringover dashboard

## Example Call Flow

Here's what happens during a complete call:

1. **Call Ringing**: Webhook triggers preparation
2. **Call Answered**: Real-time audio streaming starts
3. **User Speaks**: Audio → STT → Text
4. **AI Processing**: Text → LLM → Response
5. **Voice Response**: Response → TTS → Audio → Caller
6. **Call Ended**: Resources cleaned up

This integration provides a complete foundation for building sophisticated voice AI agents with Ringover's telephony infrastructure.
