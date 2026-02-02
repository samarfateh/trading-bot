#!/bin/bash

# deploy_server.sh
# Run this on your VPS to set up the environment.

set -e

echo "=== 1. Checking for Docker ==="
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    # Add current user to docker group to avoid sudo usage
    sudo usermod -aG docker $USER || true
    echo "Docker installed. You may need to log out and back in for group changes to take effect."
else
    echo "Docker is already installed."
fi

echo "=== 2. Building and Starting Trading Bot ==="
# Ensure we are in the directory with docker-compose.yml
cd "$(dirname "$0")"

if [ ! -f "docker-compose.yml" ]; then
    echo "Error: docker-compose.yml not found in current directory."
    exit 1
fi

echo "Building container..."
sudo docker compose build

echo "Starting container..."
sudo docker compose up -d

echo "Trading Bot is running on port 8080."
echo "Check logs with: sudo docker compose logs -f"

echo "=== 3. OpenClaw Setup Instructions ==="
echo "To install OpenClaw (The AI Agent):"
echo "Run: curl -fsSL https://openclaw.ai/install.sh | bash"
echo "Then: openclaw onboard"
echo "DURING ONBOARDING:"
echo " - select 'Local' gateway"
echo " - select 'Ollama' (if you installed it) or 'Anthropic'/'OpenAI' (recommended for cheap servers)"
echo " - Ensure you pair it with Discord/WhatsApp."

echo "=== Done ==="
