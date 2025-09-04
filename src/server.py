#!/usr/bin/env python3
"""
MCP Web Scraper Server
Educational/Research Purpose Only - Always respect website ToS and legal requirements
"""

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Import environment utilities
try:
    from utils.env_loader import get_secure_config, check_environment_health

    ENV_UTILS_AVAILABLE = True
except ImportError:
    ENV_UTILS_AVAILABLE = False
    logging.warning("Environment utilities not available")

# Import Jina AI Research Integration
try:
    from research.jina_researcher import JinaResearcher, MCP_JinaIntegration

    JINA_AVAILABLE = True
except ImportError:
    JINA_AVAILABLE = False
    logging.warning(
        "Jina AI integration not available. Install aiohttp for full functionality."
    )

# Import RFT Integration
try:
    from rft_integration import (
        RFTSupabaseClient,
        RFTTrainingManager,
        integrate_with_mcp_scraper,
    )

    RFT_AVAILABLE = True
except ImportError:
    RFT_AVAILABLE = False
    logging.warning(
        "RFT integration not available. Install aiohttp for full functionality."
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp-web-scraper")


def load_config_with_env_vars(config_path: str) -> Dict:
    """Load configuration and substitute environment variables"""
    with open(config_path, "r") as f:
        config_content = f.read()

    # Replace environment variable placeholders
    import re

    def replace_env_var(match):
        env_var = match.group(1)
        return os.getenv(
            env_var, match.group(0)
        )  # Return original if env var not found

    config_content = re.sub(r"\$\{([^}]+)\}", replace_env_var, config_content)

    try:
        return json.loads(config_content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse configuration: {e}")
        logger.info(
            "Make sure to set required environment variables: SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY"
        )
        raise


class WebScraperMCPServer:
    """MCP Server for web scraping and image categorization"""

    def __init__(self, config: Dict):
        self.config = config
        self.server = Server("web-scraper")

        # Initialize scrapers
        self.scrapers = {
            "generic": self.create_generic_scraper(),
            "pornpics": self.create_pornpics_scraper(),
        }

        self.stats = {
            "total_scraped": 0,
            "total_categorized": 0,
            "total_faces_detected": 0,
            "total_persons_identified": 0,
            "rft_sessions": 0,
            "rft_responses": 0,
        }

        # Initialize RFT integration if available
        self.rft_client = None
        self.rft_manager = None
        if RFT_AVAILABLE and config.get("supabase"):
            try:
                self.rft_client = RFTSupabaseClient(
                    config["supabase"]["url"], config["supabase"].get("anon_key")
                )
                self.rft_manager = RFTTrainingManager(
                    self.rft_client, config["supabase"]
                )
                logger.info("RFT integration initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize RFT integration: {e}")

        self.setup_directories()
        self.setup_tools()

    def create_generic_scraper(self):
        """Create generic scraper instance"""
        try:
            from scrapers.base_scraper import GenericScraper

            scraper_config = self.config.get("scrapers", {}).get("generic", {})

            # Add proxy configuration if available
            proxy_config = self.config.get("proxy_config", {})
            if proxy_config.get("webshare_proxies"):
                scraper_config["proxies"] = proxy_config["webshare_proxies"]
                logger.info(
                    f"GenericScraper initialized with {len(proxy_config['webshare_proxies'])} proxies"
                )

            return GenericScraper(scraper_config)
        except ImportError:
            logger.warning("Could not import GenericScraper")
            return None

    def create_pornpics_scraper(self):
        """Create PornPics scraper instance"""
        try:
            from scrapers.base_scraper import PornPicsScraper

            pornpics_config = self.config.get("scrapers", {}).get("pornpics", {})

            if pornpics_config.get("enabled", False):
                # Add proxy configuration if available
                proxy_config = self.config.get("proxy_config", {})
                if proxy_config.get("webshare_proxies"):
                    pornpics_config["proxies"] = proxy_config["webshare_proxies"]
                    logger.info(
                        f"PornPicsScraper initialized with {len(proxy_config['webshare_proxies'])} proxies"
                    )

                return PornPicsScraper(pornpics_config)
        except ImportError:
            logger.warning("Could not import PornPicsScraper")
        return None

    def setup_directories(self):
        """Create necessary directories"""
        paths = [
            self.config["storage"]["base_path"],
            self.config["storage"]["raw_path"],
            self.config["storage"]["processed_path"],
            self.config["storage"]["categorized_path"],
            self.config["storage"]["metadata_path"],
            "./logs",
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
                                "description": "Website URL to scrape",
                            },
                            "max_images": {
                                "type": "integer",
                                "default": 50,
                                "description": "Maximum number of images to scrape",
                            },
                            "category": {
                                "type": "string",
                                "default": "general",
                                "description": "Category name for organization",
                            },
                            "check_legal": {
                                "type": "boolean",
                                "default": True,
                                "description": "Check robots.txt and legal compliance",
                            },
                        },
                        "required": ["url"],
                    },
                ),
                types.Tool(
                    name="categorize_images",
                    description="Automatically categorize and organize downloaded images by detected persons",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source_folder": {
                                "type": "string",
                                "description": "Path to folder containing images to categorize",
                            },
                            "learn_new_faces": {
                                "type": "boolean",
                                "default": True,
                                "description": "Learn and create new person categories",
                            },
                            "min_confidence": {
                                "type": "number",
                                "default": 0.8,
                                "description": "Minimum confidence for person identification",
                            },
                        },
                        "required": ["source_folder"],
                    },
                ),
                types.Tool(
                    name="get_statistics",
                    description="Get scraping and categorization statistics",
                    inputSchema={"type": "object", "properties": {}, "required": []},
                ),
                types.Tool(
                    name="check_legal_compliance",
                    description="Check legal compliance for a website (robots.txt, ToS analysis)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "Website URL to check",
                            },
                            "check_robots": {
                                "type": "boolean",
                                "default": True,
                                "description": "Check robots.txt compliance",
                            },
                            "analyze_tos": {
                                "type": "boolean",
                                "default": True,
                                "description": "Analyze terms of service",
                            },
                        },
                        "required": ["url"],
                    },
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
                                "description": "Include thumbnail previews",
                            }
                        },
                        "required": [],
                    },
                ),
                types.Tool(
                    name="intelligent_research",
                    description="Use Jina AI to automatically discover URLs and generate keywords for scraping",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "Research topic (e.g., 'celebrity photos', 'model portfolio')",
                            },
                            "context": {
                                "type": "object",
                                "default": {},
                                "description": "Additional context like style, category, etc.",
                            },
                            "max_keywords": {
                                "type": "integer",
                                "default": 5,
                                "description": "Maximum keywords to generate",
                            },
                            "urls_per_keyword": {
                                "type": "integer",
                                "default": 5,
                                "description": "URLs to find per keyword",
                            },
                            "filter_criteria": {
                                "type": "object",
                                "default": {},
                                "description": "Filtering criteria for discovered URLs",
                            },
                        },
                        "required": ["topic"],
                    },
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
                                "description": "Run immediate proxy health check",
                            }
                        },
                        "required": [],
                    },
                ),
                types.Tool(
                    name="rft_process_images",
                    description="Process scraped images for RFT (Reinforcement Fine-tuning) training pipeline",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "image_paths": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Paths to images to process for RFT training",
                            },
                            "context": {
                                "type": "object",
                                "default": {},
                                "description": "Context information about the images (source, category, etc.)",
                            },
                            "user_id": {
                                "type": "string",
                                "default": "mcp-scraper",
                                "description": "User ID for tracking",
                            },
                        },
                        "required": ["image_paths"],
                    },
                ),
                types.Tool(
                    name="rft_create_reward",
                    description="Create reward feedback for RFT training responses",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "response_id": {
                                "type": "string",
                                "description": "ID of the response to reward",
                            },
                            "feedback": {
                                "type": "object",
                                "description": "Human feedback object with type, quality, comments",
                            },
                        },
                        "required": ["response_id", "feedback"],
                    },
                ),
                types.Tool(
                    name="rft_get_statistics",
                    description="Get comprehensive RFT training statistics and progress",
                    inputSchema={"type": "object", "properties": {}, "required": []},
                ),
                types.Tool(
                    name="rft_manage_checkpoints",
                    description="Manage RFT model checkpoints (create, activate, list)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["create", "activate", "list", "get_active"],
                                "description": "Action to perform on checkpoints",
                            },
                            "checkpoint_data": {
                                "type": "object",
                                "description": "Data for checkpoint creation (version, storage_key, etc.)",
                            },
                            "checkpoint_id": {
                                "type": "string",
                                "description": "ID of checkpoint to activate",
                            },
                        },
                        "required": ["action"],
                    },
                ),
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
            elif name == "rft_process_images":
                return await self.handle_rft_process_images(arguments or {})
            elif name == "rft_create_reward":
                return await self.handle_rft_create_reward(arguments or {})
            elif name == "rft_get_statistics":
                return await self.handle_rft_get_statistics(arguments or {})
            elif name == "rft_manage_checkpoints":
                return await self.handle_rft_manage_checkpoints(arguments or {})
            else:
                raise ValueError(f"Unknown tool: {name}")

    async def handle_scrape_website(self, arguments: Dict) -> List[types.TextContent]:
        """Handle website scraping request"""
        try:
            url = arguments.get("url", "")
            max_images = arguments.get("max_images", 50)
            category = arguments.get("category", "general")
            check_legal = arguments.get("check_legal", True)

            if not url:
                return [
                    types.TextContent(type="text", text="❌ Error: URL is required")
                ]

            result_text = f"🔍 Scraping Website: {url}\n"
            result_text += f"📊 Max Images: {max_images}\n"
            result_text += f"🏷️ Category: {category}\n\n"

            # Choose appropriate scraper
            scraper = None
            if "pornpics.com" in url.lower():
                scraper = self.scrapers.get("pornpics")
                if not scraper:
                    result_text += "⚠️ PornPics scraper not enabled in config\n"
                    scraper = self.scrapers.get("generic")
            else:
                scraper = self.scrapers.get("generic")

            if not scraper:
                return [
                    types.TextContent(
                        type="text", text="❌ Error: No suitable scraper available"
                    )
                ]

            # Legal compliance check if requested
            if check_legal:
                result_text += "⚖️ Legal Compliance Check:\n"
                compliance = await self.check_website_compliance(url)
                result_text += f"  🤖 Robots.txt: {'✅ Allowed' if compliance['robots_ok'] else '❌ Blocked'}\n"
                result_text += f"  📋 Terms Check: {compliance['tos_status']}\n\n"

                if not compliance["robots_ok"]:
                    result_text += "❌ Cannot proceed - robots.txt blocks access\n"
                    result_text += (
                        "💡 Consider using official APIs or contact website owner\n"
                    )
                    return [types.TextContent(type="text", text=result_text)]

            # Perform scraping
            result_text += "🚀 Starting scraping...\n"
            scraping_result = await scraper.scrape_url(url, max_images)

            if scraping_result["status"] == "success":
                images = scraping_result["images"]
                result_text += f"✅ Scraping completed successfully!\n"
                result_text += f"📊 Found {scraping_result.get('total_images_found', 0)} total images\n"
                result_text += f"� Filtered to {scraping_result.get('filtered_images', 0)} quality images\n"
                result_text += f"📥 Selected {len(images)} images for download\n"

                if "title" in scraping_result:
                    result_text += f"📄 Page Title: {scraping_result['title']}\n"
                if "model_name" in scraping_result:
                    result_text += f"👤 Model: {scraping_result['model_name']}\n"
                if "tags" in scraping_result:
                    tags = scraping_result["tags"][:5]  # Show first 5 tags
                    result_text += f"🏷️ Tags: {', '.join(tags)}\n"

                # Download images using professional downloader
                result_text += "\n📥 Starting image downloads...\n"

                try:
                    from downloaders.image_downloader import (
                        download_images_from_scraping_result,
                    )

                    download_result = await download_images_from_scraping_result(
                        scraping_result, self.config, category
                    )

                    if download_result["status"] == "success":
                        downloaded = download_result.get("downloaded", [])
                        failed = download_result.get("failed", [])
                        skipped = download_result.get("skipped", [])

                        result_text += f"✅ Download completed!\n"
                        result_text += f"📥 Downloaded: {len(downloaded)} images\n"
                        result_text += f"⏭️ Skipped: {len(skipped)} duplicates\n"
                        result_text += f"❌ Failed: {len(failed)} images\n"

                        if downloaded:
                            total_size_mb = sum(
                                img.get("file_size", 0) for img in downloaded
                            ) / (1024 * 1024)
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
                    result_text += (
                        "📝 Will save to: "
                        + self.config["storage"]["raw_path"]
                        + f"/{category}/\n"
                    )
                    result_text += (
                        "🔧 Run: pip install aiohttp to enable professional downloads\n"
                    )

                # Update statistics
                self.stats["total_scraped"] += len(images)

                # Integrate with RFT if available
                if self.rft_manager and images:
                    result_text += "\n🤖 RFT Integration:\n"
                    try:
                        # Prepare scraping result for RFT
                        scraping_result = {
                            "url": url,
                            "images": [
                                {"local_path": img.get("local_path")}
                                for img in images
                                if img.get("local_path")
                            ],
                            "category": category,
                            "timestamp": time.time(),
                            "user_id": "mcp-scraper",
                            "avg_quality_score": scraping_result.get(
                                "avg_quality_score", 0.7
                            ),
                        }

                        # Integrate with RFT pipeline
                        rft_result = await self.rft_manager.integrate_scraping_session(
                            scraping_result
                        )

                        if rft_result.get("success"):
                            summary = rft_result.get("summary", {})
                            result_text += f"✅ RFT integration completed!\n"
                            result_text += (
                                f"📊 Session ID: {rft_result.get('session_id')}\n"
                            )
                            result_text += f"📥 Images processed: {summary.get('processed_images', 0)}\n"
                            result_text += f"📝 Training responses: {summary.get('responses_created', 0)}\n"
                            result_text += f"🚀 Ready for training: {'Yes' if summary.get('ready_for_training') else 'No'}\n"

                            # Update RFT stats
                            self.stats["rft_sessions"] += 1
                            self.stats["rft_responses"] += summary.get(
                                "responses_created", 0
                            )
                        else:
                            result_text += (
                                f"⚠️ RFT integration failed: {rft_result.get('error')}\n"
                            )

                    except Exception as e:
                        result_text += f"⚠️ RFT integration error: {str(e)}\n"
                        logger.warning(f"RFT integration failed: {e}")

            elif scraping_result["status"] == "blocked":
                result_text += f"❌ Scraping blocked: {scraping_result['message']}\n"

            else:
                result_text += f"❌ Scraping failed: {scraping_result['message']}\n"

            return [types.TextContent(type="text", text=result_text)]

        except Exception as e:
            logger.error(f"Error in scrape_website: {e}")
            return [
                types.TextContent(
                    type="text", text=f"❌ Error scraping website: {str(e)}"
                )
            ]

    async def handle_categorize_images(
        self, arguments: Dict
    ) -> List[types.TextContent]:
        """Handle image categorization request"""
        try:
            source_folder = arguments.get("source_folder", "")
            learn_new_faces = arguments.get("learn_new_faces", True)
            min_confidence = arguments.get("min_confidence", 0.8)

            if not source_folder:
                return [
                    types.TextContent(
                        type="text", text="❌ Error: source_folder is required"
                    )
                ]

            folder_path = Path(source_folder)
            if not folder_path.exists():
                return [
                    types.TextContent(
                        type="text", text=f"❌ Error: Folder not found: {source_folder}"
                    )
                ]

            result_text = f"🤖 Categorizing Images from: {source_folder}\n"
            result_text += f"📊 Learn New Faces: {'Yes' if learn_new_faces else 'No'}\n"
            result_text += f"🎯 Min Confidence: {min_confidence}\n\n"

            # Count images
            image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
            image_files = [
                f for f in folder_path.iterdir() if f.suffix.lower() in image_extensions
            ]

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
            return [
                types.TextContent(
                    type="text", text=f"❌ Error categorizing images: {str(e)}"
                )
            ]

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
            result_text += (
                f"  • Persons Identified: {self.stats['total_persons_identified']}\n\n"
            )

            # Directory stats
            result_text += "📁 Directory Information:\n"

            storage_config = self.config["storage"]
            for folder_type, folder_path in storage_config.items():
                if folder_type.endswith("_path"):
                    path = Path(folder_path)
                    if path.exists():
                        file_count = len(list(path.rglob("*")))
                        result_text += f"  • {folder_type}: {file_count} files\n"
                    else:
                        result_text += f"  • {folder_type}: Not created yet\n"

            result_text += "\n🔧 Configuration:\n"
            result_text += f"  • Face Detection Threshold: {self.config['face_detection']['face_threshold']}\n"
            result_text += f"  • Min Confidence: {self.config['categorization']['min_confidence']}\n"
            result_text += (
                f"  • Legal Checks: {self.config['legal']['require_robots_check']}\n"
            )

            return [types.TextContent(type="text", text=result_text)]

        except Exception as e:
            logger.error(f"Error in get_statistics: {e}")
            return [
                types.TextContent(
                    type="text", text=f"❌ Error getting statistics: {str(e)}"
                )
            ]

    async def handle_check_legal_compliance(
        self, arguments: Dict
    ) -> List[types.TextContent]:
        """Handle legal compliance check"""
        try:
            url = arguments.get("url", "")
            check_robots = arguments.get("check_robots", True)
            analyze_tos = arguments.get("analyze_tos", True)

            if not url:
                return [
                    types.TextContent(type="text", text="❌ Error: URL is required")
                ]

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
            return [
                types.TextContent(
                    type="text", text=f"❌ Error checking legal compliance: {str(e)}"
                )
            ]

    async def handle_list_categories(self, arguments: Dict) -> List[types.TextContent]:
        """Handle list categories request"""
        try:
            include_thumbnails = arguments.get("include_thumbnails", False)

            result_text = "📁 Person Categories\n"
            result_text += "=" * 30 + "\n\n"

            categorized_path = Path(self.config["storage"]["categorized_path"])

            if not categorized_path.exists():
                result_text += "📂 No categories found yet.\n"
                result_text += (
                    "💡 Run 'categorize_images' first to create person categories.\n"
                )
                return [types.TextContent(type="text", text=result_text)]

            # List person directories
            person_dirs = [d for d in categorized_path.iterdir() if d.is_dir()]

            if not person_dirs:
                result_text += "📂 No person categories found.\n"
            else:
                result_text += f"👥 Found {len(person_dirs)} person categories:\n\n"

                for i, person_dir in enumerate(person_dirs, 1):
                    # Count images in directory
                    image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
                    image_files = [
                        f
                        for f in person_dir.iterdir()
                        if f.suffix.lower() in image_extensions
                    ]

                    result_text += f"{i}. 👤 {person_dir.name}\n"
                    result_text += f"   📊 Images: {len(image_files)}\n"

                    # Show sample files
                    if image_files:
                        result_text += "   📋 Sample files:\n"
                        for img_file in image_files[:3]:
                            result_text += f"      • {img_file.name}\n"
                        if len(image_files) > 3:
                            result_text += (
                                f"      ... and {len(image_files) - 3} more\n"
                            )
                    result_text += "\n"

            if include_thumbnails:
                result_text += "🖼️ Thumbnail generation coming soon!\n"

            return [types.TextContent(type="text", text=result_text)]

        except Exception as e:
            logger.error(f"Error in list_categories: {e}")
            return [
                types.TextContent(
                    type="text", text=f"❌ Error listing categories: {str(e)}"
                )
            ]

    async def handle_intelligent_research(
        self, arguments: Dict
    ) -> List[types.TextContent]:
        """Handle intelligent research using Jina AI"""
        try:
            if not JINA_AVAILABLE:
                return [
                    types.TextContent(
                        type="text",
                        text="❌ Error: Jina AI integration not available.\n"
                        + "Install required packages: pip install aiohttp",
                    )
                ]

            topic = arguments.get("topic", "")
            context = arguments.get("context", {})
            max_keywords = arguments.get("max_keywords", 5)
            urls_per_keyword = arguments.get("urls_per_keyword", 5)
            filter_criteria = arguments.get("filter_criteria", {})

            # Get API key from environment variable
            jina_api_key = os.getenv("JINA_API_KEY")

            if not topic:
                return [
                    types.TextContent(
                        type="text", text="❌ Error: Research topic is required"
                    )
                ]

            if not jina_api_key:
                return [
                    types.TextContent(
                        type="text",
                        text="❌ Error: Jina API key not configured. Set JINA_API_KEY environment variable.",
                    )
                ]

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
                "max_targets": filter_criteria.get("max_targets", 20),
            }

            result_text += "🚀 Starting intelligent research...\n\n"

            # Run auto discovery
            discovery_result = await jina_integration.auto_discover_scraping_targets(
                research_request
            )

            if discovery_result["status"] == "success":
                research_results = discovery_result["research_results"]
                targets = discovery_result["filtered_targets"]
                plan = discovery_result["scraping_plan"]

                # Display research summary
                result_text += f"✅ Research completed successfully!\n"
                result_text += (
                    f"📊 Keywords generated: {research_results['keywords_generated']}\n"
                )
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
                        for site_type, count in summary[
                            "site_type_distribution"
                        ].items():
                            result_text += f"    - {site_type}: {count}\n"

                    # Priority distribution
                    if summary.get("priority_distribution"):
                        priority_dist = summary["priority_distribution"]
                        result_text += f"  • Priority Distribution:\n"
                        result_text += f"    - High: {priority_dist.get('high', 0)}\n"
                        result_text += (
                            f"    - Medium: {priority_dist.get('medium', 0)}\n"
                        )
                        result_text += f"    - Low: {priority_dist.get('low', 0)}\n"

                    result_text += "\n"

                # Show top targets
                if targets:
                    result_text += f"🎯 Top Scraping Targets:\n"
                    for i, target in enumerate(targets[:5], 1):
                        result_text += f"{i}. {target['domain']}\n"
                        result_text += f"   🔗 URL: {target['url'][:60]}{'...' if len(target['url']) > 60 else ''}\n"
                        result_text += f"   ⭐ Priority: {target.get('scraping_priority', 0)}/100\n"
                        result_text += (
                            f"   🏷️ Type: {target.get('site_type', 'unknown')}\n"
                        )
                        result_text += f"   ⚖️ Legal: {target.get('legal_considerations', {}).get('risk_level', 'unknown')} risk\n"
                        result_text += "\n"

                # Show scraping plan
                if plan:
                    result_text += f"📋 Scraping Plan:\n"
                    result_text += f"  • Total Targets: {plan['total_targets']}\n"
                    result_text += (
                        f"  • Estimated Time: {plan['estimated_time']//60} minutes\n"
                    )
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
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Error in intelligent research: {str(e)}\n"
                    + f"🔧 Make sure Jina AI integration is properly configured",
                )
            ]

    async def handle_proxy_status(self, arguments: Dict) -> List[types.TextContent]:
        """Handle proxy status check request"""
        try:
            run_health_check = arguments.get("run_health_check", False)

            result_text = "🌐 Proxy System Status\n"
            result_text += "=" * 30 + "\n\n"

            # Check if scrapers have proxy stats
            proxy_stats_found = False

            for scraper_name, scraper in self.scrapers.items():
                if scraper and hasattr(scraper, "get_proxy_stats"):
                    stats = scraper.get_proxy_stats()
                    if stats:
                        proxy_stats_found = True
                        result_text += (
                            f"📊 {scraper_name.capitalize()} Scraper Proxies:\n"
                        )
                        result_text += f"  • Total Proxies: {stats['total_proxies']}\n"
                        result_text += f"  • Healthy: {stats['healthy_proxies']}\n"
                        result_text += (
                            f"  • Unhealthy: {stats['unhealthy_proxies']}\n\n"
                        )

                        # Show individual proxy stats
                        result_text += f"🔍 Proxy Details:\n"
                        for proxy in stats["proxies"][:5]:  # Show first 5
                            health_status = "✅" if proxy["is_healthy"] else "❌"
                            result_text += (
                                f"  {health_status} {proxy['ip']}:{proxy['port']}\n"
                            )
                            result_text += (
                                f"     Success Rate: {proxy['success_rate']:.2%}\n"
                            )
                            result_text += (
                                f"     Response Time: {proxy['response_time']:.2f}s\n"
                            )
                            result_text += f"     Requests: {proxy['success_count']} ✅ / {proxy['failure_count']} ❌\n"

                        if len(stats["proxies"]) > 5:
                            result_text += (
                                f"  ... and {len(stats['proxies']) - 5} more proxies\n"
                            )
                        result_text += "\n"

            if not proxy_stats_found:
                result_text += "❌ No proxy system found\n"
                result_text += (
                    "💡 Proxies are not configured or scrapers not initialized\n"
                )

                # Check configuration
                proxy_config = self.config.get("proxy_config", {})
                if proxy_config.get("webshare_proxies"):
                    result_text += f"📋 Configuration found: {len(proxy_config['webshare_proxies'])} proxies configured\n"
                    result_text += (
                        "🔧 Proxies should be initialized when scraping starts\n"
                    )
                else:
                    result_text += "⚠️ No proxy configuration found in config\n"
                    result_text += (
                        "💡 Add proxy_config section to enable proxy rotation\n"
                    )

            if run_health_check and proxy_stats_found:
                result_text += "🔄 Running proxy health check...\n"
                result_text += "(Health checks run automatically in background)\n"

            # Show configuration if available
            proxy_config = self.config.get("proxy_config", {})
            if proxy_config:
                result_text += "⚙️ Proxy Configuration:\n"
                settings = proxy_config.get("settings", {})
                result_text += f"  • Health Check Interval: {settings.get('health_check_interval', 300)}s\n"
                result_text += f"  • Max Retries: {settings.get('max_retries', 3)}\n"
                result_text += (
                    f"  • Request Timeout: {settings.get('request_timeout', 30)}s\n"
                )
                result_text += (
                    f"  • Rate Limit Delay: {settings.get('rate_limit_delay', 1)}s\n"
                )

            return [types.TextContent(type="text", text=result_text)]

        except Exception as e:
            logger.error(f"Error in proxy_status: {e}")
            return [
                types.TextContent(
                    type="text", text=f"❌ Error checking proxy status: {str(e)}"
                )
            ]

    async def handle_rft_process_images(
        self, arguments: Dict
    ) -> List[types.TextContent]:
        """Handle RFT image processing request"""
        try:
            if not RFT_AVAILABLE or not self.rft_manager:
                return [
                    types.TextContent(
                        type="text",
                        text="❌ Error: RFT integration not available.\n"
                        + "Install required packages: pip install aiohttp",
                    )
                ]

            image_paths = arguments.get("image_paths", [])
            context = arguments.get("context", {})
            user_id = arguments.get("user_id", "mcp-scraper")

            if not image_paths:
                return [
                    types.TextContent(
                        type="text", text="❌ Error: No image paths provided"
                    )
                ]

            result_text = f"🤖 RFT Image Processing\n"
            result_text += "=" * 40 + "\n\n"
            result_text += f"📊 Processing {len(image_paths)} images\n"
            result_text += f"👤 User ID: {user_id}\n"
            result_text += f"📋 Context: {context}\n\n"

            # Process images for RFT
            processing_result = await self.rft_manager.processor.process_scraped_images(
                image_paths, context
            )

            if processing_result:
                result_text += f"✅ Processing completed!\n"
                result_text += (
                    f"📥 Processed: {len(processing_result['processed'])} images\n"
                )
                result_text += f"❌ Failed: {len(processing_result['failed'])} images\n"
                result_text += f"🆔 Session ID: {processing_result['session_id']}\n\n"

                # Create training data
                if processing_result["processed"]:
                    result_text += "🧠 Creating training data...\n"
                    training_result = (
                        await self.rft_manager.processor.create_rft_training_data(
                            processing_result["processed"]
                        )
                    )

                    result_text += f"📝 Responses created: {len(training_result['responses_created'])}\n"
                    result_text += (
                        f"❌ Training data failed: {len(training_result['failed'])}\n\n"
                    )

                    # Update stats
                    self.stats["rft_sessions"] += 1
                    self.stats["rft_responses"] += len(
                        training_result["responses_created"]
                    )

                # Show sample results
                if processing_result["processed"][:3]:
                    result_text += "📋 Sample processed images:\n"
                    for i, img in enumerate(processing_result["processed"][:3], 1):
                        result_text += f"  {i}. {Path(img['image_path']).name}\n"
                        result_text += f"     🔗 URL: {img['url']}\n"
                        result_text += f"     🆔 ID: {img['image_id']}\n"

                if processing_result["failed"]:
                    result_text += f"\n⚠️ Failed images:\n"
                    for fail in processing_result["failed"][:3]:
                        result_text += (
                            f"  • {Path(fail['image_path']).name}: {fail['error']}\n"
                        )

            else:
                result_text += "❌ Processing failed\n"

            return [types.TextContent(type="text", text=result_text)]

        except Exception as e:
            logger.error(f"Error in rft_process_images: {e}")
            return [
                types.TextContent(
                    type="text", text=f"❌ Error processing images for RFT: {str(e)}"
                )
            ]

    async def handle_rft_create_reward(
        self, arguments: Dict
    ) -> List[types.TextContent]:
        """Handle RFT reward creation request"""
        try:
            if not RFT_AVAILABLE or not self.rft_manager:
                return [
                    types.TextContent(
                        type="text",
                        text="❌ Error: RFT integration not available.\n"
                        + "Install required packages: pip install aiohttp",
                    )
                ]

            response_id = arguments.get("response_id", "")
            feedback = arguments.get("feedback", {})

            if not response_id or not feedback:
                return [
                    types.TextContent(
                        type="text",
                        text="❌ Error: response_id and feedback are required",
                    )
                ]

            result_text = f"🎯 Creating RFT Reward\n"
            result_text += "=" * 30 + "\n\n"
            result_text += f"📝 Response ID: {response_id}\n"
            result_text += f"💭 Feedback Type: {feedback.get('type', 'unknown')}\n"
            result_text += (
                f"⭐ Quality Rating: {feedback.get('quality', 'not specified')}\n\n"
            )

            # Create reward
            reward_result = await self.rft_manager.create_reward_feedback(
                response_id, feedback
            )

            if reward_result.get("success"):
                reward_data = reward_result.get("data", {})
                result_text += f"✅ Reward created successfully!\n"
                result_text += f"🆔 Reward ID: {reward_data.get('id')}\n"
                result_text += f"📊 Score: {reward_data.get('score')}\n"
                result_text += f"📝 Details: {reward_data.get('detail', 'None')}\n"
            else:
                result_text += (
                    f"❌ Failed to create reward: {reward_result.get('error')}\n"
                )

            return [types.TextContent(type="text", text=result_text)]

        except Exception as e:
            logger.error(f"Error in rft_create_reward: {e}")
            return [
                types.TextContent(
                    type="text", text=f"❌ Error creating RFT reward: {str(e)}"
                )
            ]

    async def handle_rft_get_statistics(
        self, arguments: Dict
    ) -> List[types.TextContent]:
        """Handle RFT statistics request"""
        try:
            if not RFT_AVAILABLE or not self.rft_manager:
                return [
                    types.TextContent(
                        type="text",
                        text="❌ Error: RFT integration not available.\n"
                        + "Install required packages: pip install aiohttp",
                    )
                ]

            result_text = f"📊 RFT Training Statistics\n"
            result_text += "=" * 40 + "\n\n"

            # Get comprehensive statistics
            stats = await self.rft_manager.get_training_statistics()

            # Display response statistics
            responses = stats.get("responses", {})
            result_text += f"📝 Responses:\n"
            result_text += f"  • Total: {responses.get('total', 0)}\n"
            result_text += f"  • Recent 24h: {responses.get('recent_24h', 0)}\n"

            by_model = responses.get("by_model", {})
            if by_model:
                result_text += f"  • By Model:\n"
                for model, count in by_model.items():
                    result_text += f"    - {model}: {count}\n"

            # Display reward statistics
            rewards = stats.get("rewards", {})
            result_text += f"\n🎯 Rewards:\n"
            result_text += f"  • Total: {rewards.get('total', 0)}\n"
            result_text += f"  • Average Score: {rewards.get('avg_score', 0):.3f}\n"

            distribution = rewards.get("distribution", {})
            if distribution:
                result_text += f"  • Distribution:\n"
                result_text += f"    - Positive: {distribution.get('positive', 0)}\n"
                result_text += f"    - Negative: {distribution.get('negative', 0)}\n"
                result_text += f"    - Neutral: {distribution.get('neutral', 0)}\n"

            # Display checkpoint statistics
            checkpoints = stats.get("checkpoints", {})
            result_text += f"\n💾 Checkpoints:\n"
            result_text += f"  • Total: {checkpoints.get('total', 0)}\n"
            result_text += f"  • Active: {checkpoints.get('active', 'None')}\n"
            result_text += (
                f"  • Best Performance: {checkpoints.get('best_performance', 0):.3f}\n"
            )

            versions = checkpoints.get("versions", [])
            if versions:
                result_text += f"  • Versions: {', '.join(versions)}\n"

            # Display training readiness
            readiness = stats.get("training_readiness", {})
            result_text += f"\n🚀 Training Readiness:\n"
            status = readiness.get("status", "unknown")
            status_emoji = {
                "ready": "✅",
                "partial": "⚠️",
                "insufficient_data": "❌",
            }.get(status, "❓")
            result_text += f"  • Status: {status_emoji} {status.title()}\n"

            recommendations = readiness.get("recommendations", [])
            if recommendations:
                result_text += f"  • Recommendations:\n"
                for rec in recommendations:
                    result_text += f"    - {rec}\n"

            # Display session statistics
            result_text += f"\n📈 Session Stats:\n"
            result_text += f"  • RFT Sessions: {self.stats.get('rft_sessions', 0)}\n"
            result_text += f"  • RFT Responses: {self.stats.get('rft_responses', 0)}\n"

            return [types.TextContent(type="text", text=result_text)]

        except Exception as e:
            logger.error(f"Error in rft_get_statistics: {e}")
            return [
                types.TextContent(
                    type="text", text=f"❌ Error getting RFT statistics: {str(e)}"
                )
            ]

    async def handle_rft_manage_checkpoints(
        self, arguments: Dict
    ) -> List[types.TextContent]:
        """Handle RFT checkpoint management request"""
        try:
            if not RFT_AVAILABLE or not self.rft_client:
                return [
                    types.TextContent(
                        type="text",
                        text="❌ Error: RFT integration not available.\n"
                        + "Install required packages: pip install aiohttp",
                    )
                ]

            action = arguments.get("action", "")
            checkpoint_data = arguments.get("checkpoint_data", {})
            checkpoint_id = arguments.get("checkpoint_id", "")

            result_text = f"💾 RFT Checkpoint Management\n"
            result_text += "=" * 35 + "\n\n"
            result_text += f"🔧 Action: {action}\n\n"

            if action == "create":
                if not checkpoint_data.get("version") or not checkpoint_data.get(
                    "storage_key"
                ):
                    return [
                        types.TextContent(
                            type="text",
                            text="❌ Error: version and storage_key required for checkpoint creation",
                        )
                    ]

                result = await self.rft_client.create_checkpoint(**checkpoint_data)

                if result.get("success"):
                    data = result.get("data", {})
                    result_text += f"✅ Checkpoint created successfully!\n"
                    result_text += f"🆔 ID: {data.get('id')}\n"
                    result_text += f"📌 Version: {data.get('version')}\n"
                    result_text += f"🔑 Storage Key: {data.get('storage_key')}\n"
                    result_text += f"📊 Epoch: {data.get('epoch', 0)}\n"
                    result_text += f"⭐ Avg Reward: {data.get('avg_reward', 0):.3f}\n"
                    result_text += (
                        f"🟢 Active: {'Yes' if data.get('is_active') else 'No'}\n"
                    )
                else:
                    result_text += (
                        f"❌ Failed to create checkpoint: {result.get('error')}\n"
                    )

            elif action == "activate":
                if not checkpoint_id:
                    return [
                        types.TextContent(
                            type="text",
                            text="❌ Error: checkpoint_id required for activation",
                        )
                    ]

                result = await self.rft_client.activate_checkpoint(checkpoint_id)

                if result.get("success"):
                    result_text += f"✅ Checkpoint activated successfully!\n"
                    result_text += f"🆔 Activated ID: {checkpoint_id}\n"
                    result_text += f"ℹ️ All other checkpoints have been deactivated\n"
                else:
                    result_text += (
                        f"❌ Failed to activate checkpoint: {result.get('error')}\n"
                    )

            elif action == "list":
                result = await self.rft_client.get_checkpoints(limit=20)

                if result.get("success"):
                    checkpoints = result.get("data", [])
                    stats = result.get("stats", {})

                    result_text += f"📋 Checkpoint List ({len(checkpoints)} total):\n\n"

                    if not checkpoints:
                        result_text += "📭 No checkpoints found\n"
                    else:
                        for i, checkpoint in enumerate(checkpoints, 1):
                            status = (
                                "🟢 Active"
                                if checkpoint.get("is_active")
                                else "⚪ Inactive"
                            )
                            result_text += (
                                f"{i}. 📌 {checkpoint.get('version')} - {status}\n"
                            )
                            result_text += f"   🆔 ID: {checkpoint.get('id')}\n"
                            result_text += (
                                f"   🔑 Storage: {checkpoint.get('storage_key')}\n"
                            )
                            result_text += (
                                f"   📊 Epoch: {checkpoint.get('epoch', 0)}\n"
                            )
                            result_text += (
                                f"   ⭐ Reward: {checkpoint.get('avg_reward', 0):.3f}\n"
                            )
                            result_text += f"   📅 Created: {checkpoint.get('created_at', 'Unknown')[:19]}\n\n"

                    # Show statistics
                    result_text += f"📊 Statistics:\n"
                    result_text += f"  • Total: {stats.get('total_checkpoints', 0)}\n"
                    result_text += f"  • Active: {stats.get('active_checkpoints', 0)}\n"
                    result_text += f"  • Latest Epoch: {stats.get('latest_epoch', 0)}\n"
                    result_text += (
                        f"  • Best Reward: {stats.get('best_avg_reward', 0):.3f}\n"
                    )

                else:
                    result_text += (
                        f"❌ Failed to list checkpoints: {result.get('error')}\n"
                    )

            elif action == "get_active":
                result = await self.rft_client.get_active_checkpoint()

                if result.get("success"):
                    data = result.get("data", {})
                    result_text += f"🟢 Active Checkpoint:\n"
                    result_text += f"🆔 ID: {data.get('id')}\n"
                    result_text += f"📌 Version: {data.get('version')}\n"
                    result_text += f"🔑 Storage Key: {data.get('storage_key')}\n"
                    result_text += f"📊 Epoch: {data.get('epoch', 0)}\n"
                    result_text += f"⭐ Avg Reward: {data.get('avg_reward', 0):.3f}\n"
                    result_text += (
                        f"📅 Created: {data.get('created_at', 'Unknown')[:19]}\n"
                    )
                else:
                    result_text += f"❌ No active checkpoint found\n"

            else:
                result_text += f"❌ Unknown action: {action}\n"
                result_text += (
                    f"💡 Available actions: create, activate, list, get_active\n"
                )

            return [types.TextContent(type="text", text=result_text)]

        except Exception as e:
            logger.error(f"Error in rft_manage_checkpoints: {e}")
            return [
                types.TextContent(
                    type="text", text=f"❌ Error managing RFT checkpoints: {str(e)}"
                )
            ]

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

                user_agent = self.config["legal"]["user_agent"]
                robots_ok = rp.can_fetch(user_agent, url)
                robots_details = f"Checked with user-agent: {user_agent}"

            except Exception as e:
                robots_ok = False
                robots_details = f"Error checking robots.txt: {str(e)}"

            # Basic ToS analysis (simplified)
            domain = parsed_url.netloc.lower()
            tos_analysis = self.analyze_domain_tos(domain)

            return {
                "robots_ok": robots_ok,
                "robots_details": robots_details,
                "tos_status": tos_analysis["status"],
                "recommendation": tos_analysis["recommendation"],
            }

        except Exception as e:
            return {
                "robots_ok": False,
                "robots_details": f"Error: {str(e)}",
                "tos_status": "Unknown",
                "recommendation": "Manual review required",
            }

    def analyze_domain_tos(self, domain: str) -> Dict[str, str]:
        """Analyze domain Terms of Service (simplified)"""

        # Known problematic domains
        restricted_domains = {
            "instagram.com": {
                "status": "❌ Restricted",
                "recommendation": "Use Instagram Basic Display API instead",
            },
            "facebook.com": {
                "status": "❌ Restricted",
                "recommendation": "Use Facebook Graph API instead",
            },
            "twitter.com": {
                "status": "❌ Restricted",
                "recommendation": "Use Twitter API instead",
            },
            "x.com": {
                "status": "❌ Restricted",
                "recommendation": "Use Twitter API instead",
            },
        }

        # Check for known restrictions
        for restricted_domain, info in restricted_domains.items():
            if restricted_domain in domain:
                return info

        # Default analysis for other domains
        return {
            "status": "⚠️ Requires Review",
            "recommendation": "Manually review ToS and consider contacting website owner",
        }


async def main():
    """Main server entry point"""
    # Load configuration
    config_path = Path(__file__).parent / "config" / "mcp_config.json"
    proxy_config_path = Path(__file__).parent / "config" / "proxy_config.json"

    # Load main configuration with environment variable substitution
    try:
        config = load_config_with_env_vars(str(config_path))
        logger.info(f"Loaded configuration from: {config_path}")
    except Exception as e:
        logger.error(f"Failed to load configuration from {config_path}: {e}")
        logger.info("Using minimal default configuration")

        # Use minimal default config
        config = {
            "storage": {
                "base_path": "./data",
                "raw_path": "./data/raw",
                "processed_path": "./data/processed",
                "categorized_path": "./data/categorized",
                "metadata_path": "./data/metadata",
            },
            "face_detection": {"face_threshold": 0.6},
            "categorization": {"min_confidence": 0.8},
            "legal": {"require_robots_check": True, "user_agent": "MCP-WebScraper/1.0"},
        }

    # Load proxy configuration if available
    try:
        with open(proxy_config_path, "r") as f:
            proxy_config = json.load(f)
            config.update(proxy_config)
            logger.info(
                f"Loaded proxy configuration with {len(proxy_config.get('proxy_config', {}).get('webshare_proxies', []))} proxies"
            )
    except FileNotFoundError:
        logger.warning(f"Proxy configuration file not found: {proxy_config_path}")
        logger.info("Proxy functionality will not be available")

    # Create and run server
    server_instance = WebScraperMCPServer(config)

    logger.info("Starting MCP Web Scraper Server...")

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
