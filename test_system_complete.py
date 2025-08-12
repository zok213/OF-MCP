#!/usr/bin/env python3
"""
Comprehensive System Test Runner
Tests all components of the MCP Web Scraper system
"""

import asyncio
import json
import logging
import sys
import traceback
from pathlib import Path
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("system-test")

class SystemTester:
    """Complete system tester and validator"""
    
    def __init__(self):
        self.test_results = {}
        self.errors = []
        
    def log_test_result(self, test_name: str, passed: bool, message: str = "", error: str = ""):
        """Log test result"""
        self.test_results[test_name] = {
            'passed': passed,
            'message': message,
            'error': error
        }
        
        if passed:
            logger.info(f"✅ {test_name}: {message}")
        else:
            logger.error(f"❌ {test_name}: {message}")
            if error:
                logger.error(f"   Error: {error}")
    
    async def test_imports(self):
        """Test all critical imports"""
        try:
            # Test MCP imports
            import mcp.server
            import mcp.types
            self.log_test_result("MCP Imports", True, "MCP server libraries available")
            
            # Test Playwright imports
            from playwright.async_api import async_playwright
            self.log_test_result("Playwright Imports", True, "Playwright async API available")
            
            # Test web scraping imports
            import requests
            import aiohttp
            from bs4 import BeautifulSoup
            self.log_test_result("Web Scraping Imports", True, "Requests, aiohttp, BeautifulSoup available")
            
            # Test image processing imports
            import numpy
            from PIL import Image
            self.log_test_result("Image Processing Imports", True, "NumPy and Pillow available")
            
            # Test our custom modules
            from scrapers.base_scraper import BaseScraper
            self.log_test_result("Custom Scraper Imports", True, "Base scraper classes available")
            
        except ImportError as e:
            self.log_test_result("Imports", False, "Import failed", str(e))
    
    async def test_playwright_functionality(self):
        """Test Playwright browser functionality"""
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as playwright:
                # Test browser launch
                browser = await playwright.chromium.launch(headless=True)
                self.log_test_result("Playwright Browser Launch", True, "Chromium browser launched successfully")
                
                # Test page creation
                context = await browser.new_context()
                page = await context.new_page()
                self.log_test_result("Playwright Page Creation", True, "Page context created successfully")
                
                # Test navigation to a simple page
                await page.goto('https://httpbin.org/html')
                title = await page.title()
                self.log_test_result("Playwright Navigation", True, f"Successfully navigated, title: {title}")
                
                # Test element selection
                h1_element = await page.query_selector('h1')
                if h1_element:
                    h1_text = await h1_element.inner_text()
                    self.log_test_result("Playwright Element Selection", True, f"Found H1: {h1_text}")
                else:
                    self.log_test_result("Playwright Element Selection", False, "Could not find H1 element")
                
                await browser.close()
                
        except Exception as e:
            self.log_test_result("Playwright Functionality", False, "Playwright test failed", str(e))
    
    async def test_config_loading(self):
        """Test configuration loading"""
        try:
            config_path = Path("config/mcp_config.json")
            
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    
                # Validate required config sections
                required_sections = ['storage', 'face_detection', 'categorization', 'legal']
                missing_sections = [section for section in required_sections if section not in config]
                
                if missing_sections:
                    self.log_test_result("Config Validation", False, f"Missing sections: {missing_sections}")
                else:
                    self.log_test_result("Config Loading", True, f"All required sections present: {list(config.keys())}")
                    
            else:
                self.log_test_result("Config Loading", False, "Config file not found", str(config_path))
                
        except Exception as e:
            self.log_test_result("Config Loading", False, "Config loading failed", str(e))
    
    async def test_directory_structure(self):
        """Test directory structure creation"""
        try:
            # Test main directories exist
            required_dirs = [
                "src",
                "src/scrapers", 
                "config",
                "data",
                "tests",
                "logs"
            ]
            
            missing_dirs = []
            existing_dirs = []
            
            for dir_path in required_dirs:
                path = Path(dir_path)
                if path.exists():
                    existing_dirs.append(dir_path)
                else:
                    missing_dirs.append(dir_path)
            
            if missing_dirs:
                self.log_test_result("Directory Structure", False, f"Missing dirs: {missing_dirs}")
            else:
                self.log_test_result("Directory Structure", True, f"All required directories exist: {existing_dirs}")
                
        except Exception as e:
            self.log_test_result("Directory Structure", False, "Directory check failed", str(e))
    
    async def test_scraper_instantiation(self):
        """Test scraper class instantiation"""
        try:
            from scrapers.base_scraper import GenericScraper, PornPicsScraper
            
            # Test GenericScraper
            config = {'delay': 1, 'max_retries': 3}
            generic_scraper = GenericScraper(config)
            self.log_test_result("Generic Scraper Instantiation", True, "GenericScraper created successfully")
            
            # Test PornPicsScraper
            pornpics_config = {'enabled': True, 'delay': 2, 'max_retries': 3}
            pornpics_scraper = PornPicsScraper(pornpics_config)
            self.log_test_result("PornPics Scraper Instantiation", True, "PornPicsScraper created successfully")
            
        except Exception as e:
            self.log_test_result("Scraper Instantiation", False, "Scraper creation failed", str(e))
    
    async def test_mcp_server_setup(self):
        """Test MCP server setup without running it"""
        try:
            # Load config
            config_path = Path("config/mcp_config.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
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
            
            # Test server instantiation
            from server import WebScraperMCPServer
            server_instance = WebScraperMCPServer(config)
            self.log_test_result("MCP Server Setup", True, "WebScraperMCPServer instantiated successfully")
            
        except Exception as e:
            self.log_test_result("MCP Server Setup", False, "Server setup failed", str(e))
    
    async def test_basic_web_request(self):
        """Test basic web request functionality"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get('https://httpbin.org/get') as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_test_result("Basic Web Request", True, f"HTTP request successful: {response.status}")
                    else:
                        self.log_test_result("Basic Web Request", False, f"HTTP request failed: {response.status}")
                        
        except Exception as e:
            self.log_test_result("Basic Web Request", False, "Web request failed", str(e))
    
    async def test_robots_txt_checking(self):
        """Test robots.txt checking functionality"""
        try:
            from urllib.robotparser import RobotFileParser
            
            # Test with a well-known robots.txt
            rp = RobotFileParser()
            rp.set_url("https://httpbin.org/robots.txt")
            rp.read()
            
            # Test if we can fetch for a user agent
            can_fetch = rp.can_fetch("*", "https://httpbin.org/get")
            self.log_test_result("Robots.txt Checking", True, f"Robots.txt parsing works, can_fetch: {can_fetch}")
            
        except Exception as e:
            self.log_test_result("Robots.txt Checking", False, "Robots.txt checking failed", str(e))
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*70)
        print("🧪 COMPREHENSIVE SYSTEM TEST SUMMARY")
        print("="*70)
        
        passed_tests = sum(1 for result in self.test_results.values() if result['passed'])
        total_tests = len(self.test_results)
        
        print(f"📊 Overall Results: {passed_tests}/{total_tests} tests passed")
        print(f"📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print("\n📋 Detailed Results:")
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"  {status} | {test_name}: {result['message']}")
            if result['error']:
                print(f"       Error: {result['error']}")
        
        print("\n" + "="*70)
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! System is ready for development and integration.")
        else:
            print("⚠️  Some tests failed. Please review and fix issues before proceeding.")
            print("\n🔧 Next Steps:")
            failed_tests = [name for name, result in self.test_results.items() if not result['passed']]
            for failed_test in failed_tests:
                print(f"   • Fix: {failed_test}")
        
        print("="*70)

    async def run_all_tests(self):
        """Run all system tests"""
        print("🚀 Starting Comprehensive System Test...")
        print("="*70)
        
        tests = [
            ("Import Tests", self.test_imports),
            ("Playwright Functionality", self.test_playwright_functionality),
            ("Configuration Loading", self.test_config_loading),
            ("Directory Structure", self.test_directory_structure),
            ("Scraper Instantiation", self.test_scraper_instantiation),
            ("MCP Server Setup", self.test_mcp_server_setup),
            ("Basic Web Requests", self.test_basic_web_request),
            ("Robots.txt Checking", self.test_robots_txt_checking)
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                await test_func()
            except Exception as e:
                self.log_test_result(test_name, False, "Test runner exception", str(e))
                traceback.print_exc()
        
        self.print_summary()


async def main():
    """Main test runner"""
    print("🧪 MCP Web Scraper - Complete System Test")
    print("Educational/Research Purpose Only")
    print("="*70)
    
    tester = SystemTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
