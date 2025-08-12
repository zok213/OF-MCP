# MCP Web Scraper

A Model Context Protocol (MCP) server for intelligent web scraping and automatic image categorization with face recognition.

## ⚠️ Important Legal Notice

**This tool is for educational and research purposes only.** Always:
- Check and respect robots.txt
- Review website Terms of Service
- Use official APIs when available
- Obtain proper permissions for commercial use
- Respect rate limits and be considerate
- Follow applicable copyright and privacy laws

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or create the project
cd mcp-web-scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Edit `config/mcp_config.json` to customize settings:
- Storage paths
- Face detection parameters
- Legal compliance requirements
- Scraper configurations

### 3. VS Code Integration

Add to your VS Code `settings.json`:

```json
{
  "mcp.servers": {
    "web-scraper": {
      "command": "python",
      "args": ["path/to/mcp-web-scraper/src/server.py"],
      "cwd": "path/to/mcp-web-scraper"
    }
  }
}
```

## 🛠️ Available Tools

### `scrape_website`
- Scrape images from a website URL
- Legal compliance checks (robots.txt, ToS)
- Quality filtering and rate limiting
- Automatic metadata extraction

### `categorize_images`  
- Automatic face detection and recognition
- Person-based image organization
- Learning new faces from examples
- Quality assessment and filtering

### `check_legal_compliance`
- Robots.txt analysis
- Terms of Service guidance
- Legal compliance recommendations

### `get_statistics`
- Scraping and categorization statistics
- Directory information
- Configuration summary

### `list_categories`
- View organized person categories
- Image counts per category
- Sample file listings

## 📁 Directory Structure

```
data/
├── raw/           # Downloaded images
├── processed/     # Quality filtered images
├── categorized/   # Organized by person
│   ├── person_1/
│   ├── person_2/
│   └── unknown/
└── metadata/      # JSON metadata files
```

## 🔧 Implementation Status

### ✅ Completed
- MCP server framework
- Tool definitions and routing
- Legal compliance checking
- Directory structure management
- Configuration system

### 🚧 In Progress / TODO
- Web scraping implementation
- Face detection integration
- Image categorization
- Quality filtering
- Metadata management

## 🤖 Face Detection & Categorization

The system will use:
- **OpenCV** for image processing
- **face_recognition** library for face detection
- **Clustering algorithms** for grouping similar faces
- **Quality metrics** for image filtering

## ⚖️ Legal & Ethical Guidelines

### Supported Use Cases
- ✅ Public domain content
- ✅ Content with explicit AI training licenses
- ✅ Educational research with proper attribution
- ✅ Personal projects with legally obtained content

### Restricted Use Cases  
- ❌ Scraping private social media content
- ❌ Ignoring robots.txt or Terms of Service
- ❌ Commercial use without proper licensing
- ❌ Bulk downloading copyrighted content

## 🔍 Example Usage

```python
# Through MCP client in VS Code:

# Check if a website allows scraping
await call_tool("check_legal_compliance", {
    "url": "https://example.com",
    "check_robots": true,
    "analyze_tos": true
})

# Scrape images (after legal compliance check)
await call_tool("scrape_website", {
    "url": "https://example.com/gallery", 
    "max_images": 50,
    "category": "example_person"
})

# Categorize downloaded images
await call_tool("categorize_images", {
    "source_folder": "./data/raw",
    "learn_new_faces": true,
    "min_confidence": 0.8
})
```

## 📊 Configuration Options

### Storage Settings
- File size limits
- Allowed formats
- Download timeout
- Concurrent downloads

### Face Detection
- Recognition threshold
- Minimum face size
- Encoding model selection

### Legal Compliance
- Robots.txt checking
- Attribution requirements  
- Rate limiting

## 🚧 Development Roadmap

1. **Phase 1**: Core scraping engine
2. **Phase 2**: Face detection integration
3. **Phase 3**: Advanced categorization
4. **Phase 4**: Quality assessment
5. **Phase 5**: Web UI dashboard

## 📞 Support & Contributing

- Create issues for bugs or feature requests
- Follow coding standards and legal guidelines
- Ensure all contributions respect copyright laws
- Test thoroughly with legal, publicly available content

## 📄 License

MIT License - See LICENSE file for details.

**Disclaimer**: Users are responsible for ensuring their use complies with applicable laws, website terms of service, and ethical guidelines.
