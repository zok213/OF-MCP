#!/usr/bin/env python3
"""
Professional MCP Web Scraper Setup Script
Sets up the complete environment with Playwright browsers and all dependencies
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProfessionalSetup:
    """Professional setup manager for MCP Web Scraper"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.config_dir = self.project_root / "config"
        self.logs_dir = self.project_root / "logs"
        self.data_dir = self.project_root / "data"
        
    def run_setup(self):
        """Run complete setup process"""
        try:
            print("🚀 Starting Professional MCP Web Scraper Setup...")
            print("=" * 60)
            
            # Check Python version
            self.check_python_version()
            
            # Create directories
            self.create_directories()
            
            # Install Python dependencies
            self.install_dependencies()
            
            # Setup Playwright browsers
            self.setup_playwright()
            
            # Create configuration files
            self.create_configuration()
            
            # Setup VS Code integration
            self.setup_vscode_integration()
            
            # Final validation
            self.validate_setup()
            
            print("\n✅ Professional MCP Web Scraper Setup Complete!")
            print("=" * 60)
            self.print_usage_instructions()
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            sys.exit(1)
    
    def check_python_version(self):
        """Check Python version compatibility"""
        print("🐍 Checking Python version...")
        
        version = sys.version_info
        if version < (3, 8):
            raise Exception("Python 3.8 or higher is required")
            
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    
    def create_directories(self):
        """Create necessary directory structure"""
        print("📁 Creating directory structure...")
        
        directories = [
            self.config_dir,
            self.logs_dir,
            self.data_dir / "raw",
            self.data_dir / "processed", 
            self.data_dir / "categorized",
            self.data_dir / "metadata",
            self.project_root / "src" / "scrapers",
            self.project_root / "src" / "downloaders",
            self.project_root / "src" / "categorizers",
            self.project_root / "tests"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        
        print("✅ Directory structure created")
    
    def install_dependencies(self):
        """Install Python dependencies"""
        print("📦 Installing Python dependencies...")
        
        requirements_files = [
            "requirements.txt",
            "requirements_professional.txt"
        ]
        
        for req_file in requirements_files:
            req_path = self.project_root / req_file
            if req_path.exists():
                print(f"Installing from {req_file}...")
                try:
                    subprocess.run([
                        sys.executable, "-m", "pip", "install", "-r", str(req_path)
                    ], check=True, capture_output=True)
                    print(f"✅ Installed dependencies from {req_file}")
                except subprocess.CalledProcessError as e:
                    print(f"⚠️  Warning: Some dependencies from {req_file} may have failed")
                    logger.warning(f"pip install error: {e.stderr.decode()}")
    
    def setup_playwright(self):
        """Setup Playwright browsers"""
        print("🎭 Setting up Playwright browsers...")
        
        try:
            # Install Playwright
            subprocess.run([
                sys.executable, "-m", "pip", "install", "playwright"
            ], check=True)
            
            # Install browsers
            print("📥 Installing Playwright browsers (this may take a while)...")
            subprocess.run([
                sys.executable, "-m", "playwright", "install"
            ], check=True)
            
            # Install system dependencies
            print("🔧 Installing system dependencies...")
            subprocess.run([
                sys.executable, "-m", "playwright", "install-deps"
            ], check=True)
            
            print("✅ Playwright setup complete")
            
        except subprocess.CalledProcessError as e:
            print("⚠️  Warning: Playwright setup may have issues")
            logger.warning(f"Playwright setup error: {e}")
    
    def create_configuration(self):
        """Create professional configuration files"""
        print("⚙️  Creating configuration files...")
        
        # Main configuration
        main_config = {
            "storage": {
                "base_path": "./data",
                "raw_path": "./data/raw", 
                "processed_path": "./data/processed",
                "categorized_path": "./data/categorized",
                "metadata_path": "./data/metadata"
            },
            
            "scrapers": {
                "generic": {
                    "enabled": True,
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    "delay_range": [2, 5],
                    "max_retries": 3,
                    "timeout": 30
                },
                
                "pornpics": {
                    "enabled": True,
                    "delay_range": [3, 7],
                    "max_retries": 5,
                    "timeout": 45
                },
                
                "playwright": {
                    "enabled": True,
                    "browser": "chromium",
                    "headless": True,
                    "viewport": {"width": 1920, "height": 1080},
                    "request_delay_ms": 2000,
                    "bypass_age_verification": True,
                    "handle_cookie_banners": True
                }
            },
            
            "image_quality": {
                "min_width": 800,
                "min_height": 600,
                "max_file_size_mb": 50,
                "allowed_formats": ["jpg", "jpeg", "png", "webp"],
                "skip_thumbnails": True
            },
            
            "face_detection": {
                "enabled": True,
                "face_threshold": 0.6
            },
            
            "categorization": {
                "min_confidence": 0.8,
                "create_unknown_category": True
            },
            
            "legal": {
                "require_robots_check": True,
                "user_agent": "MCP-WebScraper/1.0",
                "respect_crawl_delay": True
            },
            
            "logging": {
                "level": "INFO",
                "file": "./logs/scraper.log",
                "max_file_size_mb": 100
            }
        }
        
        # Save main config
        config_file = self.config_dir / "mcp_config.json"
        with open(config_file, 'w') as f:
            json.dump(main_config, f, indent=2)
        
        print(f"✅ Configuration saved to {config_file}")
        
        # Create VS Code settings
        vscode_dir = self.project_root / ".vscode"
        vscode_dir.mkdir(exist_ok=True)
        
        vscode_settings = {
            "python.defaultInterpreterPath": sys.executable,
            "python.linting.enabled": True,
            "python.linting.flake8Enabled": True,
            "python.formatting.provider": "black",
            "files.exclude": {
                "**/__pycache__": True,
                "**/*.pyc": True,
                "**/node_modules": True,
                ".pytest_cache": True
            }
        }
        
        with open(vscode_dir / "settings.json", 'w') as f:
            json.dump(vscode_settings, f, indent=2)
    
    def setup_vscode_integration(self):
        """Setup VS Code MCP integration"""
        print("🔧 Setting up VS Code MCP integration...")
        
        mcp_config = {
            "mcpServers": {
                "web-scraper": {
                    "command": "python",
                    "args": [str(self.project_root / "src" / "server.py")]
                }
            }
        }
        
        # Save MCP config for reference
        mcp_file = self.config_dir / "vscode_mcp_config.json"
        with open(mcp_file, 'w') as f:
            json.dump(mcp_config, f, indent=2)
        
        print(f"📝 MCP configuration example saved to {mcp_file}")
        print("💡 Add this to your VS Code settings.json mcpServers section")
    
    def validate_setup(self):
        """Validate the setup"""
        print("✅ Validating setup...")
        
        # Check critical files
        critical_files = [
            self.project_root / "src" / "server.py",
            self.config_dir / "mcp_config.json",
            self.project_root / "requirements.txt"
        ]
        
        for file_path in critical_files:
            if not file_path.exists():
                raise Exception(f"Critical file missing: {file_path}")
        
        # Test imports
        try:
            import mcp
            import aiohttp
            import beautifulsoup4
            print("✅ Core dependencies validated")
        except ImportError as e:
            print(f"⚠️  Warning: Some dependencies may need manual installation: {e}")
        
        # Test Playwright
        try:
            from playwright.async_api import async_playwright
            print("✅ Playwright validated")
        except ImportError:
            print("⚠️  Warning: Playwright may need manual installation")
    
    def print_usage_instructions(self):
        """Print usage instructions"""
        print("\n📖 Usage Instructions:")
        print("-" * 40)
        print("1. 🚀 Start the MCP server:")
        print(f"   python {self.project_root / 'src' / 'server.py'}")
        print()
        print("2. 🔧 Configure VS Code:")
        print("   - Open VS Code settings (Ctrl+,)")
        print("   - Search for 'mcp'")
        print("   - Add the configuration from vscode_mcp_config.json")
        print()
        print("3. 📊 Test the setup:")
        print("   - Open GitHub Copilot Chat")
        print("   - Try: 'Check legal compliance for https://example.com'")
        print("   - Try: 'Get scraper statistics'")
        print()
        print("4. 🌐 Professional scraping:")
        print("   - Use 'scrape_website' tool for image extraction")
        print("   - Use 'categorize_images' for AI organization")
        print("   - Check logs in ./logs/ for detailed information")
        print()
        print("⚠️  Legal Reminder:")
        print("   Always respect website terms of service and robots.txt")
        print("   This tool is for educational/research purposes only")


def main():
    """Main setup function"""
    setup = ProfessionalSetup()
    setup.run_setup()


if __name__ == "__main__":
    main()
