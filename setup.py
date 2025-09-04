#!/usr/bin/env python3
"""
OF-MCP Setup Script
Installs dependencies and validates environment
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True
        )
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"❌ Python 3.11+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def install_dependencies():
    """Install Python dependencies"""
    requirements_file = Path(__file__).parent / "requirements.txt"

    if not requirements_file.exists():
        print(f"❌ Requirements file not found: {requirements_file}")
        return False

    # Install base requirements
    if not run_command(
        f"pip install -r {requirements_file}", "Installing base dependencies"
    ):
        return False

    # Install additional development dependencies
    dev_packages = [
        "python-dotenv>=1.0.0",  # For .env file loading
        "pytest>=7.0.0",  # For testing
        "black>=23.0.0",  # For code formatting
        "flake8>=6.0.0",  # For linting
    ]

    for package in dev_packages:
        if not run_command(
            f"pip install {package}", f"Installing {package.split('>=')[0]}"
        ):
            print(f"⚠️ Optional package {package} failed to install")

    return True


def setup_environment():
    """Setup environment files"""
    env_example = Path(__file__).parent / ".env.example"
    env_file = Path(__file__).parent / ".env"

    if env_example.exists() and not env_file.exists():
        try:
            import shutil

            shutil.copy(env_example, env_file)
            print(f"✅ Created .env file from template")
            print(f"⚠️ Please edit .env file with your actual API keys")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    elif env_file.exists():
        print(f"✅ .env file already exists")
        return True
    else:
        print(f"⚠️ No .env.example file found")
        return False


def create_directories():
    """Create necessary directories"""
    directories = [
        "data/raw",
        "data/processed",
        "data/categorized",
        "data/metadata",
        "logs",
    ]

    for directory in directories:
        dir_path = Path(__file__).parent / directory
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        except Exception as e:
            print(f"❌ Failed to create directory {directory}: {e}")
            return False

    return True


def validate_installation():
    """Validate the installation"""
    print("\n🔍 Validating installation...")

    # Test imports
    try:
        import mcp

        print("✅ MCP library available")
    except ImportError:
        print("❌ MCP library not available")
        return False

    try:
        import aiohttp

        print("✅ aiohttp available")
    except ImportError:
        print("❌ aiohttp not available - RFT integration will not work")

    try:
        import requests

        print("✅ requests available")
    except ImportError:
        print("❌ requests not available")
        return False

    try:
        import cv2

        print("✅ OpenCV available")
    except ImportError:
        print("⚠️ OpenCV not available - face detection will not work")

    try:
        from playwright.sync_api import sync_playwright

        print("✅ Playwright available")
    except ImportError:
        print("⚠️ Playwright not available - advanced scraping will not work")

    # Test environment
    try:
        from src.utils.env_loader import check_environment_health

        health = check_environment_health()
        print(f"✅ Environment health: {health['status']}")

        if health["warnings"]:
            for warning in health["warnings"]:
                print(f"⚠️ {warning}")

        if health["issues"]:
            for issue in health["issues"]:
                print(f"❌ {issue}")

    except ImportError:
        print("⚠️ Environment utilities not available")

    return True


def main():
    """Main setup function"""
    print("🚀 OF-MCP Setup Script")
    print("=" * 40)

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Install dependencies
    if not install_dependencies():
        print("❌ Dependency installation failed")
        sys.exit(1)

    # Setup environment
    if not setup_environment():
        print("⚠️ Environment setup had issues")

    # Create directories
    if not create_directories():
        print("❌ Directory creation failed")
        sys.exit(1)

    # Validate installation
    if not validate_installation():
        print("⚠️ Installation validation had issues")

    print("\n🎉 Setup completed!")
    print("\n📝 Next steps:")
    print("1. Edit .env file with your API keys")
    print("2. Set up Supabase database (see docs/RFT_INTEGRATION.md)")
    print("3. Run: python src/server.py")
    print("\n🔗 Documentation: docs/")


if __name__ == "__main__":
    main()
