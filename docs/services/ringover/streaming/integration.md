# Ringover Streaming Integration

## Overview

The Ringover streaming service is now fully integrated into the main FastAPI application as an internal service. This eliminates the need for external processes and provides seamless real-time audio streaming capabilities.

## Architecture

- **Internal FastAPI Service**: The streamer runs as part of the main application
- **WebSocket Endpoints**: Integrated streaming endpoints at `/api/v1/streaming/ringover/*`
- **Event-Driven**: Handles real-time RTP streams and voicebot interactions

## Features

- Real-time WebSocket streaming server for RTP from Ringover media servers
- Direct event responses for voicebot functionality
- Integrated lifecycle management with the main application
- Automatic startup and shutdown with other services

## Configuration

The streaming service is configured through environment variables in `.env`:

```bash
RINGOVER_API_KEY=your_api_key
RINGOVER_API_BASE_URL=https://public-api.ringover.com/v2.1/
RINGOVER_STREAMER_AUTH_TOKEN=your_streaming_token
```

## Available Events

### Play Event

Send audio to be played to the user:

```json
{
  "event": "play",
  "file": "https://example.com/audio.mp3"
}
```

### Hangup Event

End the current call:

```json
{
  "event": "hangup"
}
```

## Integration Points

- Started automatically with the main application
- Accessible via the unified API at `/api/v1/streaming/ringover/`
- Managed by the Ringover service startup manager
- Integrated with the application's logging and error handling
