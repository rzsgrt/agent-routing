#!/bin/bash

# AI Agent Backend - Docker Runner Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="ai-agent-backend"
CONTAINER_NAME="ai-agent"
PORT="8000"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check for OpenWeather API key
if [ -z "$OPENWEATHER_API_KEY" ]; then
    print_warning "OPENWEATHER_API_KEY environment variable not set."
    print_warning "You can:"
    print_warning "1. Set it now: export OPENWEATHER_API_KEY=your_key"
    print_warning "2. Edit .env file after running"
    print_warning "3. Continue without it (weather tool won't work)"
    echo
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Stop and remove existing container if it exists
if docker ps -a --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    print_status "Stopping and removing existing container..."
    docker stop $CONTAINER_NAME > /dev/null 2>&1 || true
    docker rm $CONTAINER_NAME > /dev/null 2>&1 || true
fi

# Build the Docker image
print_status "Building Docker image..."
docker build -t $IMAGE_NAME .

# Run the container
print_status "Starting container..."
docker run -d \
    --name $CONTAINER_NAME \
    --restart unless-stopped \
    -p $PORT:8000 \
    -e OPENWEATHER_API_KEY=${OPENWEATHER_API_KEY:-your_api_key_here} \
    -e LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1 \
    -e DEBUG=false \
    $IMAGE_NAME

# Wait a moment for container to start
sleep 3

# Check if container is running
if docker ps --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    print_status "Container started successfully!"
    echo
    echo "🚀 AI Agent Backend is running!"
    echo "📍 URL: http://localhost:$PORT"
    echo "🏥 Health: http://localhost:$PORT/health"
    echo
    echo "💡 Test commands:"
    echo "   curl http://localhost:$PORT/health"
    echo "   curl -X POST http://localhost:$PORT/query -H 'Content-Type: application/json' -d '{\"query\": \"what is 15 + 25?\"}'"
    echo
    echo "📊 View logs: docker logs $CONTAINER_NAME -f"
    echo "🛑 Stop: docker stop $CONTAINER_NAME"
else
    print_error "Failed to start container!"
    print_error "Check logs: docker logs $CONTAINER_NAME"
    exit 1
fi 