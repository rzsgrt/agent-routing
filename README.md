# AI Agent Backend

A FastAPI-based backend that routes natural language queries to appropriate tools (Weather, Math, LLM).

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configuration

Copy the example environment file:
```bash
cp env.example .env
```

Edit `.env` with your settings:
```env
# Application Settings
APP_NAME=AI Agent Backend
APP_VERSION=1.0.0
DEBUG=false

# LM Studio Settings (local LLM)
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=local-model
LM_STUDIO_API_KEY=lm-studio

# Weather API Settings
# Get your free API key from: https://openweathermap.org/api
OPENWEATHER_API_KEY=your_openweather_api_key_here

# Location Settings  
DEFAULT_LOCATION=Jakarta

# Agent Settings
AGENT_TIMEOUT=30
```

### 3. Run the Application

#### Option A: Direct Python
```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Option B: Docker (Recommended)
```bash
# Quick start with helper script (recommended)
./run-docker.sh

# Or simple Docker run (uses defaults from env.example)
docker build -t ai-agent-backend .
docker run -d --name ai-agent -p 8000:8000 ai-agent-backend

# Or with custom environment variables
docker run -d --name ai-agent -p 8000:8000 \
  -e OPENWEATHER_API_KEY=your_actual_api_key \
  -e LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1 \
  ai-agent-backend
```

The API will be available at: http://localhost:8000

**Note**: Environment variables are optional. The container uses defaults from `env.example`. Override them only when needed:
- `OPENWEATHER_API_KEY`: Required for weather queries
- `LM_STUDIO_BASE_URL`: Required for LLM functionality (routing and general chat)
  - For Docker: Use `http://host.docker.internal:1234/v1`
  - For direct Python: Use `http://localhost:1234/v1`
- `DEFAULT_LOCATION`: Optional, defaults to Jakarta

### 4. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Math query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is 42 * 7?"}'

# Weather query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the weather in London?"}'

# General query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Tell me a joke"}'
```

## API Documentation

### POST /query

**Request:**
```json
{
  "query": "What's the weather in Paris?"
}
```

**Response:**
```json
{
  "query": "What's the weather in Paris?",
  "tool_used": "weather",
  "result": "The weather in Paris is currently 22°C with partly cloudy skies..."
}
```

### GET /health

**Response:**
```json
{
  "status": "healthy"
}
```

## Prerequisites

- **Python 3.11+**
- **LM Studio** running locally (for general LLM functionality and routing)
- **OpenWeather API Key** (free from [openweathermap.org](https://openweathermap.org/api))

## Architecture

```
app/
├── main.py              # FastAPI application
├── models.py            # Pydantic request/response models
├── config.py            # Configuration management
├── logging_config.py    # Logging setup
├── agents/
│   └── main_agent.py    # Main routing agent
└── tools/
    ├── base.py          # Base tool class
    ├── math_tool.py     # Mathematical calculations
    ├── weather_tool.py  # Weather information
    └── general_tool.py  # LLM conversations
```

## Docker Commands

### Build and Run
```bash
# Build the image
docker build -t ai-agent-backend .

# Simple run (uses defaults)
docker run -d --name ai-agent -p 8000:8000 ai-agent-backend

# Run with custom environment variables (when needed)
docker run -d \
  --name ai-agent \
  --restart unless-stopped \
  -p 8000:8000 \
  -e OPENWEATHER_API_KEY=your_actual_api_key \
  -e LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1 \
  -e DEFAULT_LOCATION=London \
  ai-agent-backend
```

### Management Commands
```bash
# View logs
docker logs ai-agent -f

# Check container status
docker ps

# Stop container
docker stop ai-agent

# Remove container
docker rm ai-agent

# Rebuild and restart
docker stop ai-agent && docker rm ai-agent && \
docker build -t ai-agent-backend . && \
docker run -d --name ai-agent -p 8000:8000 \
  -e OPENWEATHER_API_KEY=your_actual_api_key \
  -e LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1 \
  ai-agent-backend
```

## Development

### Running Tests
```bash
pytest tests/ -v
```
