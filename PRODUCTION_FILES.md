# Production File Structure

This document lists the **essential files** needed to run the AI-Driven MCP Web Scraper in production.

## ✅ **Essential Production Files:**

### **Core Application**
```
src/                          # Main application code
├── server.py                 # MCP server entry point
├── research/                 # Jina AI research integration
├── scrapers/                 # Web scraping modules
├── categorization/           # Image categorization
├── downloaders/              # Download managers
└── storage/                  # Data storage utilities
```

### **Configuration**
```
config/
├── mcp_config.example.json   # MCP server configuration template
└── mcp_config.json          # Actual MCP configuration (auto-generated)
```

### **Environment & Dependencies**
```
.env.example                 # Environment variables template
requirements.txt             # Essential Python dependencies
```

### **Project Files**
```
README.md                    # Main documentation
LICENSE                      # MIT License
.gitignore                   # Git ignore patterns (excludes development/)
```

### **GitHub Integration**
```
.github/
├── workflows/               # CI/CD pipelines
└── ISSUE_TEMPLATE/          # Issue templates
```

## 🚫 **Development Files (Ignored in Production):**

All non-essential files are organized in the `development/` folder and ignored by `.gitignore`:

```
development/                 # Excluded from production
├── testing/                 # Test files and utilities
├── setup/                   # Setup scripts
└── documentation/           # Additional docs
```

## 🚀 **Quick Start:**

1. **Clone repository**
2. **Install dependencies:** `pip install -r requirements.txt`
3. **Configure environment:** Copy `.env.example` to `.env` and set API keys
4. **Run MCP server:** `python src/server.py`

## 📊 **Repository Stats:**

- **Production Files:** 14 essential files
- **Development Files:** Organized in separate folder (ignored)
- **Total Dependencies:** 8 essential packages
- **Ready for:** Production deployment, Docker, CI/CD

---

*This structure ensures a clean, reliable, and logically organized production deployment while preserving development tools separately.*
