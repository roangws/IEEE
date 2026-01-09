#!/bin/bash
# Setup script for Academic Paper Analysis & Generation System

set -e  # Exit on error

echo "=========================================="
echo "Academic Paper RAG System Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet
echo "✓ pip upgraded"
echo ""

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Check Qdrant
echo "Checking Qdrant connection..."
if curl -s http://localhost:6333 > /dev/null 2>&1; then
    echo "✓ Qdrant is running at localhost:6333"
else
    echo "⚠ Qdrant is not running!"
    echo ""
    echo "To start Qdrant, run:"
    echo "  docker run -p 6333:6333 qdrant/qdrant"
    echo ""
fi

# Check Ollama
echo "Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    echo "✓ Ollama is installed"
    
    # Check if qwen2.5:7b is available
    if ollama list | grep -q "qwen2.5:7b"; then
        echo "✓ qwen2.5:7b model is available"
    else
        echo "⚠ qwen2.5:7b model not found"
        echo ""
        echo "To install the model, run:"
        echo "  ollama pull qwen2.5:7b"
        echo ""
    fi
else
    echo "⚠ Ollama is not installed"
    echo ""
    echo "To install Ollama, visit: https://ollama.ai"
    echo ""
fi

# Check API keys
echo "Checking API keys..."
if [ -n "$OPENAI_API_KEY" ]; then
    echo "✓ OPENAI_API_KEY is set"
else
    echo "ℹ OPENAI_API_KEY not set (optional)"
fi

if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "✓ ANTHROPIC_API_KEY is set"
else
    echo "ℹ ANTHROPIC_API_KEY not set (optional)"
fi
echo ""

# Count PDFs
pdf_count=$(find downloaded_pdfs -name "*.pdf" 2>/dev/null | wc -l | tr -d ' ')
echo "Found $pdf_count PDF files in downloaded_pdfs/"
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Make sure Qdrant is running:"
echo "   docker run -p 6333:6333 qdrant/qdrant"
echo ""
echo "2. Ingest PDFs into vector database:"
echo "   python ingest.py"
echo ""
echo "3. Launch the web interface:"
echo "   streamlit run app.py"
echo ""
echo "Or test the query engine:"
echo "   python query.py 'What is machine learning?'"
echo ""
echo "=========================================="
