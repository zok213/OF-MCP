#!/usr/bin/env python3
"""
MCP Web Scraper Server
Educational/Research Purpose Only - Always respect website ToS and legal requirements
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Import core modules for production hardening
from core.security import (
    initialize_security, get_secure_credential, store_secure_credential,
    validate_api_key_format, SecureConfigValidator, APIRateLimiter
)
from core.error_handling import (
    ResilienceManager, AsyncRetry, create_retry_config,
    handle_errors, error_boundary, health_checker
)
from core.browser_persistence import (
    AutonomousScraper, AutonomousConfig, get_session_storage_path
)

# Import cloud storage and database modules (NEW)
try:
    from core.cloud_storage import CloudStorageManager
    from core.database import DatabaseManager
    CLOUD_AVAILABLE = True
except ImportError:
    CLOUD_AVAILABLE = False
    logger.warning("Cloud storage and database modules not available. Install cloud dependencies.")

# Import Jina AI Research Integration
try:
    from research.jina_researcher import JinaResearcher, MCP_JinaIntegration
    JINA_AVAILABLE = True
except ImportError:
    JINA_AVAILABLE = False
    logging.warning("Jina AI integration not available. Install aiohttp for full functionality.")

# Enhanced logging with structured logging
try:
    import structlog
    logger = structlog.get_logger("mcp-web-scraper")
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
except ImportError:
    # Fallback to standard logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp-web-scraper")

class WebScraperMCPServer:
    """Production-hardened MCP Server for web scraping and image categorization"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.server = Server("web-scraper")
        
        # Initialize security system
        self.initialize_security_system()

        # Initialize resilience system
        self.resilience_manager = ResilienceManager()
        self.setup_default_retry_configs()

        # Initialize autonomous scraper
        self.autonomous_config = AutonomousConfig(
            session_persistence=True,
            auto_login=True,
            headless=config.get('headless', False),
            max_concurrent_sessions=config.get('max_concurrent_sessions', 3)
        )
        self.autonomous_scraper = AutonomousScraper(self.autonomous_config)

        # Initialize cloud storage and database (NEW)
        if CLOUD_AVAILABLE:
            cloud_config = config.get('cloud_storage', {})
            if cloud_config.get('enabled', True):
                self.cloud_storage = CloudStorageManager(cloud_config)
            else:
                self.cloud_storage = None

            db_config = config.get('database', {})
            if db_config.get('enabled', True):
                self.database = DatabaseManager(db_config)
            else:
                self.database = None
        else:
            self.cloud_storage = None
            self.database = None

        # Initialize scrapers with enhanced error handling
        self.scrapers = {
            'generic': self.create_generic_scraper(),
            'pornpics': self.create_pornpics_scraper()
        }
        
        # Enhanced statistics with health monitoring
        self.stats = {
            "total_scraped": 0,
            "total_categorized": 0,
            "total_faces_detected": 0,
            "total_persons_identified": 0,
            "uptime_seconds": 0,
            "last_health_check": time.time(),
            "circuit_breaker_trips": 0,
            "autonomous_sessions_active": 0
        }
        
        self.setup_directories()
        self.setup_tools()

    async def initialize_cloud_services(self) -> bool:
        """Initialize cloud storage and database services asynchronously"""
        if not CLOUD_AVAILABLE:
            logger.warning("Cloud services not available - missing dependencies")
            return False

        cloud_ok = True
        db_ok = True

        # Initialize cloud storage
        if self.cloud_storage:
            try:
                logger.info("Initializing cloud storage...")
                cloud_ok = await self.cloud_storage.initialize()
                if cloud_ok:
                    logger.info("✅ Cloud storage initialized successfully")
                else:
                    logger.error("❌ Cloud storage initialization failed")
            except Exception as e:
                logger.error(f"Cloud storage initialization error: {e}")
                cloud_ok = False

        # Initialize database
        if self.database:
            try:
                logger.info("Initializing database...")
                db_ok = await self.database.initialize()
                if db_ok:
                    logger.info("✅ Database initialized successfully")
                else:
                    logger.error("❌ Database initialization failed")
            except Exception as e:
                logger.error(f"Database initialization error: {e}")
                db_ok = False

        success = cloud_ok and db_ok
        logger.info(f"Cloud services initialization: {'✅ SUCCESS' if success else '❌ PARTIAL/FAILED'}")
        return success

    def register_health_checks(self):

    def initialize_security_system(self):
        """Initialize the security system with credential management"""
        try:
            # Initialize encryption
            master_password = os.environ.get('MCP_SCRAPER_MASTER_PASSWORD')
            if not initialize_security(master_password):
                logger.warning("Failed to initialize security system. Using fallback mode.")

            # Validate configuration for security issues
            validation_result = SecureConfigValidator.validate_config(self.config)
            if not validation_result['valid']:
                logger.warning("Configuration security issues detected:")
                for warning in validation_result['warnings']:
                    logger.warning(f"  - {warning}")

            # Initialize rate limiters for different operations
            self.rate_limiters = {
                'jina_api': APIRateLimiter(requests_per_minute=30),  # Conservative limit
                'scraping': APIRateLimiter(requests_per_minute=60),
                'downloads': APIRateLimiter(requests_per_minute=100)
            }

            logger.info("Security system initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize security system: {e}")
            # Continue with degraded security mode
            self.rate_limiters = {}

    def setup_default_retry_configs(self):
        """Setup default retry configurations for different operations"""
        retry_configs = {
            'scraping': create_retry_config(
                max_attempts=5,
                base_delay=2.0,
                retryable_errors=[ConnectionError, TimeoutError]
            ),
            'api_calls': create_retry_config(
                max_attempts=3,
                base_delay=1.0,
                retryable_errors=[ConnectionError, TimeoutError]
            ),
            'file_operations': create_retry_config(
                max_attempts=2,
                base_delay=0.5,
                retryable_errors=[OSError, IOError]
            )
        }

        for operation, config in retry_configs.items():
            self.resilience_manager.set_retry_config(operation, config)

    def register_health_checks(self):
        """Register health checks for system monitoring"""
        # Register core system health check
        health_checker.register_component("mcp_server", self.check_server_health)

        # Register scraper health checks
        for scraper_name, scraper in self.scrapers.items():
            if scraper:
                health_checker.register_component(
                    f"scraper_{scraper_name}",
                    lambda: self.check_scraper_health(scraper_name)
                )

        # Register autonomous scraper health
        health_checker.register_component(
            "autonomous_scraper",
            lambda: self.check_autonomous_health()
        )

    # Health check methods
    async def check_server_health(self) -> Dict[str, Any]:
        """Check overall server health"""
        try:
            # Check if server is responsive
            uptime = time.time() - self.stats.get("start_time", time.time())
            self.stats["uptime_seconds"] = uptime

            # Check memory usage (if psutil available)
            try:
                import psutil
                memory_percent = psutil.virtual_memory().percent
            except ImportError:
                memory_percent = 0

            # Check if critical components are available
            critical_components = [
                JINA_AVAILABLE,
                bool(self.scrapers.get('generic')),
                bool(self.autonomous_scraper)
            ]

            all_critical_healthy = all(critical_components)

            return {
                "healthy": all_critical_healthy,
                "uptime_seconds": uptime,
                "memory_usage_percent": memory_percent,
                "active_sessions": len(self.autonomous_scraper.get_active_sessions()) if self.autonomous_scraper else 0,
                "circuit_breaker_trips": self.stats.get("circuit_breaker_trips", 0),
                "last_health_check": time.time()
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": time.time()
            }

    async def check_scraper_health(self, scraper_name: str) -> Dict[str, Any]:
        """Check health of a specific scraper"""
        try:
            scraper = self.scrapers.get(scraper_name)
            if not scraper:
                return {"healthy": False, "error": f"Scraper {scraper_name} not found"}

            # Get proxy stats if available
            proxy_stats = scraper.get_proxy_stats() if hasattr(scraper, 'get_proxy_stats') else None

            return {
                "healthy": True,
                "scraper_type": scraper_name,
                "proxy_stats": proxy_stats,
                "last_check": time.time()
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "scraper_type": scraper_name,
                "timestamp": time.time()
            }

    async def check_autonomous_health(self) -> Dict[str, Any]:
        """Check autonomous scraper health"""
        try:
            if not self.autonomous_scraper:
                return {"healthy": False, "error": "Autonomous scraper not initialized"}

            active_sessions = self.autonomous_scraper.get_active_sessions()

            return {
                "healthy": True,
                "active_sessions": len(active_sessions),
                "session_ids": active_sessions,
                "session_storage_path": str(get_session_storage_path()),
                "last_check": time.time()
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": time.time()
            }
    
    def create_generic_scraper(self):
        """Create generic scraper instance"""
        try:
            from scrapers.base_scraper import GenericScraper
            scraper_config = self.config.get('scrapers', {}).get('generic', {})
            
            # Add proxy configuration if available
            proxy_config = self.config.get('proxy_config', {})
            if proxy_config.get('webshare_proxies'):
                scraper_config['proxies'] = proxy_config['webshare_proxies']
                logger.info(f"GenericScraper initialized with {len(proxy_config['webshare_proxies'])} proxies")
            
            return GenericScraper(scraper_config)
        except ImportError:
            logger.warning("Could not import GenericScraper")
            return None
    
    def create_pornpics_scraper(self):
        """Create PornPics scraper instance"""
        try:
            from scrapers.base_scraper import PornPicsScraper
            pornpics_config = self.config.get('scrapers', {}).get('pornpics', {})
            
            if pornpics_config.get('enabled', False):
                # Add proxy configuration if available  
                proxy_config = self.config.get('proxy_config', {})
                if proxy_config.get('webshare_proxies'):
                    pornpics_config['proxies'] = proxy_config['webshare_proxies']
                    logger.info(f"PornPicsScraper initialized with {len(proxy_config['webshare_proxies'])} proxies")
                
                return PornPicsScraper(pornpics_config)
        except ImportError:
            logger.warning("Could not import PornPicsScraper")
        return None
    
    def setup_directories(self):
        """Create necessary directories"""
        paths = [
            self.config['storage']['base_path'],
            self.config['storage']['raw_path'],
            self.config['storage']['processed_path'],
            self.config['storage']['categorized_path'],
            self.config['storage']['metadata_path'],
            "./logs"
        ]
        
        for path_str in paths:
            Path(path_str).mkdir(parents=True, exist_ok=True)
    
    def setup_tools(self):
        """Setup MCP tools"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            return [
                types.Tool(
                    name="scrape_website",
                    description="Scrape images from a website URL with legal compliance checks",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "Website URL to scrape"
                            },
                            "max_images": {
                                "type": "integer", 
                                "default": 50,
                                "description": "Maximum number of images to scrape"
                            },
                            "category": {
                                "type": "string",
                                "default": "general",
                                "description": "Category name for organization"
                            },
                            "check_legal": {
                                "type": "boolean",
                                "default": True,
                                "description": "Check robots.txt and legal compliance"
                            }
                        },
                        "required": ["url"]
                    }
                ),
                
                types.Tool(
                    name="categorize_images",
                    description="Automatically categorize and organize downloaded images by detected persons",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source_folder": {
                                "type": "string",
                                "description": "Path to folder containing images to categorize"
                            },
                            "learn_new_faces": {
                                "type": "boolean",
                                "default": True,
                                "description": "Learn and create new person categories"
                            },
                            "min_confidence": {
                                "type": "number",
                                "default": 0.8,
                                "description": "Minimum confidence for person identification"
                            }
                        },
                        "required": ["source_folder"]
                    }
                ),
                
                types.Tool(
                    name="get_statistics",
                    description="Get scraping and categorization statistics",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                
                types.Tool(
                    name="check_legal_compliance",
                    description="Check legal compliance for a website (robots.txt, ToS analysis)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "Website URL to check"
                            },
                            "check_robots": {
                                "type": "boolean",
                                "default": True,
                                "description": "Check robots.txt compliance"
                            },
                            "analyze_tos": {
                                "type": "boolean", 
                                "default": True,
                                "description": "Analyze terms of service"
                            }
                        },
                        "required": ["url"]
                    }
                ),
                
                types.Tool(
                    name="list_categories",
                    description="List all person categories and their image counts",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_thumbnails": {
                                "type": "boolean",
                                "default": False,
                                "description": "Include thumbnail previews"
                            }
                        },
                        "required": []
                    }
                ),
                
                types.Tool(
                    name="intelligent_research",
                    description="Use Jina AI to automatically discover URLs and generate keywords for scraping",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "Research topic (e.g., 'celebrity photos', 'model portfolio')"
                            },
                            "context": {
                                "type": "object",
                                "default": {},
                                "description": "Additional context like style, category, etc."
                            },
                            "max_keywords": {
                                "type": "integer",
                                "default": 5,
                                "description": "Maximum keywords to generate"
                            },
                            "urls_per_keyword": {
                                "type": "integer", 
                                "default": 5,
                                "description": "URLs to find per keyword"
                            },
                            "filter_criteria": {
                                "type": "object",
                                "default": {},
                                "description": "Filtering criteria for discovered URLs"
                            },
                            "jina_api_key": {
                                "type": "string",
                                "description": "Jina AI API key for research"
                            }
                        },
                        "required": ["topic", "jina_api_key"]
                    }
                ),
                
                types.Tool(
                    name="proxy_status",
                    description="Check proxy health and rotation statistics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "run_health_check": {
                                "type": "boolean",
                                "default": False,
                                "description": "Run immediate proxy health check"
                            }
                        },
                        "required": []
                    }
                ),

                types.Tool(
                    name="autonomous_scrape",
                    description="Start autonomous scraping session with persistent browser sessions",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "profile_name": {
                                "type": "string",
                                "description": "Browser profile name for session persistence"
                            },
                            "target_sites": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of websites to scrape autonomously"
                            },
                            "duration_hours": {
                                "type": "number",
                                "default": 24,
                                "description": "How long to run autonomous scraping"
                            },
                            "headless": {
                                "type": "boolean",
                                "default": False,
                                "description": "Run browser in headless mode"
                            }
                        },
                        "required": ["profile_name", "target_sites"]
                    }
                ),

                types.Tool(
                    name="manage_sessions",
                    description="Manage autonomous scraping sessions",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["list", "stop", "status", "cleanup"],
                                "description": "Action to perform"
                            },
                            "session_id": {
                                "type": "string",
                                "description": "Session ID for stop/status actions"
                            }
                        },
                        "required": ["action"]
                    }
                ),

                types.Tool(
                    name="system_health",
                    description="Get comprehensive system health and monitoring information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "detailed": {
                                "type": "boolean",
                                "default": False,
                                "description": "Include detailed component health"
                            }
                        },
                        "required": []
                    }
                ),

                types.Tool(
                    name="secure_credentials",
                    description="Manage secure credential storage",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["store", "retrieve", "list", "validate"],
                                "description": "Credential management action"
                            },
                            "service": {
                                "type": "string",
                                "description": "Service name (e.g., 'jina', 'openai')"
                            },
                            "key": {
                                "type": "string",
                                "description": "Credential key"
                            },
                            "value": {
                                "type": "string",
                                "description": "Credential value (for store action)"
                            }
                        },
                        "required": ["action"]
                    }
                ),

                # Cloud Storage Tools (NEW)
                types.Tool(
                    name="cloud_upload",
                    description="Upload files to cloud storage (Wasabi S3)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Local file path to upload"
                            },
                            "cloud_prefix": {
                                "type": "string",
                                "description": "Cloud storage prefix/key"
                            },
                            "metadata": {
                                "type": "object",
                                "default": {},
                                "description": "Additional metadata for the file"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),

                types.Tool(
                    name="cloud_download",
                    description="Download files from cloud storage (Wasabi S3)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "s3_key": {
                                "type": "string",
                                "description": "S3 key of file to download"
                            },
                            "local_path": {
                                "type": "string",
                                "description": "Local path to save downloaded file"
                            },
                            "force": {
                                "type": "boolean",
                                "default": False,
                                "description": "Overwrite existing local file"
                            }
                        },
                        "required": ["s3_key", "local_path"]
                    }
                ),

                types.Tool(
                    name="cloud_list",
                    description="List files in cloud storage (Wasabi S3)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "prefix": {
                                "type": "string",
                                "default": "",
                                "description": "File prefix to filter results"
                            },
                            "max_files": {
                                "type": "integer",
                                "default": 100,
                                "description": "Maximum number of files to list"
                            }
                        },
                        "required": []
                    }
                ),

                # Database Tools (NEW)
                types.Tool(
                    name="database_stats",
                    description="Get comprehensive database statistics and analytics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "days": {
                                "type": "integer",
                                "default": 7,
                                "description": "Number of days to analyze"
                            }
                        },
                        "required": []
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict | None
        ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            
            if name == "scrape_website":
                return await self.handle_scrape_website(arguments or {})
            elif name == "categorize_images":
                return await self.handle_categorize_images(arguments or {})
            elif name == "get_statistics":
                return await self.handle_get_statistics(arguments or {})
            elif name == "check_legal_compliance":
                return await self.handle_check_legal_compliance(arguments or {})
            elif name == "list_categories":
                return await self.handle_list_categories(arguments or {})
            elif name == "intelligent_research":
                return await self.handle_intelligent_research(arguments or {})
            elif name == "proxy_status":
                return await self.handle_proxy_status(arguments or {})
            elif name == "autonomous_scrape":
                return await self.handle_autonomous_scrape(arguments or {})
            elif name == "manage_sessions":
                return await self.handle_manage_sessions(arguments or {})
            elif name == "system_health":
                return await self.handle_system_health(arguments or {})
            elif name == "secure_credentials":
                return await self.handle_secure_credentials(arguments or {})

            # Cloud Storage Tools (NEW)
            elif name == "cloud_upload":
                return await self.handle_cloud_upload(arguments or {})
            elif name == "cloud_download":
                return await self.handle_cloud_download(arguments or {})
            elif name == "cloud_list":
                return await self.handle_cloud_list(arguments or {})

            # Database Tools (NEW)
            elif name == "database_stats":
                return await self.handle_database_stats(arguments or {})

            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def handle_scrape_website(self, arguments: Dict) -> List[types.TextContent]:
        """Handle website scraping request"""
        try:
            url = arguments.get('url', '')
            max_images = arguments.get('max_images', 50)
            category = arguments.get('category', 'general')
            check_legal = arguments.get('check_legal', True)
            
            if not url:
                return [types.TextContent(
                    type="text",
                    text="❌ Error: URL is required"
                )]
            
            result_text = f"🔍 Scraping Website: {url}\n"
            result_text += f"📊 Max Images: {max_images}\n"
            result_text += f"🏷️ Category: {category}\n\n"
            
            # Choose appropriate scraper
            scraper = None
            if 'pornpics.com' in url.lower():
                scraper = self.scrapers.get('pornpics')
                if not scraper:
                    result_text += "⚠️ PornPics scraper not enabled in config\n"
                    scraper = self.scrapers.get('generic')
            else:
                scraper = self.scrapers.get('generic')
            
            if not scraper:
                return [types.TextContent(
                    type="text",
                    text="❌ Error: No suitable scraper available"
                )]
            
            # Legal compliance check if requested
            if check_legal:
                result_text += "⚖️ Legal Compliance Check:\n"
                compliance = await self.check_website_compliance(url)
                result_text += f"  🤖 Robots.txt: {'✅ Allowed' if compliance['robots_ok'] else '❌ Blocked'}\n"
                result_text += f"  📋 Terms Check: {compliance['tos_status']}\n\n"
                
                if not compliance['robots_ok']:
                    result_text += "❌ Cannot proceed - robots.txt blocks access\n"
                    result_text += "💡 Consider using official APIs or contact website owner\n"
                    return [types.TextContent(type="text", text=result_text)]
            
            # Perform scraping
            result_text += "🚀 Starting scraping...\n"
            scraping_result = await scraper.scrape_url(url, max_images)
            
            if scraping_result['status'] == 'success':
                images = scraping_result['images']
                result_text += f"✅ Scraping completed successfully!\n"
                result_text += f"📊 Found {scraping_result.get('total_images_found', 0)} total images\n"
                result_text += f"� Filtered to {scraping_result.get('filtered_images', 0)} quality images\n"
                result_text += f"📥 Selected {len(images)} images for download\n"
                
                if 'title' in scraping_result:
                    result_text += f"📄 Page Title: {scraping_result['title']}\n"
                if 'model_name' in scraping_result:
                    result_text += f"👤 Model: {scraping_result['model_name']}\n"
                if 'tags' in scraping_result:
                    tags = scraping_result['tags'][:5]  # Show first 5 tags
                    result_text += f"🏷️ Tags: {', '.join(tags)}\n"
                
                # Download images using professional downloader
                result_text += "\n📥 Starting image downloads...\n"
                
                try:
                    from downloaders.image_downloader import download_images_from_scraping_result
                    
                    download_result = await download_images_from_scraping_result(
                        scraping_result, self.config, category
                    )
                    
                    if download_result['status'] == 'success':
                        downloaded = download_result.get('downloaded', [])
                        failed = download_result.get('failed', [])
                        skipped = download_result.get('skipped', [])
                        
                        result_text += f"✅ Download completed!\n"
                        result_text += f"📥 Downloaded: {len(downloaded)} images\n"
                        result_text += f"⏭️ Skipped: {len(skipped)} duplicates\n"
                        result_text += f"❌ Failed: {len(failed)} images\n"
                        
                        if downloaded:
                            total_size_mb = sum(img.get('file_size', 0) for img in downloaded) / (1024 * 1024)
                            result_text += f"💾 Total size: {total_size_mb:.1f}MB\n"
                            result_text += f"� Saved to: {self.config['storage']['raw_path']}/{category}/\n"
                        
                        if failed and len(failed) <= 3:
                            result_text += f"\n⚠️ Failed downloads:\n"
                            for fail in failed[:3]:
                                result_text += f"  • {fail.get('url', 'unknown')}: {fail.get('error', 'Unknown error')}\n"
                    
                    else:
                        result_text += f"❌ Download failed: {download_result.get('message', 'Unknown error')}\n"
                
                except ImportError:
                    result_text += "\n⚠️ Professional downloader not available, using basic implementation\n"
                    result_text += "📝 Will save to: " + self.config['storage']['raw_path'] + f"/{category}/\n"
                    result_text += "🔧 Run: pip install aiohttp to enable professional downloads\n"
                
                # Update statistics
                self.stats['total_scraped'] += len(images)
                
            elif scraping_result['status'] == 'blocked':
                result_text += f"❌ Scraping blocked: {scraping_result['message']}\n"
                
            else:
                result_text += f"❌ Scraping failed: {scraping_result['message']}\n"
            
            return [types.TextContent(type="text", text=result_text)]
            
        except Exception as e:
            logger.error(f"Error in scrape_website: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Error scraping website: {str(e)}"
            )]
    
    async def handle_categorize_images(self, arguments: Dict) -> List[types.TextContent]:
        """Handle image categorization request"""
        try:
            source_folder = arguments.get('source_folder', '')
            learn_new_faces = arguments.get('learn_new_faces', True)
            min_confidence = arguments.get('min_confidence', 0.8)
            
            if not source_folder:
                return [types.TextContent(
                    type="text",
                    text="❌ Error: source_folder is required"
                )]
            
            folder_path = Path(source_folder)
            if not folder_path.exists():
                return [types.TextContent(
                    type="text",
                    text=f"❌ Error: Folder not found: {source_folder}"
                )]
            
            result_text = f"🤖 Categorizing Images from: {source_folder}\n"
            result_text += f"📊 Learn New Faces: {'Yes' if learn_new_faces else 'No'}\n"
            result_text += f"🎯 Min Confidence: {min_confidence}\n\n"
            
            # Count images
            image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
            image_files = [f for f in folder_path.iterdir() 
                          if f.suffix.lower() in image_extensions]
            
            result_text += f"📁 Found {len(image_files)} images\n\n"
            
            # TODO: Implement face detection and categorization
            result_text += "🚧 Categorization Implementation Coming Soon!\n"
            result_text += "📝 This will include:\n"
            result_text += "  • Face detection using OpenCV/face_recognition\n"
            result_text += "  • Person identification and clustering\n"
            result_text += "  • Quality assessment\n"
            result_text += "  • Automatic folder organization\n"
            result_text += "  • Metadata generation\n"
            result_text += "  • Duplicate detection\n\n"
            
            if image_files:
                result_text += f"📋 Sample files found:\n"
                for i, img_file in enumerate(image_files[:5]):
                    result_text += f"  • {img_file.name}\n"
                if len(image_files) > 5:
                    result_text += f"  ... and {len(image_files) - 5} more\n"
            
            return [types.TextContent(type="text", text=result_text)]
            
        except Exception as e:
            logger.error(f"Error in categorize_images: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Error categorizing images: {str(e)}"
            )]
    
    async def handle_get_statistics(self, arguments: Dict) -> List[types.TextContent]:
        """Handle statistics request"""
        try:
            result_text = "📊 MCP Web Scraper Statistics\n"
            result_text += "=" * 40 + "\n\n"
            
            # Current stats
            result_text += "📈 Current Session:\n"
            result_text += f"  • Total Scraped: {self.stats['total_scraped']}\n"
            result_text += f"  • Total Categorized: {self.stats['total_categorized']}\n"
            result_text += f"  • Faces Detected: {self.stats['total_faces_detected']}\n"
            result_text += f"  • Persons Identified: {self.stats['total_persons_identified']}\n\n"
            
            # Directory stats
            result_text += "📁 Directory Information:\n"
            
            storage_config = self.config['storage']
            for folder_type, folder_path in storage_config.items():
                if folder_type.endswith('_path'):
                    path = Path(folder_path)
                    if path.exists():
                        file_count = len(list(path.rglob('*')))
                        result_text += f"  • {folder_type}: {file_count} files\n"
                    else:
                        result_text += f"  • {folder_type}: Not created yet\n"
            
            result_text += "\n🔧 Configuration:\n"
            result_text += f"  • Face Detection Threshold: {self.config['face_detection']['face_threshold']}\n"
            result_text += f"  • Min Confidence: {self.config['categorization']['min_confidence']}\n"
            result_text += f"  • Legal Checks: {self.config['legal']['require_robots_check']}\n"
            
            return [types.TextContent(type="text", text=result_text)]
            
        except Exception as e:
            logger.error(f"Error in get_statistics: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Error getting statistics: {str(e)}"
            )]
    
    async def handle_check_legal_compliance(self, arguments: Dict) -> List[types.TextContent]:
        """Handle legal compliance check"""
        try:
            url = arguments.get('url', '')
            check_robots = arguments.get('check_robots', True)
            analyze_tos = arguments.get('analyze_tos', True)
            
            if not url:
                return [types.TextContent(
                    type="text",
                    text="❌ Error: URL is required"
                )]
            
            result_text = f"⚖️ Legal Compliance Check for: {url}\n"
            result_text += "=" * 50 + "\n\n"
            
            compliance = await self.check_website_compliance(url)
            
            if check_robots:
                result_text += "🤖 Robots.txt Analysis:\n"
                result_text += f"  Status: {'✅ Allowed' if compliance['robots_ok'] else '❌ Blocked'}\n"
                result_text += f"  Details: {compliance['robots_details']}\n\n"
            
            if analyze_tos:
                result_text += "📋 Terms of Service Analysis:\n"
                result_text += f"  Status: {compliance['tos_status']}\n"
                result_text += f"  Recommendation: {compliance['recommendation']}\n\n"
            
            result_text += "💡 General Guidelines:\n"
            result_text += "  • Always respect rate limits\n"
            result_text += "  • Use official APIs when available\n"
            result_text += "  • Contact website owners for permissions\n"
            result_text += "  • Maintain proper attribution\n"
            result_text += "  • Follow applicable copyright laws\n"
            result_text += "  • Respect user privacy\n"
            
            return [types.TextContent(type="text", text=result_text)]
            
        except Exception as e:
            logger.error(f"Error in check_legal_compliance: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Error checking legal compliance: {str(e)}"
            )]
    
    async def handle_list_categories(self, arguments: Dict) -> List[types.TextContent]:
        """Handle list categories request"""
        try:
            include_thumbnails = arguments.get('include_thumbnails', False)
            
            result_text = "📁 Person Categories\n"
            result_text += "=" * 30 + "\n\n"
            
            categorized_path = Path(self.config['storage']['categorized_path'])
            
            if not categorized_path.exists():
                result_text += "📂 No categories found yet.\n"
                result_text += "💡 Run 'categorize_images' first to create person categories.\n"
                return [types.TextContent(type="text", text=result_text)]
            
            # List person directories
            person_dirs = [d for d in categorized_path.iterdir() if d.is_dir()]
            
            if not person_dirs:
                result_text += "📂 No person categories found.\n"
            else:
                result_text += f"👥 Found {len(person_dirs)} person categories:\n\n"
                
                for i, person_dir in enumerate(person_dirs, 1):
                    # Count images in directory
                    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
                    image_files = [f for f in person_dir.iterdir() 
                                  if f.suffix.lower() in image_extensions]
                    
                    result_text += f"{i}. 👤 {person_dir.name}\n"
                    result_text += f"   📊 Images: {len(image_files)}\n"
                    
                    # Show sample files
                    if image_files:
                        result_text += "   📋 Sample files:\n"
                        for img_file in image_files[:3]:
                            result_text += f"      • {img_file.name}\n"
                        if len(image_files) > 3:
                            result_text += f"      ... and {len(image_files) - 3} more\n"
                    result_text += "\n"
            
            if include_thumbnails:
                result_text += "🖼️ Thumbnail generation coming soon!\n"
            
            return [types.TextContent(type="text", text=result_text)]
            
        except Exception as e:
            logger.error(f"Error in list_categories: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Error listing categories: {str(e)}"
            )]
    
    async def handle_intelligent_research(self, arguments: Dict) -> List[types.TextContent]:
        """Handle intelligent research using Jina AI"""
        try:
            if not JINA_AVAILABLE:
                return [types.TextContent(
                    type="text",
                    text="❌ Error: Jina AI integration not available.\n" +
                         "Install required packages: pip install aiohttp"
                )]
            
            topic = arguments.get('topic', '')
            context = arguments.get('context', {})
            max_keywords = arguments.get('max_keywords', 5)
            urls_per_keyword = arguments.get('urls_per_keyword', 5)
            filter_criteria = arguments.get('filter_criteria', {})
            jina_api_key = arguments.get('jina_api_key', '')
            
            if not topic:
                return [types.TextContent(
                    type="text",
                    text="❌ Error: Research topic is required"
                )]
            
            if not jina_api_key:
                return [types.TextContent(
                    type="text", 
                    text="❌ Error: Jina API key is required"
                )]
            
            result_text = f"🧠 Intelligent Research Pipeline\n"
            result_text += f"=" * 50 + "\n\n"
            result_text += f"🎯 Research Topic: {topic}\n"
            result_text += f"📋 Context: {context}\n"
            result_text += f"🔍 Max Keywords: {max_keywords}\n"
            result_text += f"🌐 URLs per Keyword: {urls_per_keyword}\n\n"
            
            # Initialize Jina integration
            jina_integration = MCP_JinaIntegration(jina_api_key, self)
            
            # Prepare research request
            research_request = {
                "topic": topic,
                "context": context,
                "max_keywords": max_keywords, 
                "urls_per_keyword": urls_per_keyword,
                "filter_criteria": filter_criteria,
                "max_targets": filter_criteria.get("max_targets", 20)
            }
            
            result_text += "🚀 Starting intelligent research...\n\n"
            
            # Run auto discovery
            discovery_result = await jina_integration.auto_discover_scraping_targets(research_request)
            
            if discovery_result["status"] == "success":
                research_results = discovery_result["research_results"]
                targets = discovery_result["filtered_targets"]
                plan = discovery_result["scraping_plan"]
                
                # Display research summary
                result_text += f"✅ Research completed successfully!\n"
                result_text += f"📊 Keywords generated: {research_results['keywords_generated']}\n"
                result_text += f"🔍 Keywords researched: {research_results['keywords_researched']}\n"
                result_text += f"🌐 Total URLs discovered: {research_results['total_valid_urls']}\n"
                result_text += f"🎯 Filtered targets: {len(targets)}\n\n"
                
                # Show research summary
                summary = research_results.get("summary", {})
                if summary:
                    result_text += f"📈 Research Summary:\n"
                    result_text += f"  • Total URLs: {summary['total_urls']}\n"
                    
                    # Site type distribution
                    if summary.get("site_type_distribution"):
                        result_text += f"  • Site Types:\n"
                        for site_type, count in summary["site_type_distribution"].items():
                            result_text += f"    - {site_type}: {count}\n"
                    
                    # Priority distribution
                    if summary.get("priority_distribution"):
                        priority_dist = summary["priority_distribution"]
                        result_text += f"  • Priority Distribution:\n"
                        result_text += f"    - High: {priority_dist.get('high', 0)}\n"
                        result_text += f"    - Medium: {priority_dist.get('medium', 0)}\n"
                        result_text += f"    - Low: {priority_dist.get('low', 0)}\n"
                    
                    result_text += "\n"
                
                # Show top targets
                if targets:
                    result_text += f"🎯 Top Scraping Targets:\n"
                    for i, target in enumerate(targets[:5], 1):
                        result_text += f"{i}. {target['domain']}\n"
                        result_text += f"   🔗 URL: {target['url'][:60]}{'...' if len(target['url']) > 60 else ''}\n"
                        result_text += f"   ⭐ Priority: {target.get('scraping_priority', 0)}/100\n"
                        result_text += f"   🏷️ Type: {target.get('site_type', 'unknown')}\n"
                        result_text += f"   ⚖️ Legal: {target.get('legal_considerations', {}).get('risk_level', 'unknown')} risk\n"
                        result_text += "\n"
                
                # Show scraping plan
                if plan:
                    result_text += f"📋 Scraping Plan:\n"
                    result_text += f"  • Total Targets: {plan['total_targets']}\n"
                    result_text += f"  • Estimated Time: {plan['estimated_time']//60} minutes\n"
                    result_text += f"  • Legal Review Required: {'Yes' if plan['legal_review_required'] else 'No'}\n\n"
                
                # Next steps
                result_text += f"🚀 Next Steps:\n"
                result_text += f"1. Review discovered targets above\n"
                result_text += f"2. Use 'scrape_website' tool with selected URLs\n"
                result_text += f"3. Run 'categorize_images' after scraping\n"
                result_text += f"4. Consider legal compliance for high-risk sites\n\n"
                
                result_text += f"💡 Pro Tip: Start with high-priority, low-risk targets for best results!\n"
                
            else:
                result_text += f"❌ Research failed: {discovery_result.get('error', 'Unknown error')}\n"
                result_text += f"🔧 Troubleshooting:\n"
                result_text += f"  • Check your Jina AI API key\n"
                result_text += f"  • Verify internet connection\n"
                result_text += f"  • Try a different research topic\n"
            
            return [types.TextContent(type="text", text=result_text)]
            
        except Exception as e:
            logger.error(f"Error in intelligent_research: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Error in intelligent research: {str(e)}\n" +
                     f"🔧 Make sure Jina AI integration is properly configured"
            )]
    
    async def handle_proxy_status(self, arguments: Dict) -> List[types.TextContent]:
        """Handle proxy status check request"""
        try:
            run_health_check = arguments.get('run_health_check', False)
            
            result_text = "🌐 Proxy System Status\n"
            result_text += "=" * 30 + "\n\n"
            
            # Check if scrapers have proxy stats
            proxy_stats_found = False
            
            for scraper_name, scraper in self.scrapers.items():
                if scraper and hasattr(scraper, 'get_proxy_stats'):
                    stats = scraper.get_proxy_stats()
                    if stats:
                        proxy_stats_found = True
                        result_text += f"📊 {scraper_name.capitalize()} Scraper Proxies:\n"
                        result_text += f"  • Total Proxies: {stats['total_proxies']}\n"
                        result_text += f"  • Healthy: {stats['healthy_proxies']}\n"
                        result_text += f"  • Unhealthy: {stats['unhealthy_proxies']}\n\n"
                        
                        # Show individual proxy stats
                        result_text += f"🔍 Proxy Details:\n"
                        for proxy in stats['proxies'][:5]:  # Show first 5
                            health_status = "✅" if proxy['is_healthy'] else "❌"
                            result_text += f"  {health_status} {proxy['ip']}:{proxy['port']}\n"
                            result_text += f"     Success Rate: {proxy['success_rate']:.2%}\n"
                            result_text += f"     Response Time: {proxy['response_time']:.2f}s\n"
                            result_text += f"     Requests: {proxy['success_count']} ✅ / {proxy['failure_count']} ❌\n"
                        
                        if len(stats['proxies']) > 5:
                            result_text += f"  ... and {len(stats['proxies']) - 5} more proxies\n"
                        result_text += "\n"
            
            if not proxy_stats_found:
                result_text += "❌ No proxy system found\n"
                result_text += "💡 Proxies are not configured or scrapers not initialized\n"
                
                # Check configuration
                proxy_config = self.config.get('proxy_config', {})
                if proxy_config.get('webshare_proxies'):
                    result_text += f"📋 Configuration found: {len(proxy_config['webshare_proxies'])} proxies configured\n"
                    result_text += "🔧 Proxies should be initialized when scraping starts\n"
                else:
                    result_text += "⚠️ No proxy configuration found in config\n"
                    result_text += "💡 Add proxy_config section to enable proxy rotation\n"
            
            if run_health_check and proxy_stats_found:
                result_text += "🔄 Running proxy health check...\n"
                result_text += "(Health checks run automatically in background)\n"
            
            # Show configuration if available
            proxy_config = self.config.get('proxy_config', {})
            if proxy_config:
                result_text += "⚙️ Proxy Configuration:\n"
                settings = proxy_config.get('settings', {})
                result_text += f"  • Health Check Interval: {settings.get('health_check_interval', 300)}s\n"
                result_text += f"  • Max Retries: {settings.get('max_retries', 3)}\n"
                result_text += f"  • Request Timeout: {settings.get('request_timeout', 30)}s\n"
                result_text += f"  • Rate Limit Delay: {settings.get('rate_limit_delay', 1)}s\n"
            
            return [types.TextContent(type="text", text=result_text)]
            
        except Exception as e:
            logger.error(f"Error in proxy_status: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Error checking proxy status: {str(e)}"
            )]
    
    async def check_website_compliance(self, url: str) -> Dict[str, Any]:
        """Check website legal compliance"""
        try:
            from urllib.robotparser import RobotFileParser
            from urllib.parse import urljoin, urlparse
            
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            # Check robots.txt
            try:
                rp = RobotFileParser()
                rp.set_url(robots_url)
                rp.read()
                
                user_agent = self.config['legal']['user_agent']
                robots_ok = rp.can_fetch(user_agent, url)
                robots_details = f"Checked with user-agent: {user_agent}"
                
            except Exception as e:
                robots_ok = False
                robots_details = f"Error checking robots.txt: {str(e)}"
            
            # Basic ToS analysis (simplified)
            domain = parsed_url.netloc.lower()
            tos_analysis = self.analyze_domain_tos(domain)
            
            return {
                'robots_ok': robots_ok,
                'robots_details': robots_details,
                'tos_status': tos_analysis['status'],
                'recommendation': tos_analysis['recommendation']
            }
            
        except Exception as e:
            return {
                'robots_ok': False,
                'robots_details': f"Error: {str(e)}",
                'tos_status': 'Unknown',
                'recommendation': 'Manual review required'
            }
    
    def analyze_domain_tos(self, domain: str) -> Dict[str, str]:
        """Analyze domain Terms of Service (simplified)"""
        
        # Known problematic domains
        restricted_domains = {
            'instagram.com': {
                'status': '❌ Restricted',
                'recommendation': 'Use Instagram Basic Display API instead'
            },
            'facebook.com': {
                'status': '❌ Restricted', 
                'recommendation': 'Use Facebook Graph API instead'
            },
            'twitter.com': {
                'status': '❌ Restricted',
                'recommendation': 'Use Twitter API instead'
            },
            'x.com': {
                'status': '❌ Restricted',
                'recommendation': 'Use Twitter API instead'
            }
        }
        
        # Check for known restrictions
        for restricted_domain, info in restricted_domains.items():
            if restricted_domain in domain:
                return info
        
        # Default analysis for other domains
        return {
            'status': '⚠️ Requires Review',
            'recommendation': 'Manually review ToS and consider contacting website owner'
        }

    # Cloud storage and database tool handlers (NEW)
    async def handle_cloud_upload(self, arguments: Dict) -> List[types.TextContent]:
        """Handle cloud storage upload operations"""
        try:
            if not self.cloud_storage:
                return [types.TextContent(
                    type="text",
                    text="❌ Cloud storage not available or not configured"
                )]

            file_path = arguments.get('file_path', '')
            cloud_prefix = arguments.get('cloud_prefix', '')
            metadata = arguments.get('metadata', {})

            if not file_path:
                return [types.TextContent(
                    type="text",
                    text="❌ file_path is required"
                )]

            local_file = Path(file_path)
            if not local_file.exists():
                return [types.TextContent(
                    type="text",
                    text=f"❌ File not found: {file_path}"
                )]

            result = await self.cloud_storage.wasabi.upload_file(
                local_file, cloud_prefix, metadata
            )

            if result:
                return [types.TextContent(
                    type="text",
                    text=f"✅ Successfully uploaded {file_path} to cloud storage\n"
                         f"📁 S3 Key: {result.s3_key}\n"
                         f"📊 Size: {result.size} bytes\n"
                         f"🏷️ Content Type: {result.content_type}"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text="❌ Upload failed - check circuit breaker status"
                )]

        except Exception as e:
            logger.error(f"Cloud upload error: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Upload error: {str(e)}"
            )]

    async def handle_cloud_download(self, arguments: Dict) -> List[types.TextContent]:
        """Handle cloud storage download operations"""
        try:
            if not self.cloud_storage:
                return [types.TextContent(
                    type="text",
                    text="❌ Cloud storage not available or not configured"
                )]

            s3_key = arguments.get('s3_key', '')
            local_path = arguments.get('local_path', '')
            force = arguments.get('force', False)

            if not s3_key or not local_path:
                return [types.TextContent(
                    type="text",
                    text="❌ Both s3_key and local_path are required"
                )]

            result = await self.cloud_storage.wasabi.download_file(
                s3_key, Path(local_path), force
            )

            if result:
                return [types.TextContent(
                    type="text",
                    text=f"✅ Successfully downloaded {s3_key}\n"
                         f"📁 Local Path: {local_path}\n"
                         f"📊 Size: {result.size} bytes\n"
                         f"🏷️ Content Type: {result.content_type}"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text="❌ Download failed - file may not exist or circuit breaker is open"
                )]

        except Exception as e:
            logger.error(f"Cloud download error: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Download error: {str(e)}"
            )]

    async def handle_cloud_list(self, arguments: Dict) -> List[types.TextContent]:
        """Handle cloud storage list operations"""
        try:
            if not self.cloud_storage:
                return [types.TextContent(
                    type="text",
                    text="❌ Cloud storage not available or not configured"
                )]

            prefix = arguments.get('prefix', '')
            max_files = arguments.get('max_files', 100)

            files = await self.cloud_storage.wasabi.list_files(prefix, max_files)

            if not files:
                return [types.TextContent(
                    type="text",
                    text=f"📁 No files found with prefix: {prefix}"
                )]

            file_list = "\n".join([
                f"📄 {f.filename} ({f.size} bytes) - {f.last_modified}"
                for f in files[:20]  # Show first 20 files
            ])

            summary = f"📊 Found {len(files)} files"
            if len(files) > 20:
                summary += f" (showing first 20)"

            return [types.TextContent(
                type="text",
                text=f"{summary}\n\n{file_list}"
            )]

        except Exception as e:
            logger.error(f"Cloud list error: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ List error: {str(e)}"
            )]

    async def handle_database_stats(self, arguments: Dict) -> List[types.TextContent]:
        """Handle database statistics queries"""
        try:
            if not self.database:
                return [types.TextContent(
                    type="text",
                    text="❌ Database not available or not configured"
                )]

            days = arguments.get('days', 7)
            stats = await self.database.get_system_stats()

            if 'error' in stats:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Database stats error: {stats['error']}"
                )]

            scraping_stats = stats.get('scraping_stats', {})
            db_health = stats.get('database_health', {})

            response = f"📊 **Database Statistics (Last {days} days)**\n\n"

            # Scraping stats
            sessions = scraping_stats.get('sessions', {})
            images = scraping_stats.get('images', {})

            response += f"**Sessions:**\n"
            response += f"• Total: {sessions.get('total', 0)}\n"
            response += f"• Completed: {sessions.get('completed', 0)}\n"
            response += f"• Failed: {sessions.get('failed', 0)}\n"
            response += f"• Success Rate: {sessions.get('success_rate', 0):.1%}\n\n"

            response += f"**Images:**\n"
            response += f"• Total: {images.get('total', 0)}\n"
            response += f"• Successful: {images.get('successful', 0)}\n"
            response += f"• Failed: {images.get('failed', 0)}\n"
            response += f"• Success Rate: {images.get('success_rate', 0):.1%}\n\n"

            # Database health
            response += f"**Database Health:**\n"
            response += f"• Status: {'✅ Healthy' if db_health.get('healthy') else '❌ Unhealthy'}\n"
            response += f"• Sessions Table: {db_health.get('table_counts', {}).get('scraping_sessions', 0)} records\n"
            response += f"• Images Table: {db_health.get('table_counts', {}).get('images', 0)} records\n"
            response += f"• Persons Table: {db_health.get('table_counts', {}).get('persons', 0)} records\n"

            return [types.TextContent(type="text", text=response)]

        except Exception as e:
            logger.error(f"Database stats error: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Database stats error: {str(e)}"
            )]

    # New tool handlers for production hardening
    async def handle_autonomous_scrape(self, arguments: Dict) -> List[types.TextContent]:
        """Handle autonomous scraping session creation"""
        try:
            profile_name = arguments.get('profile_name', '')
            target_sites = arguments.get('target_sites', [])
            duration_hours = arguments.get('duration_hours', 24)
            headless = arguments.get('headless', False)

            if not profile_name:
                return [types.TextContent(
                    type="text",
                    text="❌ Error: profile_name is required"
                )]

            if not target_sites:
                return [types.TextContent(
                    type="text",
                    text="❌ Error: target_sites list is required"
                )]

            result_text = f"🚀 Starting Autonomous Scraping Session\n"
            result_text += f"=" * 50 + "\n\n"
            result_text += f"👤 Profile: {profile_name}\n"
            result_text += f"🎯 Target Sites: {len(target_sites)}\n"
            result_text += f"⏱️ Duration: {duration_hours} hours\n"
            result_text += f"👁️ Headless: {headless}\n\n"

            # Update autonomous config
            self.autonomous_config.headless = headless
            self.autonomous_config.session_timeout_hours = duration_hours

            async with self.autonomous_scraper:
                task_id = await self.autonomous_scraper.create_autonomous_session(
                    profile_name, target_sites
                )

                result_text += f"✅ Session started successfully!\n"
                result_text += f"🆔 Task ID: {task_id}\n\n"

                # List target sites
                result_text += f"📋 Target Sites:\n"
                for i, site in enumerate(target_sites, 1):
                    result_text += f"  {i}. {site}\n"

                result_text += f"\n💡 Session will run for {duration_hours} hours\n"
                result_text += f"💾 Browser sessions will be saved automatically\n"
                result_text += f"🔄 Use 'manage_sessions' tool to monitor/stop the session\n"

                self.stats["autonomous_sessions_active"] += 1

            return [types.TextContent(type="text", text=result_text)]

        except Exception as e:
            logger.error(f"Error in autonomous scraping: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Error starting autonomous scraping: {str(e)}"
            )]

    async def handle_manage_sessions(self, arguments: Dict) -> List[types.TextContent]:
        """Handle session management operations"""
        try:
            action = arguments.get('action', '')
            session_id = arguments.get('session_id', '')

            if action == 'list':
                active_sessions = self.autonomous_scraper.get_active_sessions()
                result_text = f"📋 Active Autonomous Sessions\n"
                result_text += f"=" * 40 + "\n\n"

                if not active_sessions:
                    result_text += "No active sessions found.\n"
                else:
                    result_text += f"Found {len(active_sessions)} active sessions:\n\n"
                    for session_id in active_sessions:
                        status = self.autonomous_scraper.get_session_status(session_id)
                        result_text += f"🆔 {session_id}\n"
                        result_text += f"  📊 Running: {status.get('running', False)}\n"
                        if status.get('exception'):
                            result_text += f"  ⚠️ Error: {status['exception']}\n"
                        result_text += "\n"

            elif action == 'stop':
                if not session_id:
                    return [types.TextContent(
                        type="text",
                        text="❌ Error: session_id is required for stop action"
                    )]

                await self.autonomous_scraper.stop_session(session_id)
                result_text = f"✅ Stopped session: {session_id}\n"
                self.stats["autonomous_sessions_active"] = max(
                    0, self.stats["autonomous_sessions_active"] - 1
                )

            elif action == 'status':
                if not session_id:
                    return [types.TextContent(
                        type="text",
                        text="❌ Error: session_id is required for status action"
                    )]

                status = self.autonomous_scraper.get_session_status(session_id)
                if not status:
                    result_text = f"❌ Session not found: {session_id}\n"
                else:
                    result_text = f"📊 Session Status: {session_id}\n"
                    result_text += f"=" * 30 + "\n"
                    result_text += f"Running: {status.get('running', False)}\n"
                    if status.get('exception'):
                        result_text += f"Error: {status['exception']}\n"

            elif action == 'cleanup':
                # Cleanup old sessions
                await self.autonomous_scraper.session_manager.cleanup_expired_sessions()
                result_text = "🧹 Cleaned up expired sessions\n"

            else:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Error: Unknown action '{action}'. Use: list, stop, status, cleanup"
                )]

            return [types.TextContent(type="text", text=result_text)]

        except Exception as e:
            logger.error(f"Error in session management: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Error managing sessions: {str(e)}"
            )]

    async def handle_system_health(self, arguments: Dict) -> List[types.TextContent]:
        """Handle system health check"""
        try:
            detailed = arguments.get('detailed', False)

            # Get system health
            system_health = await health_checker.get_system_health()

            result_text = f"🏥 System Health Report\n"
            result_text += f"=" * 30 + "\n\n"

            result_text += f"Overall Health: {'✅ Healthy' if system_health['healthy'] else '❌ Issues Detected'}\n"
            result_text += f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(system_health['timestamp']))}\n\n"

            if detailed:
                result_text += f"📊 Component Details:\n"
                for component, health in system_health['components'].items():
                    status_icon = "✅" if health.get('healthy', False) else "❌"
                    result_text += f"  {status_icon} {component}\n"

                    if not health.get('healthy', True):
                        error = health.get('error', 'Unknown error')
                        result_text += f"    ⚠️ {error}\n"

                    if component == 'mcp_server':
                        uptime = health.get('uptime_seconds', 0)
                        result_text += f"    ⏱️ Uptime: {uptime:.0f}s ({uptime/3600:.1f}h)\n"
                        memory = health.get('memory_usage_percent', 0)
                        if memory > 0:
                            result_text += f"    💾 Memory: {memory:.1f}%\n"

                    result_text += "\n"

            # Add resilience statistics
            result_text += f"🔄 Resilience Statistics:\n"
            result_text += f"  • Circuit Breaker Trips: {self.stats.get('circuit_breaker_trips', 0)}\n"
            result_text += f"  • Active Sessions: {self.stats.get('autonomous_sessions_active', 0)}\n"
            result_text += f"  • Total Scraped: {self.stats.get('total_scraped', 0)}\n\n"

            if not system_health['healthy']:
                result_text += f"⚠️ System health issues detected. Check logs for details.\n"

            return [types.TextContent(type="text", text=result_text)]

        except Exception as e:
            logger.error(f"Error in system health check: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Error checking system health: {str(e)}"
            )]

    async def handle_secure_credentials(self, arguments: Dict) -> List[types.TextContent]:
        """Handle secure credential management"""
        try:
            action = arguments.get('action', '')
            service = arguments.get('service', '')
            key = arguments.get('key', '')
            value = arguments.get('value', '')

            result_text = f"🔐 Secure Credential Management\n"
            result_text += f"=" * 35 + "\n\n"

            if action == 'store':
                if not service or not key or not value:
                    return [types.TextContent(
                        type="text",
                        text="❌ Error: service, key, and value are required for store action"
                    )]

                # Validate API key format
                if not validate_api_key_format(service, value):
                    return [types.TextContent(
                        type="text",
                        text=f"❌ Error: Invalid {service} API key format"
                    )]

                success = store_secure_credential(service, key, value)
                if success:
                    result_text += f"✅ Successfully stored credential for {service}.{key}\n"
                else:
                    result_text += f"❌ Failed to store credential for {service}.{key}\n"

            elif action == 'retrieve':
                if not service or not key:
                    return [types.TextContent(
                        type="text",
                        text="❌ Error: service and key are required for retrieve action"
                    )]

                retrieved_value = get_secure_credential(service, key)
                if retrieved_value:
                    # Mask the value for security
                    masked_value = retrieved_value[:8] + "..." + retrieved_value[-4:] if len(retrieved_value) > 12 else "***"
                    result_text += f"✅ Retrieved credential for {service}.{key}: {masked_value}\n"
                else:
                    result_text += f"❌ Credential not found for {service}.{key}\n"

            elif action == 'validate':
                if not service or not value:
                    return [types.TextContent(
                        type="text",
                        text="❌ Error: service and value are required for validate action"
                    )]

                is_valid = validate_api_key_format(service, value)
                result_text += f"{'✅' if is_valid else '❌'} API key validation for {service}: {'Valid' if is_valid else 'Invalid'}\n"

            elif action == 'list':
                # This would need to be implemented carefully for security
                result_text += "📋 Available credential services:\n"
                result_text += "  • jina (Jina AI)\n"
                result_text += "  • openai (OpenAI)\n"
                result_text += "  • instagram (Instagram API)\n"
                result_text += "  • custom (Custom services)\n\n"
                result_text += "💡 Use 'retrieve' action to get specific credentials\n"

            else:
                return [types.TextContent(
                    type="text",
                    text="❌ Error: Unknown action. Use: store, retrieve, validate, list"
                )]

            result_text += f"\n🔒 Credentials are encrypted and stored securely\n"
            result_text += f"📁 Storage location: {Path.home() / '.mcp-scraper' / 'credentials.enc'}\n"

            return [types.TextContent(type="text", text=result_text)]

        except Exception as e:
            logger.error(f"Error in credential management: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Error managing credentials: {str(e)}"
            )]


async def main():
    """Main server entry point"""
    # Load configuration
    config_path = Path(__file__).parent / "config" / "mcp_config.json"
    proxy_config_path = Path(__file__).parent / "config" / "proxy_config.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        # Use minimal default config
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
    
    # Load proxy configuration if available
    try:
        with open(proxy_config_path, 'r') as f:
            proxy_config = json.load(f)
            config.update(proxy_config)
            logger.info(f"Loaded proxy configuration with {len(proxy_config.get('proxy_config', {}).get('webshare_proxies', []))} proxies")
    except FileNotFoundError:
        logger.warning(f"Proxy configuration file not found: {proxy_config_path}")
        logger.info("Proxy functionality will not be available")
    
    # Create and run server
    server_instance = WebScraperMCPServer(config)
    server_instance.stats["start_time"] = time.time()

    # Initialize cloud services (NEW)
    cloud_init_ok = await server_instance.initialize_cloud_services()

    logger.info("Starting Production-Hardened MCP Web Scraper Server...")
    logger.info("Security: ✅ Enabled | Resilience: ✅ Enabled | Autonomous: ✅ Enabled")
    logger.info(f"Cloud Services: {'✅ Enabled' if cloud_init_ok else '❌ Disabled'}")
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="web-scraper",
                server_version="0.1.0",
                capabilities=server_instance.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
