# Universal Deep Research Backend (UDR-B)

A FastAPI-based backend service that provides intelligent research and reporting capabilities using large language models and web search APIs. The system can perform comprehensive research on user queries, aggregate findings, and generate detailed reports.

This software is provided exclusively for research and demonstration purposes. It is intended solely as a prototype to demonstrate research concepts and methodologies in artificial intelligence and automated research systems.

- This software is not intended for production deployment, commercial use, or any real-world application where reliability, accuracy, or safety is required.
- This software contains experimental features, unproven methodologies, and research-grade implementations that may contain bugs, security vulnerabilities, or other issues.
- The software is provided "AS IS" without any warranties. Neither NVIDIA Corporation nor the authors shall be liable for any damages arising from the use of this software to the fullest extent permitted by law.

By using this software, you acknowledge that you have read and understood the complete DISCLAIMER file and agree to be bound by its terms. For the complete legal disclaimer, please see the [DISCLAIMER](DISCLAIMER.txt) file in this directory.

## Features

- **Intelligent Research**: Automated web search and content analysis using Tavily API
- **Multi-Model Support**: Configurable LLM backends (OpenAI, NVIDIA, local vLLM)
- **Streaming Responses**: Real-time progress updates via Server-Sent Events
- **Session Management**: Persistent research sessions with unique identifiers
- **Flexible Architecture**: Modular design with configurable components
- **Dry Run Mode**: Testing capabilities with mock data
- **Advanced Framing**: Custom FrameV4 system for increased reliability of instruction following across all models

## Architecture

The backend consists of several key components:

- **`main.py`**: FastAPI application with research endpoints
- **`scan_research.py`**: Core research and reporting logic
- **`clients.py`**: LLM and search API client management
- **`frame/`**: Advanced reliability framework (FrameV4)
- **`items.py`**: Data persistence utilities
- **`sessions.py`**: Session key generation and management

## Quick Start

### Prerequisites

- Python 3.8+
- API keys for your chosen LLM provider
- Tavily API key for web search functionality

### Installation

#### Option 1: Automated Setup (Recommended)

The easiest way to set up the backend is using the provided `setup.py` script:

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Run the setup script**:

   ```bash
   python3 setup.py
   ```

   The setup script will:

   - Check Python version compatibility
   - Create necessary directories (`logs/`, `instances/`, `mock_instances/`)
   - Set up environment configuration (`.env` file)
   - Check for required API key files
   - Install Python dependencies
   - Validate the setup

3. **Configure API keys**:
   Create the following files with your API keys:

   ```bash
   echo "your-tavily-api-key" > tavily_api.txt
   echo "your-llm-api-key" > nvdev_api.txt  # or openai_api.txt
   ```

4. **Start the server**:

   ```bash
   ./launch_server.sh
   ```

   **Note**: The `launch_server.sh` script is the recommended way to start the server as it:

   - Automatically loads environment variables from `.env`
   - Sets proper default configurations
   - Runs the server in the background with logging
   - Provides process management information

#### Option 2: Manual Setup

If you prefer to set up the backend manually, follow these steps:

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Create virtual environment**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Create necessary directories**:

   ```bash
   mkdir -p logs instances mock_instances
   ```

5. **Set up environment configuration**:
   Copy the example environment file and configure it:

   ```bash
   cp env.example .env
   # Edit .env file with your configuration
   ```

6. **Configure API keys**:
   Create the following files with your API keys:

   ```bash
   echo "your-tavily-api-key" > tavily_api.txt
   echo "your-llm-api-key" > nvdev_api.txt  # or e.g., openai_api.txt
   ```

7. **Start the server**:

   ```bash
   ./launch_server.sh
   ```

   **Note**: As noted for Option 1, the `launch_server.sh` script is the recommended way to start the server as it:

   - Automatically loads environment variables from `.env`
   - Sets proper default configurations
   - Runs the server in the background with logging
   - Provides process management information

The server will be available at `http://localhost:8000`

You can now quickly test the server.

```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What are the latest developments in quantum computing?",
    "start_from": "research"
  }'
```

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Server Configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info

# CORS Configuration
FRONTEND_URL=http://localhost:3000

# Model Configuration
DEFAULT_MODEL=llama-3.1-nemotron-253b
LLM_BASE_URL=https://integrate.api.nvidia.com/v1
LLM_API_KEY_FILE=nvdev_api.txt

# Search Configuration
TAVILY_API_KEY_FILE=tavily_api.txt

# Research Configuration
MAX_TOPICS=1
MAX_SEARCH_PHRASES=1
MOCK_DIRECTORY=mock_instances/stocks_24th_3_sections

# Logging Configuration
LOG_DIR=logs
TRACE_ENABLED=true
```

### Model Configuration

The system supports multiple LLM providers. Configure models in `clients.py`:

```python
MODEL_CONFIGS = {
    "llama-3.1-8b": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "api_type": "nvdev",
        "completion_config": {
            "model": "nvdev/meta/llama-3.1-8b-instruct",
            "temperature": 0.2,
            "top_p": 0.7,
            "max_tokens": 2048,
            "stream": True
        }
    },
    # Add more models as needed
}
```

### API Key Files

The system expects API keys in text files:

- `tavily_api.txt`: Tavily search API key
- `nvdev_api.txt`: NVIDIA API key
- `openai_api.txt`: OpenAI API key

## API Endpoints

### GET `/`

Health check endpoint that returns a status message.

### POST `/api/research`

Main research endpoint that performs research and generates reports.

**Request Body**:

```json
{
  "dry": false,
  "session_key": "optional-session-key",
  "start_from": "research",
  "prompt": "Your research query here",
  "mock_directory": "mock_instances/stocks_24th_3_sections"
}
```

**Parameters**:

- `dry` (boolean): Use mock data for testing
- `session_key` (string, optional): Existing session to continue
- `start_from` (string): "research" or "reporting"
- `prompt` (string): Research query (required for research phase)
- `mock_directory` (string): Directory for mock data

**Response**: Server-Sent Events stream with research progress

### POST `/api/research2`

Advanced reliability framework endpoint using FrameV4 system. This is the endpoint that supports custom user deep research strategies.

**Request Body**:

```json
{
  "prompt": "Your research query",
  "strategy_id": "custom-strategy",
  "strategy_content": "Custom research strategy"
}
```

## Usage Examples

### Basic Research Request

```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What are the latest developments in quantum computing?",
    "start_from": "research"
  }'
```

### Dry Run Testing

```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{
    "dry": true,
    "prompt": "Test research query",
    "start_from": "research"
  }'
```

### Continue from Reporting Phase

```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{
    "session_key": "20241201T120000Z-abc12345", # This would be the key of the session which you have previously started
    "start_from": "reporting"
  }'
```

## Development

### Logging

Logs are stored in the `logs/` directory:

- `comms_YYYYMMDD_HH-MM-SS.log`: Communication traces
- `{instance_id}_compilation.log`: Frame compilation logs
- `{instance_id}_execution.log`: Frame execution logs

### Mock Data

Mock research data is available in `mock_instances/`:

- `stocks_24th_3_sections/`: Stock market research data
- `stocks_30th_short/`: Short stock market data

## Deployment

### Production Deployment

1. **Set up environment**:

   ```bash
   export HOST=0.0.0.0
   export PORT=8000
   export LOG_LEVEL=info
   ```

2. **Run with gunicorn**:

   ```bash
   pip install gunicorn
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

   **Note**: For development, prefer using `./launch_server.sh` which provides better process management and logging.

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure API key files exist and contain valid keys
2. **CORS Errors**: Check `FRONTEND_URL` configuration
3. **Model Errors**: Verify model configuration in `clients.py`
4. **Permission Errors**: Ensure write permissions for `logs/` and `instances/` directories

### Debug Mode

Enable debug logging by setting the LOG_LEVEL environment variable:

```bash
export LOG_LEVEL=debug
./launch_server.sh
```

Or run uvicorn directly for debugging:

```bash
uvicorn main:app --reload --log-level=debug
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License and Disclaimer

This software is provided for research and demonstration purposes only. Please refer to the [DISCLAIMER](DISCLAIMER.txt) file for complete terms and conditions regarding the use of this software. You can find the license in [LICENSE](LICENSE.txt).

**Do not use this code in production.**

## Support

For issues and questions:

- Create an issue in the repository
- Check the logs in the `logs/` directory
- Review the configuration settings

### Nebius AI Studio (OpenAI-compatible)

To run the v1 endpoint with Nebius as the default LLM:

1) Copy env and set CORS to your frontend port (e.g., 3004):

```bash
cp env.example .env
sed -i '' 's#^FRONTEND_URL=.*#FRONTEND_URL=http://localhost:3004#' .env
```

2) Set Nebius defaults and provide the key (no quotes):

```bash
sed -i '' 's#^DEFAULT_MODEL=.*#DEFAULT_MODEL=nebius-kimi-k2#' .env
# NEBIUS_API_KEY=your-nebius-api-key
# FRAME_BASE_URL=https://api.studio.nebius.com/v1/
# FRAME_MODEL=moonshotai/Kimi-K2-Instruct
```

3) Start:

```bash
./launch_server.sh
```

Notes: Tavily search optional via tavily_api.txt.
