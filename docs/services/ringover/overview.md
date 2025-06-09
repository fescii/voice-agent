# Ringover Integration Setup Guide

## Overview

This implementation provides complete Ringover integration with webhooks and real-time audio streaming for AI voice agents, as described in the Ringover documentation.

## Architecture

The integration consists of three main components:

1. **Webhook Event Processing** - Receives real-time event notifications from Ringover
2. **Real-time Audio Streaming** - Bidirectional audio communication via WebSocket  
3. **Coordination Layer** - Synchronizes webhooks with audio streams for seamless operation

## Required Configuration

### 1. Environment Variables

Add these to your `.env` file:

```bash
# Ringover API Configuration
RINGOVER_API_KEY=your_api_key_here
RINGOVER_API_BASE_URL=https://public-api.ringover.com/v2
RINGOVER_DEFAULT_CALLER_ID=your_ringover_number

# Webhook Configuration (CRITICAL for security)
RINGOVER_WEBHOOK_SECRET=your_webhook_secret_here
RINGOVER_WEBHOOK_URL=https://your-domain.com

# Streaming Configuration
RINGOVER_WEBSOCKET_HOST=0.0.0.0
RINGOVER_WEBSOCKET_PORT=8001
RINGOVER_STREAMER_AUTH_TOKEN=your_auth_token
```

### 2. Ringover Dashboard Setup

#### API Key Setup
1. Log into your Ringover dashboard
2. Navigate to "Developer" section
3. Click "Create an API key"
4. Assign appropriate permissions:
   - **Calls**: Read/Write (for call management)
   - **Contacts**: Read/Write (for contact lookup)
   - **Users**: Read (for user information)
   - **Monitoring**: Read (for call analytics)

#### Webhook Configuration
1. Go to "Developer" → "Webhooks" in Ringover dashboard
2. Set webhook URL: `https://your-domain.com/api/v1/webhooks/ringover/event`
3. Set webhook secret (same as `RINGOVER_WEBHOOK_SECRET`)
4. Enable these events:
   - ✅ Calls ringing
   - ✅ Calls answered  
   - ✅ Calls ended
   - ✅ Missed calls
   - ✅ Voicemail
   - ✅ SMS received/sent (optional)

## Implementation Details

### Webhook Event Flow

```
1. Call Event Occurs → 2. Webhook Sent → 3. Signature Verified → 4. Event Processed
                                                                      ↓
5. Audio Stream Initiated ← 4. Ringover Media Servers Connect ← 3. WebSocket Server Ready
```

### Real-time Audio Processing

```
Ringover Media → WebSocket → STT Service → LLM → TTS Service → WebSocket → Ringover Media
(Caller Audio)              (Transcription)  (AI Response)  (Synthesized)              (AI Audio)
```

## Usage Examples

### Basic Integration

```python
from services.ringover.integration import get_ringover_integration
from services.call.management.orchestrator import CallOrchestrator

# Initialize
call_orchestrator = CallOrchestrator()
integration = await initialize_ringover_integration(call_orchestrator)

# The integration is now active and will:
# 1. Process webhook events automatically
# 2. Start audio streaming when calls are answered
# 3. Provide real-time AI responses
```

### Getting Integration Status

```python
integration = get_ringover_integration()
status = integration.get_integration_status()

print(f"Active calls: {len(status['active_streaming_calls'])}")
print(f"Webhook security: {'Enabled' if status['webhook_security_enabled'] else 'Disabled'}")
```

## Security Features

### HMAC Signature Verification
- All webhook payloads are verified using HMAC-SHA256
- Prevents webhook spoofing attacks
- Uses the secret configured in Ringover dashboard

### Authentication
- API key authentication for all Ringover API calls
- WebSocket authentication for streaming connections
- Secure token-based access control

## Subscription Requirements

Based on Ringover documentation:

- **SMART Plan ($21/user/month)**: API access only
- **BUSINESS Plan ($44/user/month)**: API + Webhooks ✅ **Required minimum**
- **ADVANCED Plan ($54/user/month)**: All features

**Note**: Webhooks are required for real-time event notifications, so at least the BUSINESS plan is needed.

## Network Configuration

### Firewall Rules
- **Inbound**: Port 8001 (WebSocket server for Ringover media)
- **Outbound**: Port 443 (HTTPS to Ringover APIs)

### DNS/Domain Requirements
- Public domain with SSL certificate
- Webhook URL must be publicly accessible
- WebSocket endpoint should be accessible to Ringover media servers

## Monitoring and Debugging

### Log Monitoring
Key log messages to watch:
```
INFO: Ringover integration initialized successfully
INFO: Call answered: {call_id} - Initiating real-time audio streaming  
INFO: Real-time audio streaming started for call {call_id}
WARNING: Webhook signature verification failed
ERROR: Failed to start audio streaming for call {call_id}
```

### Health Checks
```python
# Check integration health
status = integration.get_integration_status()
assert status['initialized'] == True
assert status['webhook_security_enabled'] == True
assert status['streaming_server']['is_running'] == True
```

## Troubleshooting

### Common Issues

1. **Webhook Signature Failures**
   - Verify `RINGOVER_WEBHOOK_SECRET` matches dashboard configuration
   - Check webhook URL is accessible via HTTPS

2. **Audio Streaming Not Starting**
   - Ensure port 8001 is open and accessible
   - Verify Ringover media servers can reach your WebSocket endpoint
   - Check authentication token configuration

3. **No Webhook Events Received**
   - Verify webhook URL in Ringover dashboard
   - Check firewall allows inbound HTTPS traffic
   - Confirm subscription plan includes webhook access

### Testing Webhooks

Use the test endpoint:
```bash
curl -X POST https://your-domain.com/api/v1/webhooks/ringover/test \
  -H "Content-Type: application/json" \
  -d '{"test": "webhook"}'
```

## Performance Considerations

### Latency Optimization
- STT: ~200-500ms (Whisper API)
- LLM: ~300-800ms (GPT-3.5/4)  
- TTS: ~75ms first chunk (ElevenLabs Flash)
- **Total**: ~600-1400ms end-to-end

### Scaling
- Supports up to 100 concurrent calls
- Async/await architecture for optimal performance
- Configurable audio buffer sizes for latency vs. accuracy trade-offs

## Advanced Configuration

### Custom Audio Processing
```python
# Override default audio handlers
streamer = integration.get_streaming_service()
if streamer:
    streamer.set_audio_handler(custom_audio_processor)
    streamer.set_event_handler(custom_event_handler)
```

### Custom Webhook Processing
```python
# Add custom webhook event handlers
orchestrator = integration.get_webhook_orchestrator()
# Custom processing logic here
```

This integration provides a complete, production-ready solution for Ringover real-time voice AI agents following the official documentation patterns.
