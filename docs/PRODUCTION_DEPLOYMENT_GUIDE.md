# 🚀 Production Deployment Guide - MCP Web Scraper

## Overview

This guide covers the deployment of a **production-hardened** MCP Web Scraper with enterprise-grade security, resilience, and autonomous capabilities.

## 🛠️ System Requirements

### Hardware Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 8GB+ recommended (4GB minimum)
- **Storage**: 50GB+ for data and logs
- **Network**: Stable internet connection

### Software Requirements
- **Python**: 3.11 or higher
- **OS**: Windows 10/11, macOS 12+, Ubuntu 20.04+
- **Browser**: Chrome/Chromium for Playwright

## 📦 Installation & Setup

### 1. Environment Setup

```bash
# Clone repository
git clone <your-repo-url>
cd mcp-web-scraper

# Create production virtual environment
python -m venv venv-production
source venv-production/bin/activate  # Linux/Mac
# venv-production\Scripts\activate   # Windows

# Install production dependencies
pip install -r requirements.txt
pip install cryptography structlog psutil

# Install Playwright browsers
python -m playwright install chromium
python -m playwright install-deps chromium
```

### 2. Security Configuration

```bash
# Set master password for encryption
export MCP_SCRAPER_MASTER_PASSWORD="your_secure_password_here"

# Initialize secure credential storage
python -c "from src.core.security import initialize_security; initialize_security('your_secure_password_here')"
```

### 3. Configuration Setup

```bash
# Copy production configuration
cp config/mcp_config.production.json config/mcp_config.json

# Edit configuration with your settings
nano config/mcp_config.json
```

### 4. API Key Setup

```bash
# Store Jina AI API key securely
python -c "
from src.core.security import store_secure_credential
store_secure_credential('jina', 'api_key', 'your_jina_api_key_here')
"
```

## 🔐 Security Features

### Credential Management
```python
from src.core.security import store_secure_credential, get_secure_credential

# Store credential securely
store_secure_credential('jina', 'api_key', 'jina_xxx...')
store_secure_credential('openai', 'api_key', 'sk-xxx...')

# Retrieve credential
api_key = get_secure_credential('jina', 'api_key')
```

### Rate Limiting
```python
from src.core.security import APIRateLimiter

limiter = APIRateLimiter(requests_per_minute=30)
await limiter.wait_if_needed()  # Respects rate limits automatically
```

## 🔄 Resilience Features

### Circuit Breaker Pattern
```python
from src.core.error_handling import ResilienceManager

manager = ResilienceManager()
cb = manager.get_circuit_breaker('api_calls')

if cb.should_attempt():
    try:
        # Your API call here
        result = await api_call()
        cb.record_success()
    except Exception as e:
        cb.record_failure()
        raise
```

### Retry with Backoff
```python
from src.core.error_handling import AsyncRetry, create_retry_config

retry_config = create_retry_config(
    max_attempts=5,
    base_delay=2.0,
    retryable_errors=[ConnectionError, TimeoutError]
)

@AsyncRetry(retry_config)
async def robust_api_call():
    return await api_call()
```

## 🤖 Autonomous Scraping Setup

### 1. Browser Profile Setup

```python
from src.core.browser_persistence import AutonomousScraper, AutonomousConfig

config = AutonomousConfig(
    session_persistence=True,
    auto_login=True,
    headless=False,  # Set to False for initial setup
    max_concurrent_sessions=3
)

async with AutonomousScraper(config) as scraper:
    # Create autonomous session
    task_id = await scraper.create_autonomous_session(
        profile_name="production_profile",
        target_sites=[
            "https://example.com/gallery",
            "https://another-site.com/photos"
        ]
    )
```

### 2. Session Management

```python
# List active sessions
sessions = scraper.get_active_sessions()

# Get session status
status = scraper.get_session_status(task_id)

# Stop session
await scraper.stop_session(task_id)
```

## 🏥 Health Monitoring

### System Health Checks

```python
from src.core.error_handling import health_checker

# Register component health check
async def check_database():
    # Your health check logic
    return {"healthy": True, "connections": 5}

health_checker.register_component("database", check_database)

# Get system health
system_health = await health_checker.get_system_health()
print(f"System healthy: {system_health['healthy']}")
```

## 🚀 Production Deployment

### 1. VS Code MCP Configuration

Add to your VS Code `settings.json`:

```json
{
  "mcp.servers": {
    "web-scraper": {
      "command": "python",
      "args": ["/path/to/mcp-web-scraper/src/server.py"],
      "cwd": "/path/to/mcp-web-scraper",
      "env": {
        "MCP_SCRAPER_MASTER_PASSWORD": "your_secure_password",
        "PYTHONPATH": "/path/to/mcp-web-scraper/src"
      }
    }
  }
}
```

### 2. Systemd Service (Linux)

Create `/etc/systemd/system/mcp-web-scraper.service`:

```ini
[Unit]
Description=MCP Web Scraper Production Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/mcp-web-scraper
Environment=MCP_SCRAPER_MASTER_PASSWORD=your_secure_password
ExecStart=/path/to/venv/bin/python src/server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 3. Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium-browser \
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . .

# Install Python dependencies
RUN pip install -r requirements.txt
RUN pip install cryptography structlog psutil

# Install Playwright
RUN python -m playwright install chromium
RUN python -m playwright install-deps chromium

# Set environment
ENV MCP_SCRAPER_MASTER_PASSWORD=your_secure_password

# Expose port if needed
EXPOSE 3000

# Run application
CMD ["python", "src/server.py"]
```

## 📊 Monitoring & Maintenance

### Log Analysis

```bash
# View recent logs
tail -f logs/mcp_scraper.log

# Search for errors
grep "ERROR" logs/mcp_scraper.log

# Monitor performance
grep "performance" logs/mcp_scraper.log | tail -20
```

### Performance Monitoring

```python
import psutil
import time

def monitor_system():
    while True:
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent

        if cpu_percent > 80:
            logger.warning(f"High CPU usage: {cpu_percent}%")
        if memory_percent > 85:
            logger.warning(f"High memory usage: {memory_percent}%")

        time.sleep(60)
```

## 🔧 Configuration Tuning

### Performance Tuning

```json
{
  "autonomous": {
    "max_concurrent_sessions": 5,
    "session_timeout_hours": 48.0
  },
  "resilience": {
    "max_retries": 5,
    "base_delay_seconds": 1.5
  },
  "scrapers": {
    "generic": {
      "max_concurrent_downloads": 10,
      "timeout": 60
    }
  }
}
```

### Security Hardening

```json
{
  "security": {
    "max_login_attempts": 3,
    "session_timeout_hours": 12,
    "audit_logging": true
  },
  "logging": {
    "log_security_events": true,
    "log_performance_metrics": true
  }
}
```

## 🚨 Troubleshooting

### Common Issues

1. **Browser Launch Failures**
   ```bash
   # Check browser installation
   python -m playwright install chromium
   python -m playwright install-deps chromium
   ```

2. **Permission Errors**
   ```bash
   # Fix data directory permissions
   chmod -R 755 data/
   chown -R your_user:your_user data/
   ```

3. **Memory Issues**
   ```bash
   # Monitor memory usage
   ps aux | grep python

   # Adjust configuration
   # Reduce max_concurrent_sessions in config
   ```

4. **Network Timeouts**
   ```json
   {
     "scrapers": {
       "generic": {
         "timeout": 120,
         "max_retries": 5
       }
     }
   }
   ```

## 📈 Scaling Strategies

### Horizontal Scaling

```python
# Multiple scraper instances
instances = []
for i in range(3):
    config = AutonomousConfig(
        session_persistence=True,
        max_concurrent_sessions=2
    )
    scraper = AutonomousScraper(config)
    instances.append(scraper)
```

### Load Balancing

```python
# Distribute work across instances
async def distribute_work(target_sites):
    tasks = []
    for i, sites_chunk in enumerate(chunk_sites(target_sites, len(instances))):
        task = asyncio.create_task(
            instances[i].create_autonomous_session(f"worker_{i}", sites_chunk)
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    return results
```

## 🔒 Security Best Practices

### Credential Rotation

```python
# Rotate API keys periodically
async def rotate_credentials():
    # Generate new encryption key
    # Update stored credentials
    # Update configuration files
    pass
```

### Audit Logging

```python
# Log all security events
logger.info("Credential accessed", extra={
    "service": "jina",
    "user": "system",
    "action": "retrieve",
    "timestamp": time.time()
})
```

### Backup Strategy

```bash
# Backup encrypted credentials
cp ~/.mcp-scraper/credentials.enc ~/.mcp-scraper/backup/

# Backup session data
cp -r ~/.mcp-scraper/sessions ~/.mcp-scraper/backup/
```

## 🎯 Autonomous Deployment Use Cases

### 1. Continuous Content Monitoring

```python
# Monitor websites for new content
target_sites = [
    "https://photography-site.com/new",
    "https://art-gallery.com/latest",
    "https://model-portfolio.com/updates"
]

async with AutonomousScraper(config) as scraper:
    task_id = await scraper.create_autonomous_session(
        "content_monitor",
        target_sites
    )
    # Runs continuously, saves sessions between restarts
```

### 2. Research Data Collection

```python
# Automated research data gathering
research_targets = [
    "https://academic-site.com/publications",
    "https://research-db.com/latest",
    "https://science-news.com/articles"
]

# Use with intelligent research
from src.research.jina_researcher import JinaResearcher

async with JinaResearcher(jina_key) as researcher:
    research = await researcher.intelligent_research_pipeline(
        "machine learning research papers",
        {"style": "academic"}
    )

    # Extract URLs and start autonomous scraping
    urls = [target["url"] for target in research["filtered_targets"]]
    await scraper.create_autonomous_session("research_scraper", urls)
```

### 3. Social Media Monitoring

```python
# Monitor social media accounts (with proper API usage)
social_targets = [
    "https://instagram.com/official_account",
    "https://twitter.com/company",
    # Note: Respect platform ToS and use official APIs when possible
]

# Combine with login persistence for authenticated scraping
await scraper.create_autonomous_session("social_monitor", social_targets)
```

## 📋 Maintenance Checklist

### Daily
- [ ] Check system health: `system_health` MCP tool
- [ ] Monitor active sessions: `manage_sessions` MCP tool
- [ ] Review error logs

### Weekly
- [ ] Clean up old sessions: `manage_sessions cleanup`
- [ ] Backup credentials and session data
- [ ] Update dependencies if needed
- [ ] Review performance metrics

### Monthly
- [ ] Rotate API keys and credentials
- [ ] Update browser and system dependencies
- [ ] Review and optimize configuration
- [ ] Audit security logs

## 🎉 Success Metrics

Track these KPIs for deployment success:

- **Uptime**: >99.5%
- **Successful Scrapes**: >95%
- **Session Recovery**: >98%
- **Security Incidents**: 0
- **Performance**: <5% CPU, <70% memory
- **Data Quality**: >90% valid images

---

## 🚀 Quick Start Commands

```bash
# 1. Setup environment
python -m venv venv-prod && source venv-prod/bin/activate
pip install -r requirements.txt

# 2. Configure security
export MCP_SCRAPER_MASTER_PASSWORD="your_password"
python -c "from src.core.security import initialize_security; initialize_security()"

# 3. Store API keys
python -c "from src.core.security import store_secure_credential; store_secure_credential('jina', 'api_key', 'your_key')"

# 4. Start server
python src/server.py

# 5. Test autonomous scraping
# Use MCP tools: autonomous_scrape, manage_sessions, system_health
```

**Your MCP Web Scraper is now production-ready with enterprise-grade security, resilience, and autonomous capabilities! 🎯**
