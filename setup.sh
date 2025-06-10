#!/bin/bash

# FastAPI Voice Agent System - Development Setup Script
echo "Setting up FastAPI Voice Agent System..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create environment file template if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env template..."
    cat > .env << EOF
# Application Configuration
APP_NAME="AI Voice Agent System"
VERSION="1.0.0"
DEBUG_MODE=true
SECRET_KEY="your-secret-key-here"

# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=voice_agents
DATABASE_USER=postgres
DATABASE_PASSWORD=your-password-here
DATABASE_ECHO_SQL=false
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_POOL_SIZE=10

# Ringover Configuration
RINGOVER_API_KEY=your-ringover-api-key
RINGOVER_API_URL=https://api.ringover.com/v2
RINGOVER_WEBHOOK_SECRET=your-webhook-secret
RINGOVER_DEFAULT_CALLER_ID=your-default-number

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_DEFAULT_MODEL=gpt-4
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.7

# Gemini Configuration
GEMINI_API_KEY=your-gemini-api-key
GEMINI_DEFAULT_MODEL=gemini-pro
GEMINI_MAX_TOKENS=1000

# Anthropic Configuration
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_DEFAULT_MODEL=claude-3-sonnet-20240229
ANTHROPIC_MAX_TOKENS=1000

# ElevenLabs Configuration
ELEVENLABS_API_KEY=your-elevenlabs-api-key
ELEVENLABS_DEFAULT_VOICE_ID=your-default-voice-id
ELEVENLABS_MODEL_ID=eleven_monolingual_v1

# Whisper Configuration
WHISPER_MODEL=base
WHISPER_DEVICE=cpu

# Security Configuration
SECURITY_PASSWORD_SALT=your-super-secret-salt-change-in-production
SECURITY_PASSWORD_ROUNDS=12
SECURITY_JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
SECURITY_JWT_ALGORITHM=HS256
SECURITY_JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
SECURITY_JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
SECURITY_SESSION_SECRET_KEY=your-session-secret-key-change-in-production
SECURITY_SESSION_COOKIE_NAME=voice_agent_session
SECURITY_SESSION_EXPIRE_HOURS=24
SECURITY_API_KEY_HEADER=X-API-Key
SECURITY_API_KEY_EXPIRE_DAYS=365
SECURITY_RATE_LIMIT_PER_MINUTE=60
SECURITY_RATE_LIMIT_PER_HOUR=1000
SECURITY_CORS_ORIGINS=*
SECURITY_CORS_METHODS=GET,POST,PUT,DELETE,OPTIONS
SECURITY_CORS_HEADERS=*
EOF
    echo "Created .env template. Please update with your actual configuration values."
fi

# Create logs directory
mkdir -p logs

echo "Development setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your actual API keys and configuration"
echo "2. Set up PostgreSQL database"
echo "3. Set up Redis server"
echo "4. Run: python main.py"
echo ""
echo "To activate the virtual environment in the future:"
echo "source venv/bin/activate"
