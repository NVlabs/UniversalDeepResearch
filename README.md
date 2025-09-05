# Universal Deep Research (UDR)

A prototype research system that combines user-defined strategies, intelligent web search, content analysis, and automated report generation using large language models. This repository contains both the backend API service and frontend web interface.

As mentioned above, this is a research demonstration prototype and should not be used for production purposes. The software contains experimental features and research-grade implementations.

## Project Structure

```
/
├── backend/          # FastAPI backend service
│   ├── README.md     # Backend setup and configuration
│   ├── main.py       # FastAPI application
│   ├── scan_research.py  # Core research logic
│   ├── frame/        # Advanced reliability framework
│   └── ...
├── frontend/         # Next.js frontend application
│   ├── README.md     # Frontend setup and configuration
│   ├── src/          # React components and pages
│   └── ...
└── README.md         # This file
```

## Getting Started

### Nebius AI Studio quickstart (OpenAI-compatible)

- Set NEBIUS_API_KEY in backend/.env and choose DEFAULT_MODEL=nebius-kimi-k2.
- Use FRAME_BASE_URL=https://api.studio.nebius.com/v1/ and FRAME_MODEL=moonshotai/Kimi-K2-Instruct.
- Frontend: NEXT_PUBLIC_API_VERSION=v1, NEXT_PUBLIC_ENABLE_V2_API=false, DRY_RUN=true (no Tavily) or false (with Tavily).
- See Nebius AI Studio Cookbook for more examples: https://github.com/nebius/ai-studio-cookbook


To run the prototype, you need to start both the backend and frontend services:

### 1. Backend Setup

Navigate to the backend directory and follow the setup instructions:

```bash
cd backend
```

See [backend/README.md](backend/README.md) for detailed setup instructions, including:

- Python environment setup
- API key configuration
- Server startup commands

### 2. Frontend Setup

In a new terminal, navigate to the frontend directory:

```bash
cd frontend
```

See [frontend/README.md](frontend/README.md) for detailed setup instructions, including:

- Node.js dependencies installation
- Environment configuration
- Development server startup

### 3. Running the Prototype

1. **Start the backend server** (typically on port 8000):

   ```bash
   cd backend
   launch_server.sh
   ```

2. **Start the frontend development server** (typically on port 3000):

   ```bash
   cd frontend
   npm run dev
   ```

3. **Access the application**:
   Open your browser and navigate to `http://localhost:3000` or similar as output by the terminal.

## Features

- **Intelligent Research**: User-configurable research strategies
- **Real-time Progress**: Live updates during research and report generation
- **Interactive Interface**: Modern web UI for research queries and results
- **Multi-Model Support**: Configurable LLM backends

## Documentation

- [Backend Documentation](backend/README.md) - API setup, configuration, and endpoints
- [Frontend Documentation](frontend/README.md) - UI setup, configuration, and deployment

## Requirements

- Python 3.8+ (for backend)
- Node.js 18+ (for frontend)
- API keys for LLM providers (e.g., NVIDIA NGC, OpenAI, etc.)
- Tavily API key for web search functionality

## Development

This is a research prototype demonstrating AI-powered research automation concepts. The codebase is structured for experimentation and demonstration rather than production deployment.
