# Ringover Integration Deployment Guide

## Overview

This guide covers the deployment and configuration of the complete Ringover integration, including webhooks and real-time audio streaming for AI voice agents.

## Architecture

The integration consists of several key components following the project's modular structure:

### Core Components

1. **Webhook System** (`services/ringover/webhooks/`)
   - `orchestrator.py`: Coordinates webhook events with streaming
   - `security.py`: HMAC signature verification
   
2. **Real-time Streaming** (`services/ringover/streaming/`)
   - `realtime.py`: Bi-directional audio streaming with STT/TTS pipeline
   - `startup.py`: WebSocket server lifecycle management
   
3. **Integration Layer** (`services/ringover/integration.py`)
   - Main coordination between webhooks and streaming
   - Dependency injection and lifecycle management

4. **API Endpoints** (`api/v1/webhooks/ringover/`)
   - `event.py`: FastAPI webhook endpoint with security

## Prerequisites

### Environment Setup

1. **Python Environment**: Use the configured `.venv` environment:
   ```bash
   source .venv/bin/activate  # If not using the configured environment
   ```

2. **Required Dependencies**: All dependencies are included in `requirements.txt`:
   - `fastapi`, `uvicorn` - Web framework
   - `websockets` - Real-time streaming
   - `openai` - LLM integration
   - `elevenlabs` - TTS services
   - `httpx` - HTTP client
   - `pytest`, `pytest-asyncio` - Testing

### Environment Variables

Configure the following environment variables in your `.env` file:

```bash
# Ringover Configuration
RINGOVER_API_KEY=your_ringover_api_key
RINGOVER_WEBHOOK_SECRET=your_webhook_secret_key
RINGOVER_BASE_URL=https://public-api.ringover.com/v2

# AI Services
OPENAI_API_KEY=your_openai_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# Streaming Configuration
RINGOVER_STREAMING_HOST=0.0.0.0
RINGOVER_STREAMING_PORT=8765
RINGOVER_STREAMING_PATH=/ws

# Database (if using persistent storage)
DATABASE_URL=postgresql://user:password@localhost/dbname
REDIS_URL=redis://localhost:6379/0
```

## Deployment Steps

### 1. Configuration Verification

Run the integration test to verify everything is configured correctly:

```bash
# Using pytest (recommended)
.venv/bin/python -m pytest services/ringover/test_integration.py -v

# Or standalone
PYTHONPATH=/home/femar/A03/voice .venv/bin/python services/ringover/test_integration.py
```

### 2. Application Startup

The integration is designed to be initialized during application startup. Add to your main application:

```python
from services.ringover.integration import initialize_ringover_integration
from services.call.management.orchestrator import CallOrchestrator

# During startup
call_orchestrator = CallOrchestrator()
await initialize_ringover_integration(call_orchestrator)
```

### 3. Webhook Endpoint Configuration

The webhook endpoint is available at:
- **Path**: `/api/v1/webhooks/ringover/event`
- **Method**: POST
- **Security**: HMAC signature verification via `X-Ringover-Signature` header

Configure this URL in your Ringover dashboard as the webhook endpoint.

### 4. Real-time Streaming Setup

The WebSocket server runs on the configured host/port:
- **Default**: `ws://0.0.0.0:8765/ws`
- **Protocol**: WebSocket with binary audio frames
- **Format**: Real-time audio streaming with STT/LLM/TTS pipeline

### 5. Production Considerations

#### Security
- ✅ HMAC signature verification implemented
- ✅ Secure WebSocket connections
- ⚠️ Configure HTTPS for webhook endpoints in production
- ⚠️ Use secure WebSocket (WSS) in production

#### Monitoring
- ✅ Comprehensive logging throughout all components
- ✅ Integration status reporting
- ✅ Error handling and recovery

#### Scalability
- 🔄 WebSocket server supports multiple concurrent connections
- 🔄 Modular design allows for horizontal scaling
- 🔄 Stateless webhook processing

## Testing

### Unit Tests
```bash
# Run specific integration test
.venv/bin/python -m pytest services/ringover/test_integration.py::TestRingoverIntegration::test_complete_integration -v
```

### Manual Testing

1. **Webhook Testing**: Send test webhooks to `/api/v1/webhooks/ringover/event`
2. **Streaming Testing**: Connect to WebSocket endpoint and test audio flow
3. **Integration Testing**: Simulate complete call lifecycle

## Troubleshooting

### Common Issues

1. **Config Registry Not Initialized**
   ```
   Error: KeyError: 'ringover'
   Solution: Ensure config_registry.initialize() is called before accessing configs
   ```

2. **Missing API Keys**
   ```
   Warning: No API key configured for service
   Solution: Set required environment variables
   ```

3. **WebSocket Connection Issues**
   ```
   Error: Connection refused to streaming server
   Solution: Verify streaming server is started and port is available
   ```

### Debug Mode

Enable debug logging by setting:
```bash
export LOG_LEVEL=DEBUG
```

### Health Checks

Check integration status:
```python
from services.ringover.integration import get_ringover_integration

integration = get_ringover_integration()
status = integration.get_integration_status()
print(json.dumps(status, indent=2))
```

## File Structure

The implementation follows strict naming conventions and deep folder structure:

```
services/ringover/
├── integration.py              # Main integration coordination
├── README.md                   # Configuration guide
├── DEPLOYMENT.md               # This deployment guide
├── test_integration.py         # Integration tests
├── webhooks/
│   ├── __init__.py
│   ├── orchestrator.py         # Webhook event coordination
│   └── security.py             # HMAC signature verification
└── streaming/
    ├── __init__.py
    ├── realtime.py             # Real-time audio streaming
    └── startup.py              # WebSocket server management
```

## Support

For issues related to:
- **Webhook Events**: Check `services/ringover/webhooks/orchestrator.py`
- **Audio Streaming**: Check `services/ringover/streaming/realtime.py`
- **Security**: Check `services/ringover/webhooks/security.py`
- **Integration**: Check `services/ringover/integration.py`

All components include comprehensive logging for debugging and monitoring.
