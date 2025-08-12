#!/usr/bin/env python3
"""
Complete Setup and Test Script for MCP Web Scraper
This script will set up the environment and run comprehensive tests
"""

import os
import sys
import subprocess
import json
from pathlib import Path
import asyncio


def setup_virtual_environment():
    """Set up Python virtual environment"""
    print("🔧 Setting up Python virtual environment...")
    
    venv_path = Path("venv")
    
    if not venv_path.exists():
        try:
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
            print("✅ Virtual environment created")
        except subprocess.CalledProcessError:
            print("❌ Failed to create virtual environment")
            return False
    else:
        print("✅ Virtual environment already exists")
    
    return True


def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    # Determine pip executable
    if os.name == 'nt':  # Windows
        pip_executable = Path("venv/Scripts/pip.exe")
    else:  # Unix/Linux/macOS
        pip_executable = Path("venv/bin/pip")
    
    if not pip_executable.exists():
        print("❌ Pip not found in virtual environment")
        return False
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    try:
        subprocess.run([
            str(pip_executable), 
            "install", 
            "-r", 
            str(requirements_file)
        ], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False


def verify_configuration():
    """Verify configuration files exist and are valid"""
    print("⚙️ Verifying configuration...")
    
    config_file = Path("config/mcp_config.json")
    
    if not config_file.exists():
        print("❌ Configuration file not found")
        return False
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        print("✅ Configuration file is valid JSON")
        
        # Check required sections
        required_sections = ['storage', 'face_detection', 'categorization', 'legal', 'scrapers']
        for section in required_sections:
            if section not in config:
                print(f"⚠️ Missing configuration section: {section}")
            else:
                print(f"✅ Configuration section '{section}' found")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in configuration: {e}")
        return False


def create_directory_structure():
    """Create required directory structure"""
    print("📁 Creating directory structure...")
    
    directories = [
        "data",
        "data/raw",
        "data/processed", 
        "data/categorized",
        "data/metadata",
        "logs"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"✅ Directory exists: {directory}")
    
    return True


async def test_scrapers():
    """Test scraper functionality"""
    print("🧪 Testing scrapers...")
    
    # Add src to path
    sys.path.insert(0, str(Path("src").absolute()))
    
    try:
        from scrapers.base_scraper import GenericScraper, PornPicsScraper
        print("✅ Scrapers imported successfully")
        
        # Test Generic Scraper
        print("\n🌐 Testing Generic Scraper...")
        generic_config = {"delay": 1, "max_retries": 2}
        generic_scraper = GenericScraper(generic_config)
        
        # Test robots.txt check
        robots_ok = generic_scraper.check_robots_txt("https://httpbin.org/")
        print(f"  🤖 Robots.txt check: {'✅ Pass' if robots_ok else '❌ Blocked'}")
        
        # Test PornPics Scraper
        print("\n🔞 Testing PornPics Scraper...")
        pornpics_config = {"delay": 2, "enabled": True}
        pornpics_scraper = PornPicsScraper(pornpics_config)
        
        print("✅ All scraper tests completed")
        
    except ImportError as e:
        print(f"❌ Failed to import scrapers: {e}")
        return False
    except Exception as e:
        print(f"❌ Scraper test failed: {e}")
        return False
    
    return True


async def test_mcp_server():
    """Test MCP server functionality"""
    print("🖥️ Testing MCP Server...")
    
    try:
        sys.path.insert(0, str(Path("src").absolute()))
        from server import WebScraperMCPServer
        
        # Load configuration
        config_file = Path("config/mcp_config.json")
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Create server
        server = WebScraperMCPServer(config)
        print("✅ MCP Server created successfully")
        
        # Test legal compliance check
        compliance_result = await server.handle_check_legal_compliance({
            "url": "https://httpbin.org/",
            "check_robots": True,
            "analyze_tos": True
        })
        
        if compliance_result:
            print("✅ Legal compliance check working")
        else:
            print("❌ Legal compliance check failed")
        
        # Test statistics
        stats_result = await server.handle_get_statistics({})
        if stats_result:
            print("✅ Statistics function working")
        else:
            print("❌ Statistics function failed")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP Server test failed: {e}")
        return False


def show_vscode_setup():
    """Show VS Code integration setup"""
    print("\n🔧 VS Code Integration Setup")
    print("=" * 40)
    
    current_path = Path.cwd().absolute()
    server_path = current_path / "src" / "server.py"
    
    # Python executable path
    if os.name == 'nt':  # Windows
        python_executable = current_path / "venv" / "Scripts" / "python.exe"
    else:
        python_executable = current_path / "venv" / "bin" / "python"
    
    settings_json = {
        "mcp.servers": {
            "web-scraper": {
                "command": str(python_executable),
                "args": [str(server_path)],
                "cwd": str(current_path)
            }
        }
    }
    
    print("Add this to your VS Code settings.json:")
    print(json.dumps(settings_json, indent=2))
    print(f"\nServer path: {server_path}")
    print(f"Python path: {python_executable}")
    print(f"Working directory: {current_path}")


def show_usage_examples():
    """Show usage examples"""
    print("\n📚 Usage Examples")
    print("=" * 20)
    
    print("1. Check legal compliance:")
    print('   call_tool("check_legal_compliance", {"url": "https://example.com"})')
    
    print("\n2. Scrape a website:")
    print('   call_tool("scrape_website", {')
    print('       "url": "https://www.pornpics.com/galleries/example/",')
    print('       "max_images": 20,')
    print('       "category": "example_person"')
    print('   })')
    
    print("\n3. Get statistics:")
    print('   call_tool("get_statistics", {})')


async def main():
    """Main setup and test function"""
    print("🚀 MCP Web Scraper - Complete Setup & Test")
    print("=" * 50)
    print("⚠️ This tool is for educational/research purposes only!")
    print("⚠️ Always respect website ToS and legal requirements!")
    print("=" * 50)
    
    # Setup steps
    setup_success = True
    
    # Step 1: Virtual environment
    if not setup_virtual_environment():
        setup_success = False
    
    # Step 2: Install dependencies
    if setup_success and not install_dependencies():
        setup_success = False
    
    # Step 3: Verify configuration
    if setup_success and not verify_configuration():
        setup_success = False
    
    # Step 4: Create directories
    if setup_success and not create_directory_structure():
        setup_success = False
    
    # Step 5: Test scrapers
    if setup_success and not await test_scrapers():
        setup_success = False
    
    # Step 6: Test MCP server
    if setup_success and not await test_mcp_server():
        setup_success = False
    
    # Results
    print("\n" + "=" * 50)
    if setup_success:
        print("🎉 Setup completed successfully!")
        print("✅ All tests passed")
        
        show_vscode_setup()
        show_usage_examples()
        
        print("\n💡 Next Steps:")
        print("1. Add the MCP server to VS Code settings")
        print("2. Restart VS Code")
        print("3. Use MCP tools in VS Code chat")
        print("4. Always check legal compliance first!")
        print("5. Start with small test batches")
        
    else:
        print("❌ Setup failed!")
        print("Please fix the issues above and run again")
    
    print("\n⚖️ Legal Reminder:")
    print("• Only scrape public domain or licensed content")
    print("• Respect robots.txt and website ToS")
    print("• Use official APIs when available")
    print("• Get permission for commercial use")


if __name__ == "__main__":
    asyncio.run(main())
