#!/bin/bash
# Setup script for Ringover integration with official ringover-streamer

set -e

echo "=== Setting up Ringover Integration ==="

# Check if we're in the correct directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Create external directory for ringover-streamer
echo "Creating external directory..."
mkdir -p external

# Clone ringover-streamer if it doesn't exist
if [ ! -d "external/ringover-streamer" ]; then
    echo "Cloning official ringover-streamer..."
    git clone https://github.com/ringover/ringover-streamer.git external/ringover-streamer
else
    echo "ringover-streamer already exists, updating..."
    cd external/ringover-streamer
    git pull origin main || git pull origin master
    cd ../..
fi

# Install ringover-streamer dependencies
echo "Installing ringover-streamer dependencies..."
cd external/ringover-streamer
# Use the virtual environment if available
if [ -f "../../.venv/bin/pip" ]; then
    ../../.venv/bin/pip install -r requirements.txt
else
    pip install -r requirements.txt
fi
cd ../..

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    echo "Installing uvicorn..."
    pip install uvicorn
fi

echo "=== Setup Complete ==="
echo ""
echo "The official ringover-streamer is now installed in: external/ringover-streamer"
echo "You can start the integration using the RingoverIntegration class."
echo ""
echo "Required environment variables:"
echo "  RINGOVER_API_KEY=your_api_key"
echo "  RINGOVER_WEBHOOK_SECRET=your_webhook_secret"
echo "  OPENAI_API_KEY=your_openai_key (for LLM)"
echo "  ELEVENLABS_API_KEY=your_elevenlabs_key (for TTS)"
echo ""
echo "The ringover-streamer will be automatically managed by the integration."
