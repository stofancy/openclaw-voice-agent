# Voice Gateway

Audio proxy service with WebRTC, STT (Speech-to-Text), and TTS (Text-to-Speech) capabilities.

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Development

```bash
# Run tests
pytest

# Run the application
python -m voice_gateway.main
```

## Configuration

The application can be configured using environment variables:

- `DEBUG`: Enable debug mode (default: false)
- `HOST`: Host to bind to (default: 0.0.0.0)
- `PORT`: Port to listen on (default: 8080)
- `STT_SERVICE_URL`: URL for STT service (default: http://localhost:8081)
- `TTS_SERVICE_URL`: URL for TTS service (default: http://localhost:8082)
- `AGENT_SERVICE_URL`: URL for Agent service (default: http://localhost:8083)