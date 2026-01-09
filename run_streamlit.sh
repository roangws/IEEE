#!/bin/bash

# Unset existing API keys to ensure .env file takes precedence
unset OPENAI_API_KEY
unset ANTHROPIC_API_KEY

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✅ Loaded environment variables from .env"
else
    echo "⚠️  No .env file found - using default environment"
fi

# Check if OPENAI_API_KEY is set
if [ -n "$OPENAI_API_KEY" ]; then
    echo "✅ OPENAI_API_KEY is set (first 10 chars: ${OPENAI_API_KEY:0:10}...)"
else
    echo "⚠️  OPENAI_API_KEY not set - OpenAI integration may fail"
fi

# Start Streamlit
echo "🚀 Starting Streamlit on http://localhost:8501"
./venv/bin/streamlit run app.py --server.headless true --server.port 8501
