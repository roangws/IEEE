# Academic Paper Analysis & Generation System

A complete RAG (Retrieval-Augmented Generation) system for analyzing 5,000+ academic PDFs with AI-powered Q&A and article synthesis capabilities.

## 🌟 Features

- **Semantic Search**: Find relevant information across thousands of papers using vector embeddings
- **AI-Powered Q&A**: Ask questions and get answers with citations from academic papers
- **Article Synthesis**: Generate comprehensive academic articles by synthesizing multiple papers
- **Multiple LLM Support**: Choose between Ollama (local/free), OpenAI GPT, or Claude
- **Web Interface**: Beautiful Streamlit UI for easy interaction
- **Customizable Templates**: Edit article generation templates to match your needs

## 📋 Prerequisites

1. **Python 3.8+**
2. **Qdrant Vector Database**
   ```bash
   # Install and run Qdrant locally using Docker
   docker pull qdrant/qdrant
   docker run -p 6333:6333 qdrant/qdrant
   ```

3. **Ollama (for local LLM)**
   ```bash
   # Install Ollama from https://ollama.ai
   # Pull the Qwen model
   ollama pull qwen2.5:7b
   ```

4. **API Keys (Optional)**
   - OpenAI API key for GPT models
   - Anthropic API key for Claude models

## 🚀 Installation

1. **Clone or navigate to the repository**
   ```bash
   cd /Users/roan-aparavi/aparavi-repo/Roan-IEEE
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up API keys (optional)**
   ```bash
   export OPENAI_API_KEY="your-openai-key"
   export ANTHROPIC_API_KEY="your-anthropic-key"
   ```

## 📚 Usage

### Step 1: Ingest PDFs into Vector Database

Process your PDFs and create embeddings:

```bash
python ingest.py
```

**Options:**
```bash
python ingest.py --help

# Custom PDF directory
python ingest.py --pdf-dir /path/to/pdfs

# Custom chunk size
python ingest.py --chunk-size 1500 --chunk-overlap 150

# Custom Qdrant settings
python ingest.py --qdrant-host localhost --qdrant-port 6333

# Skip ingestion (if already done)
python ingest.py --skip-ingest
```

**What it does:**
- Reads all PDFs from `downloaded_pdfs/` folder
- Extracts text using PyMuPDF
- Chunks text into 1000-character segments with 100-character overlap
- Creates embeddings using Nomic Embed model
- Stores in Qdrant vector database
- Shows progress bar and statistics

### Step 2: Launch Web Interface

Start the Streamlit app:

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Step 3: Use the System

#### **Q&A Analysis Tab**
1. Enter your question about the papers
2. Adjust retrieval settings (optional)
3. Click "Search & Answer"
4. View answer with citations and source excerpts

#### **Article Generation Tab**
1. Select your preferred LLM (Ollama/OpenAI/Claude)
2. Describe the article topic
3. Customize the template (optional)
4. Set word count, tone, and number of sources
5. Click "Generate Article"
6. Download the generated article as Markdown

## 🧪 Command-Line Testing

### Test Query Engine
```bash
python query.py "What are the main approaches to neural network optimization?"
```

### Test Individual Components
```python
# Test search
from query import search_and_answer

result = search_and_answer("What is transfer learning?")
print(result['answer'])
print(result['sources'])
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Web UI (app.py)               │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │   Q&A Section    │         │ Article Generator │         │
│  └──────────────────┘         └──────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Query Engine (query.py)                        │
│  • Semantic Search  • Context Formatting  • LLM Prompting   │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│   Qdrant Vector Store     │   │   LLM APIs (config.py)    │
│  • 5000+ PDF chunks       │   │  • Ollama (local)         │
│  • Nomic embeddings       │   │  • OpenAI GPT             │
│  • Cosine similarity      │   │  • Claude                 │
└───────────────────────────┘   └───────────────────────────┘
                ▲
                │
┌───────────────────────────┐
│  PDF Ingestor (ingest.py) │
│  • PyMuPDF extraction     │
│  • Text chunking          │
│  • Batch embedding        │
└───────────────────────────┘
```

## 📁 Project Structure

```
Roan-IEEE/
├── app.py                  # Streamlit web interface
├── ingest.py              # PDF ingestion and vector storage
├── query.py               # Search and answer engine
├── config.py              # LLM configuration and API handlers
├── template.py            # Article generation templates
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── downloaded_pdfs/      # Your PDF files (5000+ papers)
└── venv/                 # Virtual environment
```

## ⚙️ Configuration

### Embedding Model
- **Model**: `nomic-ai/nomic-embed-text-v1.5`
- **Dimension**: 768
- **Prefix for documents**: `"search_document: "`
- **Prefix for queries**: `"search_query: "`

### Chunking Strategy
- **Chunk size**: 1000 characters
- **Overlap**: 100 characters
- **Rationale**: Balances context preservation with retrieval precision

### Vector Database
- **Database**: Qdrant
- **Collection**: `academic_papers`
- **Distance metric**: Cosine similarity
- **Host**: `localhost:6333`

### LLM Models
- **Ollama**: `qwen2.5:7b` (local, free)
- **OpenAI**: `gpt-4o` (requires API key)
- **Claude**: `claude-3-5-sonnet-20241022` (requires API key)

## 🔧 Troubleshooting

### Qdrant Connection Error
```bash
# Make sure Qdrant is running
docker ps | grep qdrant

# If not running, start it
docker run -p 6333:6333 qdrant/qdrant
```

### Ollama Model Not Found
```bash
# Pull the model
ollama pull qwen2.5:7b

# Verify it's installed
ollama list
```

### Out of Memory During Ingestion
```bash
# Reduce batch size
python ingest.py --batch-size 50

# Or process fewer PDFs at a time
```

### Slow Article Generation
- Use Ollama for faster local generation
- Reduce word count target
- Decrease number of sources retrieved

## 📊 Performance

- **Ingestion**: ~2-5 PDFs/second (depends on PDF size)
- **Search**: <1 second for 15 results
- **Q&A Generation**: 5-30 seconds (depends on LLM)
- **Article Generation**: 1-3 minutes (depends on LLM and length)

## 🎯 Example Use Cases

1. **Literature Review**: "What are the current approaches to explainable AI?"
2. **Methodology Research**: "Compare different neural architecture search methods"
3. **Survey Article**: Generate a 3000-word survey on "Transformer models in computer vision"
4. **Technical Analysis**: "What are the limitations of current reinforcement learning algorithms?"

## 🛠️ Advanced Usage

### Custom Templates
Edit the template in the web UI or modify `template.py` to create custom article structures.

### Batch Processing
```python
from query import search_and_answer

questions = [
    "What is attention mechanism?",
    "How does BERT work?",
    "What is transfer learning?"
]

for q in questions:
    result = search_and_answer(q)
    print(f"Q: {q}\nA: {result['answer']}\n")
```

### Export Results
The web UI allows downloading generated articles as Markdown files.

## 📝 Notes

- First ingestion takes time but only needs to be done once
- Embeddings are stored persistently in Qdrant
- You can add more PDFs by re-running ingestion (it will ask to recreate collection)
- Local Ollama is free but slower than cloud APIs
- Cloud APIs (OpenAI/Claude) are faster but require payment

## 🤝 Support

For issues or questions:
1. Check Qdrant is running: `curl http://localhost:6333`
2. Verify Ollama is running: `ollama list`
3. Check Python dependencies: `pip list`

## 📄 License

This project is for academic and research purposes.

---

**Built with**: Python, Streamlit, Qdrant, Sentence Transformers, Ollama, OpenAI, Anthropic
