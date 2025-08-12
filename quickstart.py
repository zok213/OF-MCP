#!/usr/bin/env python3
"""
Quick Start Script for MCP Web Scraper
Run this script to test the MCP server functionality
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from server import WebScraperMCPServer

async def test_mcp_server():
    """Test the MCP server functionality"""
    print("🚀 MCP Web Scraper - Quick Start Test")
    print("=" * 50)
    
    # Load configuration
    config_path = Path(__file__).parent / "config" / "mcp_config.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        print(f"✅ Configuration loaded from: {config_path}")
    except FileNotFoundError:
        print(f"⚠️  Configuration file not found, using defaults")
        config = {
            "storage": {
                "base_path": "./data",
                "raw_path": "./data/raw",
                "processed_path": "./data/processed",
                "categorized_path": "./data/categorized",
                "metadata_path": "./data/metadata"
            },
            "face_detection": {"face_threshold": 0.6},
            "categorization": {"min_confidence": 0.8},
            "legal": {
                "require_robots_check": True,
                "user_agent": "MCP-WebScraper/1.0"
            }
        }
    
    # Create server instance
    print("\n🔧 Creating MCP server instance...")
    server = WebScraperMCPServer(config)
    print("✅ Server created successfully!")
    
    # Test legal compliance check
    print("\n⚖️  Testing legal compliance check...")
    try:
        result = await server.handle_check_legal_compliance({
            "url": "https://www.pornpics.com/",
            "check_robots": True,
            "analyze_tos": True
        })
        print("✅ Legal compliance check completed:")
        print(result[0].text)
    except Exception as e:
        print(f"❌ Legal compliance check failed: {e}")
    
    # Test statistics
    print("\n📊 Testing statistics...")
    try:
        result = await server.handle_get_statistics({})
        print("✅ Statistics retrieved:")
        print(result[0].text)
    except Exception as e:
        print(f"❌ Statistics failed: {e}")
    
    # Test directory structure
    print("\n📁 Testing directory structure...")
    storage_paths = [
        config['storage']['base_path'],
        config['storage']['raw_path'],
        config['storage']['processed_path'],
        config['storage']['categorized_path'],
        config['storage']['metadata_path']
    ]
    
    for path_str in storage_paths:
        path = Path(path_str)
        if path.exists():
            print(f"✅ {path_str} - EXISTS")
        else:
            print(f"📂 {path_str} - CREATED")
    
    print("\n🎉 Quick start test completed!")
    print("\n📋 Next steps:")
    print("1. Install the server in VS Code settings")
    print("2. Use MCP tools through VS Code chat")
    print("3. Always check legal compliance before scraping")
    print("4. Start with small test batches")

async def demo_scraping_workflow():
    """Demonstrate the scraping workflow"""
    print("\n🔍 Demo: Typical Scraping Workflow")
    print("=" * 40)
    
    print("1. 📋 Check legal compliance:")
    print("   await call_tool('check_legal_compliance', {'url': 'https://example.com'})")
    
    print("\n2. 🌐 Scrape website (if legally compliant):")
    print("   await call_tool('scrape_website', {")
    print("       'url': 'https://example.com/gallery',")
    print("       'max_images': 50,")
    print("       'category': 'person_name'")
    print("   })")
    
    print("\n3. 🤖 Categorize downloaded images:")
    print("   await call_tool('categorize_images', {")
    print("       'source_folder': './data/raw',")
    print("       'learn_new_faces': true")
    print("   })")
    
    print("\n4. 📊 Check statistics:")
    print("   await call_tool('get_statistics', {})")
    
    print("\n5. 👥 List categories:")
    print("   await call_tool('list_categories', {})")

def show_vscode_setup():
    """Show VS Code setup instructions"""
    print("\n🔧 VS Code MCP Setup")
    print("=" * 25)
    
    current_path = Path(__file__).parent.absolute()
    server_path = current_path / "src" / "server.py"
    
    settings_json = {
        "mcp.servers": {
            "web-scraper": {
                "command": "python",
                "args": [str(server_path)],
                "cwd": str(current_path)
            }
        }
    }
    
    print("Add this to your VS Code settings.json:")
    print(json.dumps(settings_json, indent=2))
    
    print(f"\n📁 Server location: {server_path}")
    print(f"📁 Working directory: {current_path}")

def show_legal_guidelines():
    """Show legal guidelines"""
    print("\n⚖️  Legal Guidelines")
    print("=" * 20)
    
    print("✅ ALLOWED:")
    print("  • Public domain content")
    print("  • Content with AI training licenses")
    print("  • Educational research (with attribution)")
    print("  • Content with explicit permission")
    
    print("\n❌ RESTRICTED:")
    print("  • Private social media accounts")
    print("  • Sites that block in robots.txt")
    print("  • Copyrighted content without permission")
    print("  • Commercial use without proper licensing")
    
    print("\n💡 BEST PRACTICES:")
    print("  • Always check robots.txt first")
    print("  • Use official APIs when available")
    print("  • Implement reasonable rate limiting")
    print("  • Maintain proper attribution")
    print("  • Contact website owners for permissions")

async def main():
    """Main function"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            await test_mcp_server()
        elif command == "demo":
            await demo_scraping_workflow()
        elif command == "setup":
            show_vscode_setup()
        elif command == "legal":
            show_legal_guidelines()
        else:
            print(f"❌ Unknown command: {command}")
            print("Available commands: test, demo, setup, legal")
    else:
        print("🚀 MCP Web Scraper - Quick Start")
        print("=" * 35)
        print("Available commands:")
        print("  python quickstart.py test    - Test server functionality")
        print("  python quickstart.py demo    - Show scraping workflow")
        print("  python quickstart.py setup   - Show VS Code setup")
        print("  python quickstart.py legal   - Show legal guidelines")

if __name__ == "__main__":
    asyncio.run(main())
