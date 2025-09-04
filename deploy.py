#!/usr/bin/env python3
"""
Professional Deployment Setup Script for MCP Web Scraper
Handles virtual environment, dependencies, and browser installation
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

class DeploymentManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / "venv-mcp-scraper"
        self.python_exe = self.venv_path / "Scripts" / "python.exe" if os.name == 'nt' else self.venv_path / "bin" / "python"
        self.pip_exe = self.venv_path / "Scripts" / "pip.exe" if os.name == 'nt' else self.venv_path / "bin" / "pip"

    def check_python_version(self):
        """Check if Python version is compatible"""
        print("🔍 Checking Python version...")
        if sys.version_info < (3, 8):
            print("❌ Error: Python 3.8 or higher is required")
            print(f"Current version: {sys.version}")
            return False
        
        print(f"✅ Python {sys.version.split()[0]} is compatible")
        return True

    def create_virtual_environment(self):
        """Create and setup virtual environment"""
        print("🏗️ Setting up virtual environment...")
        
        if self.venv_path.exists():
            print(f"⚠️ Virtual environment already exists at {self.venv_path}")
            response = input("Do you want to recreate it? (y/N): ").lower()
            if response == 'y':
                print("🗑️ Removing existing virtual environment...")
                shutil.rmtree(self.venv_path)
            else:
                print("✅ Using existing virtual environment")
                return True

        try:
            subprocess.run([sys.executable, "-m", "venv", str(self.venv_path)], check=True)
            print(f"✅ Virtual environment created at {self.venv_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error creating virtual environment: {e}")
            return False

    def upgrade_pip(self):
        """Upgrade pip in virtual environment"""
        print("📦 Upgrading pip, setuptools, and wheel...")
        try:
            subprocess.run([
                str(self.python_exe), "-m", "pip", "install", 
                "--upgrade", "pip", "setuptools", "wheel"
            ], check=True)
            print("✅ Package management tools upgraded")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error upgrading pip: {e}")
            return False

    def install_requirements(self, minimal=False):
        """Install Python requirements"""
        req_file = "requirements-minimal.txt" if minimal else "requirements.txt"
        req_path = self.project_root / req_file
        
        if not req_path.exists():
            print(f"❌ Requirements file not found: {req_path}")
            return False
        
        print(f"📦 Installing packages from {req_file}...")
        try:
            subprocess.run([
                str(self.python_exe), "-m", "pip", "install", 
                "-r", str(req_path)
            ], check=True)
            print("✅ Python packages installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing requirements: {e}")
            return False

    def install_playwright_browsers(self):
        """Install Playwright browsers"""
        print("🌐 Installing Playwright browsers...")
        try:
            # Install Chromium (lightweight and sufficient for most scraping)
            subprocess.run([
                str(self.python_exe), "-m", "playwright", "install", "chromium"
            ], check=True)
            print("✅ Playwright Chromium browser installed")
            
            # Optionally install system dependencies
            print("🔧 Installing system dependencies...")
            subprocess.run([
                str(self.python_exe), "-m", "playwright", "install-deps", "chromium"
            ], check=False)  # Don't fail if this doesn't work
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing Playwright browsers: {e}")
            return False

    def create_config_files(self):
        """Create configuration files if they don't exist"""
        print("📝 Creating configuration files...")
        
        # Create .env file
        env_path = self.project_root / ".env"
        if not env_path.exists():
            env_content = """# MCP Web Scraper Environment Configuration
# Copy this file and customize for your deployment

# Legal and ethical settings
RESPECT_ROBOTS_TXT=true
USER_AGENT=MCP-WebScraper/1.0
REQUEST_DELAY_MS=2000

# Storage paths
DATA_BASE_PATH=./data
RAW_IMAGES_PATH=./data/raw
PROCESSED_IMAGES_PATH=./data/processed
CATEGORIZED_IMAGES_PATH=./data/categorized
METADATA_PATH=./data/metadata

# Image quality filters
MIN_IMAGE_WIDTH=800
MIN_IMAGE_HEIGHT=600
MAX_FILE_SIZE_MB=50

# Browser settings
HEADLESS=true
VIEWPORT_WIDTH=1920
VIEWPORT_HEIGHT=1080

# Adult site settings (18+ compliance)
BYPASS_AGE_VERIFICATION=true
HANDLE_COOKIE_BANNERS=true
"""
            with open(env_path, 'w') as f:
                f.write(env_content)
            print(f"✅ Created .env configuration file")

        # Create data directories
        data_dirs = ['data', 'data/raw', 'data/processed', 'data/categorized', 'data/metadata', 'logs']
        for dir_name in data_dirs:
            dir_path = self.project_root / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
        
        print("✅ Created data directories")
        return True

    def create_run_scripts(self):
        """Create convenient run scripts"""
        print("📜 Creating run scripts...")
        
        # Windows batch script
        if os.name == 'nt':
            bat_script = self.project_root / "run_mcp_server.bat"
            bat_content = f"""@echo off
echo Starting MCP Web Scraper Server...
cd /d "{self.project_root}"
"{self.python_exe}" mcp-web-scraper\\src\\server.py
pause
"""
            with open(bat_script, 'w') as f:
                f.write(bat_content)
            print("✅ Created run_mcp_server.bat")

        # PowerShell script
        ps1_script = self.project_root / "run_mcp_server.ps1"
        ps1_content = f"""# MCP Web Scraper PowerShell Launch Script
Write-Host "Starting MCP Web Scraper Server..." -ForegroundColor Green
Set-Location "{self.project_root}"
& "{self.python_exe}" mcp-web-scraper\\src\\server.py
"""
        with open(ps1_script, 'w') as f:
            f.write(ps1_content)
        print("✅ Created run_mcp_server.ps1")

        # Python activation script
        activate_script = self.project_root / "activate_venv.py"
        activate_content = f'''#!/usr/bin/env python3
"""
Activation helper for MCP Web Scraper virtual environment
"""
import os
import subprocess
import sys

def main():
    venv_path = r"{self.venv_path}"
    python_exe = r"{self.python_exe}"
    
    print("🚀 MCP Web Scraper Development Environment")
    print(f"Virtual Environment: {{venv_path}}")
    print(f"Python Executable: {{python_exe}}")
    print()
    
    # Show installed packages
    try:
        result = subprocess.run([str(python_exe), "-m", "pip", "list"], 
                              capture_output=True, text=True)
        print("📦 Installed packages:")
        print(result.stdout)
    except Exception as e:
        print(f"Error listing packages: {{e}}")
    
    print("💡 To activate manually:")
    if os.name == 'nt':
        print(f"   {{venv_path}}\\Scripts\\Activate.ps1")
    else:
        print(f"   source {{venv_path}}/bin/activate")

if __name__ == "__main__":
    main()
'''
        with open(activate_script, 'w') as f:
            f.write(activate_content)
        print("✅ Created activate_venv.py")

        return True

    def verify_installation(self):
        """Verify that everything is installed correctly"""
        print("🔍 Verifying installation...")
        
        tests = [
            ("Python executable", lambda: self.python_exe.exists()),
            ("MCP import", lambda: self.test_import("mcp")),
            ("Playwright import", lambda: self.test_import("playwright")),
            ("aiohttp import", lambda: self.test_import("aiohttp")),
            ("BeautifulSoup import", lambda: self.test_import("bs4")),
            ("Pillow import", lambda: self.test_import("PIL")),
            ("NumPy import", lambda: self.test_import("numpy")),
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            try:
                if test_func():
                    print(f"  ✅ {test_name}")
                else:
                    print(f"  ❌ {test_name}")
                    all_passed = False
            except Exception as e:
                print(f"  ❌ {test_name}: {e}")
                all_passed = False
        
        return all_passed

    def test_import(self, module_name):
        """Test if a module can be imported"""
        try:
            result = subprocess.run([
                str(self.python_exe), "-c", f"import {module_name}; print('OK')"
            ], capture_output=True, text=True, check=True)
            return "OK" in result.stdout
        except subprocess.CalledProcessError:
            return False

    def run_deployment(self, minimal=False):
        """Run full deployment process"""
        print("🚀 Starting MCP Web Scraper Deployment")
        print("=" * 50)
        
        steps = [
            ("Check Python Version", self.check_python_version),
            ("Create Virtual Environment", self.create_virtual_environment),
            ("Upgrade Package Tools", self.upgrade_pip),
            ("Install Requirements", lambda: self.install_requirements(minimal)),
            ("Install Playwright Browsers", self.install_playwright_browsers),
            ("Create Configuration", self.create_config_files),
            ("Create Run Scripts", self.create_run_scripts),
            ("Verify Installation", self.verify_installation)
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            if not step_func():
                print(f"❌ Deployment failed at step: {step_name}")
                return False
        
        print("\n🎉 Deployment completed successfully!")
        print("\n📖 Next steps:")
        print(f"1. Review configuration in .env file")
        print(f"2. Run the server with: python mcp-web-scraper/src/server.py")
        print(f"3. Or use the convenience script: run_mcp_server.bat")
        print(f"4. Check logs in ./logs/ directory")
        
        return True


def main():
    """Main deployment entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy MCP Web Scraper")
    parser.add_argument("--minimal", action="store_true", 
                       help="Install minimal requirements only")
    parser.add_argument("--verify-only", action="store_true",
                       help="Only verify existing installation")
    
    args = parser.parse_args()
    
    deployer = DeploymentManager()
    
    if args.verify_only:
        success = deployer.verify_installation()
        sys.exit(0 if success else 1)
    else:
        success = deployer.run_deployment(minimal=args.minimal)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
