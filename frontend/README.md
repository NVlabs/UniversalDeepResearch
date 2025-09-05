# NVR Universal Deep Research - Frontend

A Next.js frontend application for the NVR Universal Deep Research system that provides an interactive interface for intelligent research and reporting capabilities.

This software is provided exclusively for research and demonstration purposes. It is intended solely as a prototype to demonstrate research concepts and methodologies in artificial intelligence and automated research systems.

- This software is not intended for production deployment, commercial use, or any real-world application where reliability, accuracy, or safety is required.
- This software contains experimental features, unproven methodologies, and research-grade implementations that may contain bugs, security vulnerabilities, or other issues.
- The software is provided "AS IS" without any warranties. Neither NVIDIA Corporation nor the authors shall be liable for any damages arising from the use of this software to the fullest extent permitted by law.

By using this software, you acknowledge that you have read and understood the complete DISCLAIMER file and agree to be bound by its terms. For the complete legal disclaimer, please see the [DISCLAIMER](DISCLAIMER.txt) file in this directory.

## Features

- Interactive research interface with real-time progress tracking
- Configurable research strategies
- Support for both V1 and V2 API endpoints
- Dry run mode for testing
- Real-time report generation and viewing

## Configuration

The frontend application is highly configurable through environment variables. Copy the example environment file and customize it for your deployment:

```bash
cp env.example .env.local
```

### Environment Variables

#### Backend API Configuration

- `NEXT_PUBLIC_BACKEND_BASE_URL`: The base URL of your backend server (default: `http://localhost`)
- `NEXT_PUBLIC_BACKEND_PORT`: The port your backend server is running on (default: `8000`)
- `NEXT_PUBLIC_API_VERSION`: API version to use - `v1` or `v2` (default: `v2`)

#### Runtime Configuration

- `NEXT_PUBLIC_DRY_RUN`: Enable dry run mode - `true` or `false` (default: `false`)
- `NEXT_PUBLIC_ENABLE_V2_API`: Enable V2 API - `true` or `false` (default: `true`)

#### Frontend Configuration

- `NEXT_PUBLIC_FRONTEND_PORT`: The port for the frontend development server (default: `3000`)
- `NEXT_PUBLIC_FRONTEND_HOST`: The host for the frontend development server (default: `localhost`)

### Example Configuration

For a production deployment with a backend on a different server:

```bash
NEXT_PUBLIC_BACKEND_BASE_URL=http://your-backend-server.com
NEXT_PUBLIC_BACKEND_PORT=8000
NEXT_PUBLIC_API_VERSION=v2
NEXT_PUBLIC_DRY_RUN=false
NEXT_PUBLIC_ENABLE_V2_API=true
```

For local development:

```bash
NEXT_PUBLIC_BACKEND_BASE_URL=http://localhost
NEXT_PUBLIC_BACKEND_PORT=8000
NEXT_PUBLIC_API_VERSION=v2
NEXT_PUBLIC_DRY_RUN=true
NEXT_PUBLIC_ENABLE_V2_API=true
```

## Getting Started

1. **Install dependencies:**

   ```bash
   npm install
   ```

2. **Configure environment variables:**

   ```bash
   cp env.example .env.local
   # Edit .env.local with your configuration
   ```

3. **Run the development server:**

   ```bash
   npm run dev
   ```

4. **Open your browser:**
   Navigate to [http://localhost:3000](http://localhost:3000) to see the application.

## Available Scripts

- `npm run dev` - Start the development server with Turbopack
- `npm run build` - Build the application for production
- `npm run start` - Start the production server
- `npm run lint` - Run ESLint

## Project Structure

```
src/
├── app/                 # Next.js app directory
│   ├── page.tsx        # Main application page
│   ├── layout.tsx      # Root layout
│   └── globals.css     # Global styles
├── components/         # React components
│   ├── PromptBar.tsx   # Main input interface
│   ├── ResearchProgressList.tsx  # Progress tracking
│   ├── ReportViewer.tsx # Report display
│   └── ...            # Other UI components
├── config/            # Configuration management
│   └── index.ts       # App configuration
└── types/             # TypeScript type definitions
    └── ApplicationState.ts
```

## Backend Requirements

This frontend requires a compatible backend server running the NVR Universal Deep Research API. The backend should:

- Support both `/api/research` (V1) and `/api/research2` (V2) endpoints
- Accept POST requests with JSON payloads
- Return Server-Sent Events (SSE) for real-time progress updates
- Support the dry run mode parameter

## Deployment

The application can be deployed to any platform that supports Next.js:

1. Build the application: `npm run build`
2. Start the production server: `npm run start`
3. Set the appropriate environment variables for your deployment

### Example Deployment Platforms

- **Vercel**: Connect your Git repository and set environment variables in the dashboard
- **Netlify**: Build and deploy with environment variable configuration
- **Railway**: Deploy with automatic environment variable management
- **Self-hosted**: Run on your own server with proper environment configuration

## Troubleshooting

### Common Issues

1. **Backend Connection Errors**: Ensure your backend server is running and the `NEXT_PUBLIC_BACKEND_BASE_URL` and `NEXT_PUBLIC_BACKEND_PORT` are correctly configured.

2. **CORS Errors**: Make sure your backend server allows requests from your frontend domain.

3. **API Version Issues**: If you're experiencing API compatibility issues, try switching between `v1` and `v2` using the `NEXT_PUBLIC_API_VERSION` environment variable.

### Development Tips

- Use `NEXT_PUBLIC_DRY_RUN=true` during development to avoid making actual API calls
- The application supports hot reloading - changes to your code will be reflected immediately
- Check the browser console for detailed error messages

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License and Disclaimer

This software is provided for research and demonstration purposes only. Please refer to the [DISCLAIMER](DISCLAIMER.txt) file for complete terms and conditions regarding the use of this software. You can find the license in [LICENSE](LICENSE.txt).

**Do not use this code in production.**

### Using Nebius AI Studio (OpenAI-compatible)

Local dev with Nebius v1:

```bash
cp env.example .env.local
sed -i '' 's#^NEXT_PUBLIC_API_VERSION=.*#NEXT_PUBLIC_API_VERSION=v1#' .env.local
sed -i '' 's#^NEXT_PUBLIC_ENABLE_V2_API=.*#NEXT_PUBLIC_ENABLE_V2_API=false#' .env.local
sed -i '' 's#^NEXT_PUBLIC_DRY_RUN=.*#NEXT_PUBLIC_DRY_RUN=false#' .env.local
npm run dev -- -p 3004
```

Backend must be configured with `DEFAULT_MODEL=nebius-kimi-k2` and `NEBIUS_API_KEY` in `backend/.env`.
