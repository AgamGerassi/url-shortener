#!/bin/bash
set -e

echo "=== URL Shortener Setup ==="

# 1. Check Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed. Please install Docker first."
    exit 1
fi
echo "✅ Docker found"

# 2. Install docker-compose-plugin if missing
if ! docker compose version &> /dev/null; then
    echo "Installing docker-compose-plugin..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq docker-compose-plugin
fi
echo "✅ Docker Compose found"

# 3. Install docker-buildx-plugin if missing
if ! docker buildx version &> /dev/null; then
    echo "Installing docker-buildx-plugin..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq docker-buildx-plugin

    # If apt install failed, install manually
    if ! docker buildx version &> /dev/null; then
        echo "Installing buildx manually..."
        mkdir -p ~/.docker/cli-plugins
        ARCH=$(dpkg --print-architecture)
        curl -sSL "https://github.com/docker/buildx/releases/latest/download/buildx-v0.19.4.linux-${ARCH}" -o ~/.docker/cli-plugins/docker-buildx
        chmod +x ~/.docker/cli-plugins/docker-buildx
    fi
fi
echo "✅ Docker Buildx found"

# 4. Check .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found."
    echo "Please create it first:  cp .env.example .env"
    exit 1
fi
echo "✅ .env file ready"

# 5. Build and start
echo ""
echo "Building and starting services..."
docker compose up --build -d

# 6. Wait for health
echo ""
echo "Waiting for services to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        echo "✅ All services are healthy!"
        echo ""
        echo "=== Ready! ==="
        echo "API:    http://localhost:8000"
        echo "Health: http://localhost:8000/health"
        if grep -q 'ENVIRONMENT=development' .env; then
            echo "Docs:   http://localhost:8000/docs"
        fi
        echo ""
        echo "Try it:"
        echo "  curl -X POST http://localhost:8000/shorten -H 'Content-Type: application/json' -d '{\"url\": \"https://www.google.com\"}'"
        exit 0
    fi
    sleep 2
    echo "  waiting... ($i/30)"
done

echo "⚠️  Services are taking longer than expected. Check logs with:"
echo "  docker compose logs"
