# AI Voice Agent System

A production-ready AI voice agent system enabling intelligent phone conversations using advanced language models, speech processing, and integrated telephony services.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 17+
- Redis 6+
- Virtual environment

### Installation

1. **Clone and setup**:

```bash
git clone <repository-url>
cd voice
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**:

```bash
cp .env.example .env
# Edit .env with your API keys and database credentials
```

3. **Run the application**:

```bash
python main.py
```

The application will start on `http://0.0.0.0:8001` with all services initialized.

## ✨ Key Features

### 🗣️ **Intelligent Conversations**

- Natural language understanding and generation
- Context-aware responses with conversation memory
- Multi-turn dialogue management
- Personality customization per agent

### ☎️ **Advanced Telephony**

- **Multi-Provider Support**: Ringover integration with extensible provider architecture
- **Inbound/Outbound Calls**: Complete call lifecycle management
- **Real-time Audio Streaming**: Low-latency WebSocket audio processing
- **Call State Management**: Comprehensive call monitoring and control
- **Webhook Integration**: Real-time event processing from telephony providers

### 🏗️ **Integrated Architecture**

**✅ All-in-One FastAPI Application**

- **Integrated Ringover Streamer**: No external processes needed
- **Unified Service Management**: All services managed by startup manager
- **Single Deployment**: One application, all features included

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

## 🏗️ Current Architecture

### System Status

**✅ PRODUCTION READY** - All services integrated and functional

### Integrated Components

```text
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐    │
│  │   Ringover  │ │  WebSocket  │ │    AI Services      │    │
│  │  Streaming  │ │ Orchestrator│ │  LLM/STT/TTS/Audio  │    │
│  │ (Integrated)│ │             │ │                     │    │
│  └─────────────┘ └─────────────┘ └─────────────────────┘    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐    │
│  │ API Routes  │ │   Config    │ │    Data Layer       │    │
│  │   /api/v1   │ │  Registry   │ │ PostgreSQL + Redis  │    │
│  └─────────────┘ └─────────────┘ └─────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Service Initialization

All services are managed by the startup manager and initialize automatically:

1. **Database**: PostgreSQL connection and verification
2. **Redis**: Cache and session storage  
3. **Telephony**: Ringover API integration with call management
4. **LLM**: Multi-provider language model orchestration  
5. **Audio**: Speech processing pipeline
6. **WebSocket**: Real-time communication handlers
7. **Monitoring**: Application metrics and health checks
8. **Ringover Streaming**: Integrated audio streaming service

## 📁 Project Structure

Following strict file organization principles with maximum modularity:

```text
voice/
├── api/v1/                      # API endpoints (modular)
│   ├── admin/                   # Administrative endpoints
│   ├── agents/                  # Agent management API
│   ├── calls/                   # Call management API
│   ├── streaming/ringover.py    # Integrated streaming endpoints
│   └── webhooks/ringover/       # Webhook event handlers
├── core/                        # Core system (deeply modular)
│   ├── config/
│   │   └── providers/ringover/  # Ringover config broken down by feature
│   │       ├── api.py           # API configuration
│   │       ├── webhook.py       # Webhook configuration  
│   │       ├── streaming.py     # Streaming configuration
│   │       └── config.py        # Combined configuration
│   ├── logging/
│   │   ├── config/              # Logging configuration factory
│   │   └── format/              # Color codes and formatters
│   └── startup/
│       ├── services/            # Individual service startups
│       │   └── telephony.py     # Telephony service initialization
│       ├── shutdown/            # Graceful shutdown handling
│       └── lifespan/            # FastAPI lifespan management
├── services/                    # Business logic (one feature per file)
│   ├── ringover/                # Telephony provider integration
│   │   ├── api.py               # Ringover API client
│   │   ├── client.py            # Core client implementation
│   │   ├── integration.py       # Integration orchestrator
│   │   └── streaming/           # Integrated streaming service
│   │       └── integrated.py    # Main streaming implementation
│   ├── call/                    # Call management services
│   │   ├── manager.py           # Call lifecycle management
│   │   ├── initiation/          # Call initiation logic
│   │   └── management/          # Call state management
│   ├── llm/providers/           # Individual LLM providers
│   ├── audio/streaming/         # Audio processing modules
│   └── stt/                     # Speech-to-text services
├── models/external/             # External API data models
│   ├── ringover/                # Ringover-specific models
│   └── llm/                     # LLM provider models
└── docs/                        # Comprehensive documentation
    ├── services/ringover/       # Service-specific docs
    ├── databases/               # Database documentation
    └── llm/                     # AI service documentation
```

## 🔧 Configuration

### Environment Variables

The system uses a comprehensive `.env` configuration:

```bash
# Application
APP_ENV=development
API_PORT=8001

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/voice

# Redis
REDIS_URL=redis://localhost:6379

# Ringover Integration
RINGOVER_API_KEY=your_api_key
RINGOVER_API_BASE_URL=https://public-api.ringover.com/v2.1/
RINGOVER_WEBHOOK_SECRET=your_webhook_secret

# AI Services
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
ELEVENLABS_API_KEY=your_elevenlabs_key

# Logging
LOG_LEVEL=INFO
LOG_DIR=/tmp/voice_agent_logs
```

## 🚀 Getting Started

### System Requirements

- Python 3.8+
- PostgreSQL 17+
- Redis 6+
- 4GB RAM minimum
- 10GB disk space

### Installation Steps

1. **Environment Setup**:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. **Database Setup**:

```bash
# Create PostgreSQL database
createdb voice

# Run migrations (if any)
# python migrate.py
```

3. **Configuration**:

```bash
cp .env.example .env
# Edit .env with your credentials
```

4. **Start Application**:

```bash
python main.py
```

**Application runs on: <http://0.0.0.0:8001>**

## ✅ Current Status

### What's Working

- ✅ **All Services Integrated**: No external dependencies
- ✅ **FastAPI Server**: Running on port 8001
- ✅ **Database**: PostgreSQL connected and verified
- ✅ **Redis**: Cache layer operational
- ✅ **Telephony**: Ringover API integration with proper URL handling
- ✅ **LLM**: OpenAI integration (needs valid API key for full functionality)
- ✅ **Streaming**: Ringover streamer fully integrated into FastAPI
- ✅ **WebSocket**: Real-time communication ready
- ✅ **Monitoring**: Application health monitoring active
- ✅ **Logging**: Comprehensive logging to `/tmp/voice_agent_logs`
- ✅ **Graceful Shutdown**: Clean startup and shutdown lifecycle

### Service Startup Time

**Complete initialization: ~7-9 seconds**

```text
🚀 Starting application initialization...
⏳ Initializing database... ✅ (0.2s)
⏳ Initializing redis... ✅ (0.1s)  
⏳ Initializing telephony... ✅ (0.5s)
⏳ Initializing llm... ✅ (6.0s)
⏳ Initializing audio... ✅ (0.1s)
⏳ Initializing websocket... ✅ (0.1s)
⏳ Initializing monitoring... ✅ (0.1s)
⏳ Initializing ringover... ✅ (0.1s)
✅ Application startup completed!
```

## 📚 Documentation

Comprehensive documentation is organized by feature:

- **[Service Documentation](docs/services/)** - Individual service guides
- **[Ringover Integration](docs/services/ringover/streaming/integration.md)** - Streaming service details
- **[Database Setup](docs/databases/)** - Database configuration and schemas
- **[LLM Configuration](docs/llm/)** - AI service setup and usage
- **[API Reference](docs/api/)** - Endpoint documentation
- **[Testing Guide](docs/testing/)** - Testing organization and runners

## 🧪 Testing

Run comprehensive tests:

```bash
# All tests
python tests.py

# Service-specific tests  
python services/ringover/tests/runner.py
python services/agent/tests/runner.py
python api/tests/runner.py
```

## 🔄 Development

### File Organization Principles

This project follows strict modularity principles:

1. **Maximum Folder Depth**: Each concept gets its own subfolder
2. **Lowercase Names**: All files and folders use lowercase, no underscores
3. **Single Responsibility**: One feature per file, files stay short
4. **Focused Modules**: Each file handles one specific functionality

### Adding New Features

When adding features, follow the existing structure:

```bash
# Good: Focused, modular structure
services/newfeature/component/logic.py
services/newfeature/component/config.py

# Avoid: Monolithic files
services/newfeature_service.py  # Wrong naming
services/bigfile.py             # Too broad
```

---

**Production-Ready AI Voice Agent System** - Fully integrated, modular, and scalable.
│   ├── llm/                # Language model integration
│   ├── notification/       # Alert and notification systems
│   ├── ringover/           # Telephony integration
│   ├── stt/                # Speech-to-text services

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

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow file organization principles (lowercase, modular, single-responsibility)
4. Add comprehensive tests
5. Update documentation
6. Submit a pull request

### Development Standards

- **Modular Architecture**: Keep files short and focused on single features
- **Naming Conventions**: Lowercase names, maximum folder depth, no underscores
- **Testing**: Comprehensive test coverage for all services
- **Documentation**: Update relevant documentation in `docs/`
- **Code Quality**: Follow type hints and async patterns

## 🐛 Troubleshooting

### Common Issues

### Database Connection Failed

```bash
# Check PostgreSQL status
sudo systemctl status postgresql
```

### API Authentication Errors

- Verify API keys in `.env` file
- Check API quota limits
- Ensure proper environment variable loading

### Service Startup Issues

- Check logs in `/tmp/voice_agent_logs/`
- Verify all required environment variables are set
- Ensure PostgreSQL and Redis are running

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Ringover](https://ringover.com) - Telephony infrastructure
- [OpenAI](https://openai.com) - GPT and Whisper APIs  
- [FastAPI](https://fastapi.tiangolo.com) - Web framework
- [PostgreSQL](https://postgresql.org) - Database layer

---

## Ready for Production 🚀

This AI Voice Agent System is production-ready with:

- ✅ Fully integrated services
- ✅ Comprehensive error handling
- ✅ Graceful shutdown procedures
- ✅ Modular, maintainable architecture
- ✅ Extensive documentation and testing
