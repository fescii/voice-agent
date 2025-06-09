# LLM-Driven AI Voice Agent System

A sophisticated AI voice agent system that enables intelligent, human-like conversations over the phone using advanced language models, speech processing, and telephony integration.

## 🚀 Overview

This system creates AI voice agents capable of conducting natural conversations by integrating:

- **Telephony Services** (Ringover) for call management and audio streaming
- **Speech-to-Text** (Whisper, Google Speech, Azure) for voice recognition
- **Large Language Models** (OpenAI GPT, Anthropic Claude, Google Gemini) for conversation intelligence
- **Text-to-Speech** (ElevenLabs, OpenAI TTS, Google TTS) for natural voice synthesis
- **Real-time Processing** with WebSocket communication for low-latency interactions

## ✨ Key Features

### 🗣️ **Intelligent Conversations**

- Natural language understanding and generation
- Context-aware responses with conversation memory
- Multi-turn dialogue management
- Personality customization per agent

### ☎️ **Advanced Telephony**

- Inbound and outbound call handling
- Real-time audio streaming
- Call state management and monitoring
- Webhook-based event processing

### 🧠 **Multi-Provider AI Support**

- **LLM Providers**: OpenAI, Anthropic, Google AI, Custom APIs
- **STT Providers**: Whisper, Google Speech, Azure Speech
- **TTS Providers**: ElevenLabs, OpenAI TTS, Google TTS, Azure Speech
- Dynamic provider selection and failover

### 🔄 **Real-time Processing**

- WebSocket-based audio streaming
- Low-latency speech processing pipeline
- Concurrent call handling (up to 100 simultaneous calls)
- Async/await architecture for optimal performance

### 📊 **Monitoring & Management**

- Real-time call status and metrics
- Agent performance monitoring
- Database-backed persistent storage
- Comprehensive logging and error handling

## 🏗️ Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telephony     │    │   FastAPI       │    │   AI Services   │
│   (Ringover)    │◄──►│   Application   │◄──►│   (LLM/STT/TTS) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────►│   WebSocket     │◄─────────────┘
                        │   Orchestrator  │
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │   PostgreSQL    │
                        │   Database      │
                        └─────────────────┘
```

### Folder Structure

The project follows a deep, modular structure with single-responsibility files:

```
voice/
├── api/v1/                 # API endpoints
│   ├── admin/              # Admin endpoints
│   ├── agents/             # Agent management
│   ├── calls/              # Call management
│   ├── schemas/            # API data models
│   ├── streaming/          # Audio streaming
│   └── webhooks/           # Webhook handlers
├── core/                   # Core system components
│   ├── config/             # Configuration management
│   ├── logging/            # Logging setup
│   ├── security/           # Authentication & security
│   └── startup/            # Service initialization
├── data/                   # Data layer
│   ├── db/                 # Database operations
│   └── redis/              # Redis operations
├── models/                 # Data models
│   ├── external/           # External API models
│   └── internal/           # Internal data structures
├── services/               # Business logic services
│   ├── agent/              # Agent management
│   ├── audio/              # Audio processing
│   ├── call/               # Call management
│   ├── llm/                # Language model integration
│   ├── notification/       # Alert and notification systems
│   ├── ringover/           # Telephony integration
│   ├── stt/                # Speech-to-text services
│   ├── transcription/      # Conversation transcription
│   └── tts/                # Text-to-speech services
└── wss/                    # WebSocket communication
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Ringover Business Account (or higher)

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd voice
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration values
   ```

5. **Initialize database**

   ```bash
   # Set up PostgreSQL database
   python -c "from data.db.connection import create_tables; import asyncio; asyncio.run(create_tables())"
   ```

6. **Run the application**

   ```bash
   python main.py
   ```

The system will start with:

- **API Server**: <http://localhost:8000>
- **WebSocket Server**: ws://localhost:8080
- **Admin Dashboard**: <http://localhost:8000/docs>

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure the following key sections:

#### 📞 **Telephony (Ringover)**

```env
RINGOVER_API_KEY=your_api_key
RINGOVER_WEBHOOK_SECRET=your_webhook_secret
RINGOVER_DEFAULT_CALLER_ID=+1234567890
```

#### 🤖 **AI Services**

```env
# OpenAI
OPENAI_API_KEY=sk-your_openai_key
OPENAI_MODEL=gpt-4

# ElevenLabs TTS
ELEVENLABS_API_KEY=your_elevenlabs_key
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# Whisper STT
WHISPER_API_KEY=sk-your_openai_key
```

#### 🗄️ **Database**

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/voice_agents
REDIS_URL=redis://localhost:6379
```

See `.env.example` for the complete configuration reference.

## 📋 API Documentation

### Core Endpoints

#### Call Management

- `POST /api/v1/calls/outbound` - Initiate outbound call
- `GET /api/v1/calls/{call_id}/status` - Get call status
- `POST /api/v1/calls/{call_id}/end` - End active call

#### Agent Management

- `GET /api/v1/agents` - List all agents
- `POST /api/v1/agents` - Create new agent
- `PUT /api/v1/agents/{agent_id}` - Update agent configuration

#### System Monitoring

- `GET /api/v1/calls/system/info` - System status and metrics
- `GET /api/v1/admin/database/health` - Database health check

#### Webhooks

- `POST /api/v1/webhooks/ringover` - Ringover webhook receiver

### WebSocket Endpoints

- `ws://localhost:8080/ws/call/{call_id}` - Real-time call communication
- `ws://localhost:8080/ws/agent/{agent_id}` - Agent status updates

## 🔧 Development

### Running in Development Mode

```bash
# Enable debug mode
export APP_DEBUG=true

# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run WebSocket server separately (if needed)
python -m wss.simple
```

### Testing

```bash
# Run all tests
python -m pytest

# Run specific test category
python -m pytest tests/api/
python -m pytest tests/services/

# Run with coverage
python -m pytest --cov=. --cov-report=html
```

### Code Quality

```bash
# Format code
black .
isort .

# Lint code
flake8 .
mypy .

# Validate configuration
python validate.py
```

## 🎯 Usage Examples

### Creating an AI Agent

```python
import httpx

# Create agent configuration
agent_config = {
    "name": "Customer Support Agent",
    "description": "Handles customer inquiries and support",
    "llm_provider": "openai",
    "llm_model": "gpt-4",
    "tts_provider": "elevenlabs",
    "tts_voice_id": "21m00Tcm4TlvDq8ikWAM",
    "personality": {
        "tone": "friendly",
        "style": "professional",
        "expertise": "customer service"
    }
}

# Create the agent
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/agents",
        json=agent_config
    )
    agent = response.json()
    print(f"Created agent: {agent['agent_id']}")
```

### Making an Outbound Call

```python
# Initiate outbound call
call_config = {
    "phone_number": "+1234567890",
    "agent_id": "agent_123",
    "caller_id": "+0987654321",
    "context": {
        "customer_name": "John Doe",
        "account_id": "ACC123",
        "purpose": "follow_up"
    }
}

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/calls/outbound",
        json=call_config
    )
    call = response.json()
    print(f"Call initiated: {call['call_id']}")
```

## 🚀 Deployment

### Docker Deployment

```dockerfile
# Dockerfile included in project
docker build -t voice-agent-system .
docker run -p 8000:8000 -p 8080:8080 --env-file .env voice-agent-system
```

### Production Considerations

1. **Database**: Use managed PostgreSQL (AWS RDS, Google Cloud SQL)
2. **Redis**: Use managed Redis (AWS ElastiCache, Redis Cloud)
3. **Load Balancing**: Use nginx or cloud load balancers
4. **SSL/TLS**: Enable HTTPS for all API endpoints
5. **Monitoring**: Set up Prometheus/Grafana for metrics
6. **Logging**: Configure centralized logging (ELK stack)

### Scaling

- **Horizontal Scaling**: Deploy multiple instances behind a load balancer
- **Database Scaling**: Use read replicas for analytics workloads
- **Redis Scaling**: Use Redis Cluster for high availability
- **AI Services**: Consider local GPU instances for reduced latency

## 📊 Monitoring & Observability

### Health Checks

```bash
# System health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/api/v1/admin/database/health

# Call system status
curl http://localhost:8000/api/v1/calls/system/info
```

### Metrics & Logging

- **Application logs**: Structured JSON logging with configurable levels
- **Call metrics**: Duration, success rates, AI response times
- **System metrics**: CPU, memory, database connections
- **Business metrics**: Agent utilization, call volume, customer satisfaction

## 🔒 Security

### Authentication & Authorization

- JWT-based API authentication
- Role-based access control (RBAC)
- Webhook signature verification
- API rate limiting and throttling

### Data Protection

- Encrypted database connections
- Secure credential storage
- Call recording encryption
- GDPR compliance features

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Follow the coding standards and folder structure guidelines
4. Add tests for new functionality
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Submit a pull request

### Development Guidelines

- **File Structure**: Follow the deep folder structure with single-responsibility files
- **Naming**: Use lowercase folder/file names (no underscores, hyphens, or camelCase)
- **Testing**: Write unit tests for all new functionality
- **Documentation**: Update README and inline documentation
- **Code Quality**: Run linting and formatting before committing

## 📚 Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:

- **[Documentation Index](docs/index.md)** - Complete navigation guide
- **[Services](docs/services/)** - Service-specific documentation
- **[Integration](docs/integration/)** - Integration guides and architecture
- **[Testing](docs/testing/)** - Test organization and guidelines
- **[Technical References](docs/)** - LLM, database, and external service docs

All documentation follows strict naming conventions and is organized by category for easy navigation.

- [API Documentation](http://localhost:8000/docs) - Interactive Swagger UI
- [PostgreSQL Integration](docs/postgres.md) - Database setup and usage
- [LLM Integration](docs/llm.md) - Language model configuration
- [Architecture Proposal](docs/proposal.md) - Detailed system design

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Failed**

   ```bash
   # Check PostgreSQL is running
   sudo systemctl status postgresql
   
   # Verify connection string in .env
   echo $DATABASE_URL
   ```

2. **Ringover API Errors**

   ```bash
   # Verify API key and permissions
   curl -H "Authorization: Bearer $RINGOVER_API_KEY" \
        https://public-api.ringover.com/v2.1/account
   ```

3. **AI Service Timeouts**
   - Check API quotas and rate limits
   - Verify network connectivity to AI service providers
   - Consider using multiple providers for failover

4. **WebSocket Connection Issues**
   - Ensure WebSocket port (8080) is accessible
   - Check firewall settings
   - Verify CORS configuration for web clients

### Debug Mode

Enable detailed logging:

```bash
export LOG_LEVEL=DEBUG
export APP_DEBUG=true
python main.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Ringover](https://ringover.com) for telephony infrastructure
- [OpenAI](https://openai.com) for GPT and Whisper APIs
- [ElevenLabs](https://elevenlabs.io) for natural voice synthesis
- [FastAPI](https://fastapi.tiangolo.com) for the web framework
- [PostgreSQL](https://postgresql.org) for reliable data storage

---

**Made with ❤️ for building the future of conversational AI**
