# 🚀 MCP Web Scraper - Professional Deployment Guide

## Overview

This is a production-ready deployment of the MCP (Model Context Protocol) Web Scraper designed for professional adult content data collection and AI training dataset preparation. The system uses state-of-the-art browser automation with Playwright and follows industry best practices.

## 🎯 Key Features

- **Professional Browser Automation**: Microsoft Playwright integration with stealth techniques
- **Legal Compliance Framework**: Built-in robots.txt checking and ToS analysis
- **Adult Content Optimization**: Age verification bypass, cookie handling, lazy loading
- **Intelligent Image Filtering**: Quality assessment, deduplication, format optimization
- **VS Code MCP Integration**: Direct integration with GitHub Copilot and VS Code
- **Scalable Architecture**: Async processing, rate limiting, session management

## 🔧 System Requirements

- **Python**: 3.8+ (Recommended: 3.11+)
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux
- **RAM**: Minimum 4GB (Recommended: 8GB+)
- **Storage**: 2GB+ free space (more for image storage)
- **Network**: Stable internet connection

## 📦 Installation Methods

### Method 1: Automated Deployment (Recommended)

```bash
# 1. Clone the repository
git clone <repository-url>
cd OF

# 2. Run automated deployment
python deploy.py

# 3. Start the server
run_mcp_server.bat  # Windows
# or
./run_mcp_server.ps1  # PowerShell
```

### Method 2: Manual Setup

```bash
# 1. Create virtual environment
python -m venv venv-mcp-scraper

# 2. Activate environment
# Windows:
venv-mcp-scraper\Scripts\activate
# Unix/macOS:
source venv-mcp-scraper/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers
python -m playwright install chromium

# 5. Create configuration
cp .env.example .env

# 6. Run server
python mcp-web-scraper/src/server.py
```

## ⚙️ Configuration

### Environment Variables (.env file)

```bash
# Legal and ethical settings
RESPECT_ROBOTS_TXT=true
USER_AGENT=MCP-WebScraper/1.0 (Educational Research)
REQUEST_DELAY_MS=2000

# Storage configuration
DATA_BASE_PATH=./data
RAW_IMAGES_PATH=./data/raw
PROCESSED_IMAGES_PATH=./data/processed
CATEGORIZED_IMAGES_PATH=./data/categorized

# Image quality filters
MIN_IMAGE_WIDTH=800
MIN_IMAGE_HEIGHT=600
MAX_FILE_SIZE_MB=50

# Browser settings
HEADLESS=true
VIEWPORT_WIDTH=1920
VIEWPORT_HEIGHT=1080

# Adult site optimization
BYPASS_AGE_VERIFICATION=true
HANDLE_COOKIE_BANNERS=true
SCROLL_FOR_LAZY_LOAD=true

# Rate limiting
MAX_CONCURRENT_REQUESTS=3
RANDOM_DELAY_VARIANCE=1000
```

### MCP Configuration (for VS Code)

Add to your VS Code MCP settings:

```json
{
  "mcpServers": {
    "web-scraper": {
      "command": "D:/Gitrepo/OF/venv-mcp-scraper/Scripts/python.exe",
      "args": ["D:/Gitrepo/OF/mcp-web-scraper/src/server.py"]
    }
  }
}
```

## 🎮 Usage Examples

### Basic Web Scraping

```python
# Through VS Code MCP integration
# Ask Copilot: "Scrape images from pornpics.com gallery with legal compliance"

# Direct tool usage:
{
  "tool": "scrape_website",
  "args": {
    "url": "https://www.pornpics.com/galleries/...",
    "max_images": 100,
    "category": "model_name",
    "check_legal": true
  }
}
```

### Image Categorization

```python
# Automatic categorization by person
{
  "tool": "categorize_images", 
  "args": {
    "source_folder": "./data/raw/model_name",
    "learn_new_faces": true,
    "min_confidence": 0.8
  }
}
```

### Legal Compliance Check

```python
{
  "tool": "check_legal_compliance",
  "args": {
    "url": "https://example-adult-site.com",
    "check_robots": true,
    "analyze_tos": true
  }
}
```

## 🏗️ Architecture

### Core Components

```
mcp-web-scraper/
├── src/
│   ├── server.py              # Main MCP server
│   └── scrapers/
│       ├── base_scraper.py    # Base scraping classes  
│       └── playwright_scraper.py  # Playwright implementation
├── config/
│   └── mcp_config.json       # MCP configuration
├── data/                     # Storage directories
├── logs/                     # Application logs
└── venv-mcp-scraper/        # Virtual environment
```

### Data Flow

1. **Input**: URL via MCP tool call
2. **Legal Check**: robots.txt and ToS analysis
3. **Browser Launch**: Playwright with stealth configuration
4. **Content Processing**: Age verification, cookie handling
5. **Image Extraction**: Intelligent selectors and quality filtering
6. **Storage**: Organized file structure with metadata
7. **Categorization**: Face detection and person clustering

## 🛡️ Security & Legal Compliance

### Built-in Safeguards

- **Robots.txt Compliance**: Automatic checking before scraping
- **Rate Limiting**: Respectful request timing with random delays
- **User-Agent Identification**: Clear identification for website owners
- **Terms of Service Analysis**: Basic ToS compliance checking
- **Data Attribution**: Metadata tracking for legal compliance

### Best Practices

1. **Always review website ToS** before scraping
2. **Use official APIs when available** instead of scraping
3. **Respect rate limits** and be polite to servers
4. **Contact website owners** for permission when in doubt
5. **Follow applicable copyright laws** in your jurisdiction
6. **Maintain proper data attribution** and sources

### Adult Content Compliance

- **Age Verification**: Built-in 18+ confirmation handling
- **Legal Jurisdiction**: Ensure compliance with local laws
- **Content Classification**: Proper labeling and storage
- **Access Controls**: Implement appropriate access restrictions

## 🚀 Deployment Options

### Development Deployment

```bash
# Quick start for development
python deploy.py --minimal
run_mcp_server.ps1 -Debug
```

### Production Deployment

```bash
# Full production setup
python deploy.py
run_mcp_server.bat
```

### Docker Deployment (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN python -m playwright install chromium

COPY . .
CMD ["python", "mcp-web-scraper/src/server.py"]
```

## 📊 Performance Optimization

### Browser Optimization
- **Resource Blocking**: Block unnecessary CSS/JS for faster loading
- **Request Interception**: Intelligent filtering of network requests
- **Session Persistence**: Reuse browser contexts for efficiency
- **Memory Management**: Proper cleanup and resource management

### Scraping Optimization
- **Lazy Loading**: Smart scrolling to trigger image loading
- **Quality Filtering**: Pre-filter images before download
- **Duplicate Detection**: Avoid downloading identical images
- **Batch Processing**: Efficient handling of large galleries

### Storage Optimization
- **Directory Structure**: Organized by model/category
- **File Naming**: Consistent, collision-resistant naming
- **Metadata Storage**: JSON metadata for each session
- **Cleanup Scripts**: Remove duplicates and low-quality images

## 🔍 Monitoring & Debugging

### Logging

```bash
# Log files location
logs/
├── mcp-server.log          # Main server logs
├── scraper.log            # Scraping activity
├── browser.log            # Browser automation logs
└── errors.log             # Error tracking
```

### Debug Mode

```bash
# Enable debug mode
run_mcp_server.ps1 -Debug

# Manual debug environment
$env:DEBUG_MODE = "true"
$env:LOG_LEVEL = "DEBUG"
python mcp-web-scraper/src/server.py
```

### Health Checks

```python
# Built-in statistics and health monitoring
{
  "tool": "get_statistics",
  "args": {}
}
```

## 🤝 VS Code Integration

### Installation in VS Code

1. Install the MCP extension
2. Add server configuration:
   ```json
   {
     "mcpServers": {
       "web-scraper": {
         "command": "D:/Gitrepo/OF/venv-mcp-scraper/Scripts/python.exe",
         "args": ["D:/Gitrepo/OF/mcp-web-scraper/src/server.py"]
       }
     }
   }
   ```
3. Restart VS Code
4. Use through GitHub Copilot chat

### Usage with Copilot

Ask Copilot natural language questions like:
- "Scrape this adult gallery and organize by person"
- "Check if I can legally scrape this website"
- "Show me statistics of my scraping activity"
- "Categorize these downloaded images by person"

## 🚨 Troubleshooting

### Common Issues

1. **Playwright Browser Not Found**
   ```bash
   python -m playwright install chromium
   ```

2. **Permission Denied Errors**
   ```bash
   # Windows: Run as administrator
   # Linux/macOS: Check file permissions
   chmod +x run_scripts/*
   ```

3. **Import Errors**
   ```bash
   # Verify virtual environment activation
   python deploy.py --verify-only
   ```

4. **Rate Limiting/Blocked Requests**
   - Increase `REQUEST_DELAY_MS` in .env
   - Check if robots.txt blocks access
   - Verify user-agent is acceptable

### Support

For technical issues:
1. Check logs in `./logs/` directory
2. Run verification: `python deploy.py --verify-only`
3. Enable debug mode for detailed output
4. Review legal compliance recommendations

## 📜 Legal Disclaimer

This software is provided for **educational and research purposes only**. Users are responsible for:

- Complying with all applicable laws and regulations
- Respecting website terms of service
- Obtaining proper permissions when required
- Following ethical web scraping practices
- Ensuring age verification compliance for adult content

The developers assume no liability for misuse of this software.

## 🔄 Updates & Maintenance

### Regular Maintenance

```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Update Playwright browsers
python -m playwright install chromium

# Clean old data
python scripts/cleanup_old_data.py
```

### Version Checks

```bash
# Check component versions
python deploy.py --verify-only
python -c "import playwright; print(playwright.__version__)"
```

---

**Version**: 1.0.0  
**Last Updated**: August 10, 2025  
**License**: Educational Use Only
