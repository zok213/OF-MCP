# 🚀 AI-Driven MCP Web Scraper

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![MCP](https://img.shields.io/badge/MCP-1.1.0-green.svg)
![Jina AI](https://img.shields.io/badge/Jina%20AI-Integrated-orange.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**Professional AI-powered web scraping system that combines intelligent URL discovery with automated image categorization.**

## 🧠 Architecture Overview

This system demonstrates advanced AI engineering by combining:

- **🔍 Jina AI Research** - Intelligent URL discovery and keyword generation
- **🤖 MCP Server Integration** - Model Context Protocol for VS Code
- **🎯 Professional Web Scraping** - Legal compliance and rate limiting
- **👥 Computer Vision** - Face detection and person categorization
- **🗄️ Automated Organization** - Database-ready image management

```
🧠 MCP Server (AI Reasoning)
    ↓ generates intelligent keywords
🔍 Jina AI Research (URL Discovery) 
    ↓ discovers relevant websites
⚡ Professional Filtering (Priority Scoring)
    ↓ selects high-value targets  
📥 Automated Scraping (Legal Compliance)
    ↓ extracts images professionally
👥 Face Detection (OpenCV)
    ↓ identifies and categorizes persons
🗄️ Database Organization (Auto-Storage)
```

## 🚀 Quick Start

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <your-repo-url>
cd mcp-web-scraper

# Create virtual environment
python -m venv venv-mcp-scraper

# Activate environment
# Windows:
venv-mcp-scraper\Scripts\activate
# Linux/Mac:
source venv-mcp-scraper/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# Get Jina AI API key from: https://jina.ai
```

### 3. Configure MCP Settings

```bash
# Copy configuration template
cp config/mcp_config.example.json config/mcp_config.json

# Edit config/mcp_config.json with your settings
```

### 4. Run the System

```bash
# Test the complete system
python tests/test_jina_integration_fixed.py

# Run production pipeline example
python examples/production_ai_pipeline.py

# Start MCP server
python src/server.py
```

## 🛠️ MCP Tools Available

The system provides 6 professional MCP tools:

### 🔍 `intelligent_research`
**NEW**: AI-powered URL discovery using Jina AI
```json
{
  "tool": "intelligent_research",
  "arguments": {
    "topic": "celebrity fashion photos",
    "context": {"style": "editorial", "quality": "high"},
    "jina_api_key": "your_key_here",
    "max_keywords": 8,
    "urls_per_keyword": 10,
    "filter_criteria": {
      "min_priority": 80,
      "exclude_high_risk": true,
      "max_targets": 15
    }
  }
}
```

### 📥 `scrape_website`
Professional web scraping with legal compliance
```json
{
  "tool": "scrape_website", 
  "arguments": {
    "url": "https://example.com",
    "max_images": 50,
    "category": "fashion_photos",
    "check_legal": true
  }
}
```

### 👥 `categorize_images`
Automatic person detection and categorization
```json
{
  "tool": "categorize_images",
  "arguments": {
    "source_folder": "./data/raw/fashion_photos",
    "learn_new_faces": true,
    "min_confidence": 0.8
  }
}
```

### 📊 `get_statistics`
Real-time progress monitoring
```json
{
  "tool": "get_statistics",
  "arguments": {}
}
```

### ⚖️ `check_legal_compliance`
Legal compliance verification
```json
{
  "tool": "check_legal_compliance",
  "arguments": {
    "url": "https://example.com",
    "check_robots": true,
    "analyze_tos": true
  }
}
```

### 📁 `list_categories`
View organized person categories
```json
{
  "tool": "list_categories",
  "arguments": {
    "include_thumbnails": false
  }
}
```

## 🎯 Professional Usage Examples

### Complete AI-Driven Workflow

```python
import asyncio
from src.research.jina_researcher import JinaResearcher

async def intelligent_scraping_workflow():
    # Step 1: AI Research
    async with JinaResearcher("your_jina_key") as researcher:
        research = await researcher.intelligent_research_pipeline(
            "professional celebrity portraits",
            {"style": "editorial"},
            max_keywords=5,
            urls_per_keyword=8
        )
    
    # Step 2: Auto-scrape discovered URLs
    for target in research["filtered_targets"]:
        if target["priority"] >= 80:  # High priority only
            await scrape_website(target["url"])
    
    # Step 3: Auto-categorize by persons
    await categorize_images("./data/raw/")

asyncio.run(intelligent_scraping_workflow())
```

### VS Code Integration

Add to your VS Code settings.json:
```json
{
  "mcp.servers": {
    "web-scraper": {
      "command": "python",
      "args": ["src/server.py"],
      "cwd": "/path/to/mcp-web-scraper"
    }
  }
}
```

## 🏗️ System Architecture

### Directory Structure
```
mcp-web-scraper/
├── src/
│   ├── server.py              # MCP server with 6 tools
│   ├── research/              # Jina AI integration
│   │   └── jina_researcher.py # Intelligent URL discovery
│   └── scrapers/              # Professional scraping engines
├── config/
│   └── mcp_config.json        # System configuration
├── tests/                     # Comprehensive validation
├── examples/                  # Production examples
├── docs/                      # Professional documentation
└── data/                      # Organized storage
    ├── raw/                   # Downloaded images
    ├── processed/             # Quality filtered
    ├── categorized/           # Person-organized
    └── metadata/              # Image information
```

### Technology Stack

- **🐍 Python 3.11+** - Modern Python with async support
- **🎭 Playwright 1.54.0** - Professional browser automation  
- **🤖 MCP 1.1.0** - Model Context Protocol framework
- **🔍 Jina AI** - Intelligent search and URL discovery
- **👁️ OpenCV 4.12.0** - Computer vision and face detection
- **🌐 aiohttp** - Async HTTP client for web requests
- **🍲 BeautifulSoup4** - HTML parsing and extraction

## ⚖️ Legal & Compliance

### Built-in Legal Features
- **🤖 Robots.txt Checking** - Automatic compliance verification
- **📋 Terms of Service Analysis** - Basic ToS compliance checking  
- **⏱️ Rate Limiting** - Respectful request timing
- **🔒 User Agent Management** - Professional identification
- **📝 Legal Risk Assessment** - Automated risk scoring

### Professional Guidelines
1. **Always respect robots.txt** - Our system checks automatically
2. **Use official APIs when available** - Recommended over scraping
3. **Respect rate limits** - Built-in delays and throttling
4. **Maintain proper attribution** - Credit sources appropriately
5. **Follow copyright laws** - Understand fair use policies
6. **Respect user privacy** - Handle personal data responsibly

## 🔧 Development Setup

### Prerequisites
- Python 3.11 or higher
- Git for version control
- VS Code (recommended) for MCP integration

### Development Installation

```bash
# Clone for development
git clone <your-repo-url>
cd mcp-web-scraper

# Create development environment
python -m venv venv-mcp-dev
source venv-mcp-dev/bin/activate  # Linux/Mac
# venv-mcp-dev\Scripts\activate   # Windows

# Install with development dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
python -m pytest tests/

# Run integration tests
python tests/test_jina_integration_fixed.py
```

### Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Test Jina AI integration
python tests/test_jina_integration_fixed.py

# Test production pipeline
python examples/production_ai_pipeline.py

# Test MCP server
python src/server.py
```

## 📊 Performance & Monitoring

### Built-in Statistics
- **📈 Real-time Progress** - Track scraping and categorization
- **🎯 Success Rates** - Monitor download and processing success
- **👥 Person Detection** - Face detection and identification stats
- **⚖️ Legal Compliance** - Track compliance checking results
- **🔍 Research Efficiency** - URL discovery and filtering metrics

### Monitoring Dashboard
```python
# Get comprehensive statistics
stats = await mcp_server.get_statistics({})
print(f"Images Processed: {stats['total_scraped']}")
print(f"Persons Identified: {stats['total_persons_identified']}")
print(f"Compliance Checks: {stats['legal_checks_passed']}")
```

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository** and create a feature branch
2. **Follow PEP 8** Python style guidelines
3. **Add tests** for new functionality
4. **Update documentation** for API changes
5. **Ensure legal compliance** in all contributions

### Development Workflow

```bash
# Create feature branch
git checkout -b feature/amazing-feature

# Make changes and test
python tests/test_jina_integration_fixed.py

# Commit changes
git commit -m "Add amazing feature with proper reasoning"

# Push and create pull request
git push origin feature/amazing-feature
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Jina AI** - For intelligent search and URL discovery capabilities
- **Microsoft MCP** - For the Model Context Protocol framework  
- **OpenCV Community** - For computer vision and face detection
- **Playwright Team** - For professional browser automation
- **Python Community** - For the amazing ecosystem

## 📞 Support & Contact

- **📖 Documentation**: See `/docs` folder for detailed guides
- **🐛 Issues**: Report bugs via GitHub Issues
- **💡 Feature Requests**: Suggest improvements via GitHub Discussions
- **📧 Contact**: For professional inquiries and collaboration

---

## 🚀 Quick Demo

```bash
# Clone and run in 3 minutes
git clone <your-repo-url>
cd mcp-web-scraper
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Add your Jina AI key
python examples/production_ai_pipeline.py
```

**Experience the power of AI-driven web scraping with intelligent reasoning! 🧠✨**
