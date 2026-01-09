# Academic Paper Analysis & Generation System

**By Roan Guilherme Weigert Salgueiro**

An advanced RAG (Retrieval-Augmented Generation) system that analyzes 5,634 academic papers using AI-powered analytics, quality metrics assessment, and automated article generation. Built with multi-layer architecture and external reference integration.

## 🌟 Key Highlights

### 📊 **Advanced Analytics & Quality Assessment** (Primary Feature)
Comprehensive analysis engine that evaluates academic papers across multiple dimensions:
- **Reproducibility Metrics**: Code availability, random seeds, error reporting
- **Statistical Rigor**: Mathematical content density, statistical tests, p-values
- **Research Quality**: Comparisons, ablation studies, contribution statements
- **Citation Network Analysis**: 224,859 references analyzed across corpus
- **Readability Assessment**: Flesch scores, grade levels, clarity metrics
- **Pattern Detection**: IEEE structure compliance, common methodologies

### ✍️ **Multi-Layer Article Generation**
4-layer system producing IEEE-formatted academic articles:
- **Layer 1**: Intelligent outline generation from research topics
- **Layer 2a**: External reference fetching via Semantic Scholar API
- **Layer 2b**: Draft generation with proper citations
- **Layer 3**: Content refinement and quality enhancement
- **Layer 4**: IEEE two-column formatting with MathJax equations

### 🔍 **Intelligent Q&A & Research Tools**
- Semantic search across 5,634 papers using vector embeddings
- AI-powered answers with inline citations and source excerpts
- Theme extraction and trend analysis
- Paper explorer with advanced filtering
- Batch processing capabilities

## 📊 Analysis Results & Corpus Metrics

### 📚 Dataset Scale
- **Total Papers Indexed**: 5,634 academic papers
- **Comprehensive Analysis**: 200 papers (structure) + 100 papers (quality metrics)
- **Citation Network**: 224,859 references analyzed
- **Average Paper Length**: 7,414 words | 7.42 sections

### 🔬 Quality Metrics Analysis (100 Papers)

| Category | Key Findings |
|----------|-------------|
| **Mathematical Rigor** | 98% contain math content (avg 39.56 indicators/paper)<br>98% use statistical tests (avg 8.63 keywords/paper) |
| **Reproducibility** | 30% provide code/GitHub links<br>42% report multiple runs<br>50% include error reporting (std, confidence intervals) |
| **Research Quality** | 97% include comparative analysis (avg 8.08 comparisons)<br>83% make novel claims, 49% claim SOTA<br>87% mention limitations, 27% include ablation studies |
| **Content Depth** | Avg 22.9 figures, 14.71 tables per paper<br>29.88 dataset mentions, 35% use known datasets<br>4.79 unique performance metrics per paper |
| **Readability** | Flesch Reading Ease: 42.31 (College level)<br>Flesch-Kincaid Grade: 9.63 (9th-10th grade) |

### 📖 IEEE Paper Structure Analysis (200 Papers)
| Section | Frequency | Section | Frequency |
|---------|-----------|---------|----------|
| Abstract | 100% | Conclusion | 81% |
| Introduction | 100% | Experiments | 62.5% |
| References | 100% | Methodology | 55% |
| Results | 99.5% | Discussion | 40.5% |
| Approach/Method | 95% | Background | 34% |

### 📚 Citation Network Insights
- **Top Publishers**: IEEE (63,412 refs), arXiv (15,315), ACM (14,626), Springer (4,392)
- **Most Influential Papers in Corpus**:
  1. Attention Is All You Need (Vaswani et al.) - 149 citations
  2. Adam Optimizer (Kingma & Ba) - 140 citations
  3. ResNet (He et al.) - 126 citations
  4. Dropout (Srivastava et al.) - 111 citations
  5. Batch Normalization (Ioffe & Szegedy) - 107 citations

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Docker (for Qdrant vector database)
- Ollama (for local LLM) or API keys for OpenAI/Claude

### Installation
```bash
# Setup environment
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Ingest papers and launch app
python ingest.py
streamlit run app.py
```

## 💡 Usage

The system provides **5 main interfaces** accessible via Streamlit tabs:

1. **📊 Article Analysis** - Run quality metrics, reproducibility checks, citation analysis
2. **✍️ Article Generation** - Generate IEEE-formatted papers with 4-layer system
3. **🔍 Q&A Analysis** - Ask questions, get cited answers from corpus
4. **🔬 Research Analysis** - Extract themes, trends, and patterns
5. **📚 Paper Explorer** - Browse, filter, and explore the paper collection

**Command-Line Analysis:**
```bash
# Run quality metrics on papers
python analyze_quality_metrics.py

# Analyze citation patterns
python analyze_references_in_bibliographies.py

# Q&A from command line
python query.py "What are the main approaches to neural network optimization?"
```

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    Streamlit Web UI (app.py)                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │ Article  │ │   Q&A    │ │ Research │ │  Paper   │ │ Article  │     │
│  │   Gen    │ │ Analysis │ │ Analysis │ │ Explorer │ │ Analysis │     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌────────────────────┐   ┌─────────────────────┐   ┌──────────────────────┐
│ Multi-Layer        │   │  Query Engine       │   │ Analysis Engine      │
│ Article Generator  │   │  (query.py)         │   │ (analyze_*.py)       │
│                    │   │                     │   │                      │
│ • Layer 1: Outline │   │ • Semantic Search   │   │ • Quality Metrics    │
│ • Layer 2a: Fetch  │   │ • Context Format    │   │ • Citation Analysis  │
│   External Refs    │   │ • LLM Prompting     │   │ • Pattern Detection  │
│ • Layer 2b: Draft  │   │ • Source Ranking    │   │ • Theme Extraction   │
│ • Layer 3: Refine  │   └─────────────────────┘   └──────────────────────┘
│ • Layer 4: Format  │              │                         │
└────────────────────┘              │                         │
         │                          │                         │
         └──────────────────────────┼─────────────────────────┘
                                    ▼
                    ┌───────────────────────────────┐
                    │   External APIs & Services    │
                    │  • Semantic Scholar API       │
                    │  • Reference Integration      │
                    │  • Metadata Enrichment        │
                    └───────────────────────────────┘
                                    │
                ┌───────────────────┴───────────────────┐
                ▼                                       ▼
┌───────────────────────────┐           ┌───────────────────────────┐
│   Qdrant Vector Store     │           │   LLM APIs (config.py)    │
│  • 5,634 PDF chunks       │           │  • Ollama (local)         │
│  • Nomic embeddings       │           │  • OpenAI GPT-4o          │
│  • Cosine similarity      │           │  • Claude 3.5 Sonnet      │
│  • Semantic search        │           │  • Token tracking         │
└───────────────────────────┘           └───────────────────────────┘
                ▲
                │
┌───────────────────────────┐
│  PDF Ingestor (ingest.py) │
│  • PyMuPDF extraction     │
│  • Text chunking          │
│  • Batch embedding        │
│  • Progress tracking      │
└───────────────────────────┘
```

## 📁 Project Structure

```
Roan-IEEE/
├── app.py                              # Main Streamlit web interface
├── ingest.py                          # PDF ingestion and vector storage
├── query.py                           # Search and answer engine
├── config.py                          # LLM configuration and API handlers
├── template.py                        # Article generation templates
│
├── Multi-Layer Article Generation:
│   ├── layer1_outline_ui.py          # Layer 1: Outline generation
│   ├── layer2_external_ui.py         # Layer 2a: External reference fetching
│   ├── layer2_draft_ui.py            # Layer 2b: Draft generation
│   ├── layer3_refine_ui.py           # Layer 3: Content refinement
│   └── layer4_format_ui.py           # Layer 4: IEEE formatting & PDF export
│
├── Analysis Scripts:
│   ├── analyze_ieee_patterns.py      # IEEE paper structure analysis
│   ├── analyze_quality_metrics.py    # Quality metrics computation
│   ├── analyze_references_in_bibliographies.py  # Citation analysis
│   ├── analyze_sample_patterns.py    # Sample pattern detection
│   └── analyze_themes.py             # Theme extraction
│
├── UI Components:
│   ├── article_analysis_ui.py        # Article analysis interface
│   └── article_analysis_ui.py.broken # Backup version
│
├── Configuration:
│   ├── config/
│   │   └── ieee_constraints.py       # IEEE formatting constraints
│   ├── .env                          # Environment variables & API keys
│   └── requirements.txt              # Python dependencies
│
├── Data & Output:
│   ├── downloaded_pdfs/              # 5,634 academic papers
│   ├── output/                       # Analysis results & metrics
│   │   ├── sample_analysis_summary.json
│   │   ├── quality_metrics_summary.json
│   │   ├── references_analysis_summary.json
│   │   └── [additional analysis files]
│   └── venv/                         # Virtual environment
│
└── Documentation:
    ├── README.md                     # This file
    ├── IMPLEMENTATION_COMPLETE.md    # Implementation status
    ├── INTEGRATION_COMPLETE.md       # Integration documentation
    └── [additional documentation]
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

##  Performance

### Core Operations
- **PDF Ingestion**: ~2-5 PDFs/second (depends on PDF size)
- **Semantic Search**: <1 second for 15 results
- **Q&A Generation**: 5-30 seconds (depends on LLM)

### Multi-Layer Article Generation
- **Layer 1 (Outline)**: 10-30 seconds
- **Layer 2a (External References)**: 30-60 seconds (with Semantic Scholar API)
- **Layer 2b (Draft)**: 2-5 minutes (depends on word count and LLM)
- **Layer 3 (Refinement)**: 1-3 minutes
- **Layer 4 (IEEE Formatting)**: 10-30 seconds
- **Total Generation Time**: 4-10 minutes for a complete IEEE-formatted article

### Analysis Operations
- **Quality Metrics Analysis**: ~1-2 seconds per paper
- **Citation Network Analysis**: ~5-10 seconds for full corpus
- **Theme Extraction**: 1-3 minutes (depends on corpus size)
- **Pattern Detection**: 30-60 seconds

### System Capacity
- **Vector Database**: 5,634 papers indexed
- **Total Embeddings**: ~50,000+ text chunks
- **Concurrent Users**: Supports single-user local deployment
- **Memory Usage**: ~2-4 GB RAM (depends on LLM choice)

## 🛠️ Advanced Features

- **Custom Templates**: Modify article structures for different paper types
- **External Reference Integration**: Semantic Scholar API enriches articles with additional citations
- **IEEE Formatting**: Automatic two-column layout with MathJax equations and PDF export
- **Batch Processing**: Analyze multiple papers or run batch Q&A queries
- **Export Options**: Markdown, PDF, JSON, and CSV formats

---

## 🔧 Technology Stack

**Built with**: 
- **Frontend**: Streamlit (Multi-tab interface)
- **Vector Database**: Qdrant (5,634 papers indexed)
- **Embeddings**: Sentence Transformers (Nomic Embed v1.5)
- **LLM Providers**: Ollama (local), OpenAI (GPT-4o), Anthropic (Claude 3.5 Sonnet)
- **External APIs**: Semantic Scholar (reference enrichment)
- **PDF Processing**: PyMuPDF, Pandoc
- **Analysis**: NumPy, Pandas, textstat
- **Formatting**: MathJax, IEEE LaTeX templates

**System Version**: Multi-Layer RAG with External Reference Integration (v2.0)

---

## 👤 Author

**Roan Guilherme Weigert Salgueiro**

*AI/ML Engineer specializing in RAG systems, academic paper analysis, and automated content generation*

This project demonstrates expertise in:
- Large-scale document analysis and quality assessment
- Multi-layer RAG architecture design
- Vector database optimization and semantic search
- LLM integration and prompt engineering
- Academic research automation and IEEE formatting
- Citation network analysis and bibliometric studies
