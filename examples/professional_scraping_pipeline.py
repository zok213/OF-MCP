#!/usr/bin/env python3
"""
Adult Content AI-Driven Web Scraping with Proxy Rotation
Demonstrates complete integration of proxy management, AI research, and adult content scraping

This example shows how to:
1. Initialize proxy rotation system for adult content sites
2. Use AI-driven URL discovery for NSFW content
3. Perform adult content web scraping with proxy rotation
4. Handle adult site errors and failover scenarios
5. Monitor proxy health and performance for adult sites

IMPORTANT: This is for educational/research purposes only.
Always respect website ToS, robots.txt, and applicable laws.
Adult content scraping - ensure compliance with local laws and age verification.
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AdultContentScrapingPipeline:
    """Complete AI-driven adult content scraping pipeline with proxy rotation"""

    def __init__(self, config_path: str = "config/proxy_config.json"):
        """Initialize the adult content scraping pipeline"""
        self.config = self.load_config(config_path)
        self.proxy_rotator = None
        self.scrapers = {}

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_path}")
            return self.get_default_config()

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "proxy_config": {
                "webshare_proxies": [
                    "23.95.150.145:6114:hmtdviqy:oipyyzu8cad4",
                    "198.23.239.134:6540:hmtdviqy:oipyyzu8cad4",
                    "45.38.107.97:6014:hmtdviqy:oipyyzu8cad4",
                ],
                "settings": {
                    "health_check_interval": 300,
                    "max_retries": 3,
                    "request_timeout": 30,
                },
            },
            "scraper_config": {
                "delay": 1,
                "max_retries": 3,
                "respect_robots_txt": True,
            },
        }

    def initialize_proxy_system(self):
        """Initialize the proxy rotation system"""
        try:
            from src.proxy.proxy_manager import (
                create_webshare_proxy_rotator,
                ProxySession,
            )

            proxy_config = self.config["proxy_config"]
            proxies = proxy_config["webshare_proxies"]

            logger.info(f"Initializing proxy system with {len(proxies)} proxies")

            # Create proxy rotator
            self.proxy_rotator = create_webshare_proxy_rotator(proxies)

            # Create proxy session for testing
            self.proxy_session = ProxySession(
                self.proxy_rotator, max_retries=proxy_config["settings"]["max_retries"]
            )

            logger.info("✅ Proxy system initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize proxy system: {e}")
            return False

    def initialize_scrapers(self):
        """Initialize scrapers with proxy support"""
        try:
            from src.scrapers.base_scraper import GenericScraper, PornPicsScraper

            scraper_config = self.config["scraper_config"].copy()
            scraper_config["proxies"] = self.config["proxy_config"]["webshare_proxies"]

            # Initialize generic scraper
            self.scrapers["generic"] = GenericScraper(scraper_config)

            # Initialize specialized scrapers as needed
            pornpics_config = scraper_config.copy()
            pornpics_config["enabled"] = True
            self.scrapers["pornpics"] = PornPicsScraper(pornpics_config)

            logger.info("✅ Scrapers initialized with proxy support")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize scrapers: {e}")
            return False

    async def test_proxy_system(self, test_count: int = 5) -> Dict[str, Any]:
        """Test proxy system with multiple requests"""
        logger.info(f"🧪 Testing proxy system with {test_count} requests")

        test_results = {
            "successful_requests": 0,
            "failed_requests": 0,
            "proxy_usage": {},
            "average_response_time": 0.0,
            "total_test_time": 0.0,
        }

        test_url = "https://httpbin.org/ip"
        start_time = time.time()
        response_times = []

        for i in range(test_count):
            try:
                logger.info(f"Test request {i+1}/{test_count}")

                request_start = time.time()
                response = self.proxy_session.get(test_url)
                request_time = time.time() - request_start

                if response and response.status_code == 200:
                    test_results["successful_requests"] += 1
                    response_times.append(request_time)

                    # Parse IP from response to track proxy usage
                    try:
                        ip_data = response.json()
                        proxy_ip = ip_data.get("origin", "unknown")
                        test_results["proxy_usage"][proxy_ip] = (
                            test_results["proxy_usage"].get(proxy_ip, 0) + 1
                        )
                        logger.info(
                            f"✅ Request {i+1} successful via IP: {proxy_ip} ({request_time:.2f}s)"
                        )
                    except:
                        logger.info(
                            f"✅ Request {i+1} successful ({request_time:.2f}s)"
                        )
                else:
                    test_results["failed_requests"] += 1
                    logger.warning(f"❌ Request {i+1} failed")

                # Small delay between requests
                await asyncio.sleep(1)

            except Exception as e:
                test_results["failed_requests"] += 1
                logger.error(f"❌ Request {i+1} error: {e}")

        test_results["total_test_time"] = time.time() - start_time
        if response_times:
            test_results["average_response_time"] = sum(response_times) / len(
                response_times
            )

        # Log summary
        logger.info(f"📊 Test Summary:")
        logger.info(f"  ✅ Successful: {test_results['successful_requests']}")
        logger.info(f"  ❌ Failed: {test_results['failed_requests']}")
        logger.info(
            f"  ⏱️ Avg Response Time: {test_results['average_response_time']:.2f}s"
        )
        logger.info(f"  🌐 Proxies Used: {len(test_results['proxy_usage'])}")

        return test_results

    async def demonstrate_researcher_integration(self, research_topics: list):
        """
        NEW: Demonstrate integration with researcher-provided links
        Shows the complete pipeline: Research → Filter → Batch Crawl
        """
        print("\n🔬 Researcher Integration Pipeline")
        print("=" * 60)

        # Import after path setup
        import sys
        import os

        sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

        from src.research.jina_researcher import JinaResearcher
        from src.server import WebScraperMCPServer

        # Initialize components
        config_path = "config/proxy_config.json"
        config = self.load_config(config_path)

        mcp_server = WebScraperMCPServer(config)

        async with JinaResearcher(self.jina_api_key) as researcher:
            for topic in research_topics:
                print(f"\n🎯 Research Topic: {topic}")
                print("-" * 50)

                # Step 1: AI Research (existing functionality)
                print("🧠 Step 1: AI-Powered URL Discovery...")
                research_result = await researcher.intelligent_research_pipeline(
                    topic, {"style": "professional"}, max_keywords=3, urls_per_keyword=5
                )

                if research_result["status"] != "success":
                    print(f"❌ Research failed for topic: {topic}")
                    continue

                # Step 2: Convert to researcher format
                print("⚡ Step 2: Preparing URLs for Advanced Crawler...")
                researcher_urls = []

                for result in research_result["research_results"]:
                    for url_data in result["valid_urls"]:
                        researcher_url = {
                            "url": url_data["url"],
                            "priority": url_data.get("scraping_priority", 75),
                            "category": self._determine_category_from_research(
                                topic, url_data
                            ),
                            "metadata": {
                                "research_topic": topic,
                                "keyword": result.get("keyword", "unknown"),
                                "site_type": url_data.get("site_type", "unknown"),
                                "legal_risk": url_data.get(
                                    "legal_considerations", {}
                                ).get("risk_level", "unknown"),
                                "discovery_method": "jina_ai_research",
                            },
                        }
                        researcher_urls.append(researcher_url)

                print(f"✅ Prepared {len(researcher_urls)} URLs for crawling")

                # Step 3: Advanced batch crawling with new tool
                print("🕷️ Step 3: Advanced Researcher Link Crawling...")

                crawl_arguments = {
                    "researcher_urls": researcher_urls,
                    "batch_size": 4,
                    "max_images_per_url": 30,
                    "min_priority": 60,  # Lower threshold for demo
                    "enable_rft": True,
                    "filter_options": {
                        "min_quality": 0.75,
                        "prefer_high_resolution": True,
                        "exclude_duplicates": True,
                        "content_filter": "safe",
                    },
                }

                try:
                    crawl_results = await mcp_server.handle_crawl_researcher_links(
                        crawl_arguments
                    )

                    if crawl_results and len(crawl_results) > 0:
                        result_text = crawl_results[0].text
                        print("📊 Crawling Results:")
                        print("-" * 30)
                        # Print key statistics from results
                        lines = result_text.split("\n")
                        for line in lines:
                            if any(
                                keyword in line
                                for keyword in [
                                    "URLs processed:",
                                    "Total images scraped:",
                                    "Success rate:",
                                    "RFT sessions",
                                ]
                            ):
                                print(f"  {line.strip()}")

                        print("✅ Advanced crawling completed!")
                    else:
                        print("⚠️ No results returned from crawler")

                except Exception as e:
                    print(f"❌ Crawling error: {e}")

                print(f"\n✅ Topic '{topic}' processing completed!\n")

    def _determine_category_from_research(self, topic: str, url_data: Dict) -> str:
        """Determine category based on adult content research topic and URL data"""
        topic_lower = topic.lower()
        site_type = url_data.get("site_type", "unknown")

        if any(x in topic_lower for x in ["hentai", "anime"]):
            if site_type == "hentai_site":
                return "hentai_premium"
            elif site_type == "image_gallery":
                return "hentai_gallery"
            else:
                return "hentai_general"
        elif any(x in topic_lower for x in ["porn", "xxx", "adult"]):
            if site_type == "porn_tube_site":
                return "porn_tube"
            elif site_type == "cam_premium_site":
                return "porn_premium"
            else:
                return "porn_general"
        elif any(x in topic_lower for x in ["nude", "erotic", "nsfw"]):
            if site_type == "image_gallery":
                return "nsfw_gallery"
            else:
                return "nsfw_general"
        else:
            return "adult_general"

    async def demonstrate_ai_research(
        self, jina_api_key: str, topic: str = "hentai anime"
    ):
        """Demonstrate AI-driven URL discovery"""
        try:
            from src.research.jina_researcher import MCP_JinaIntegration

            logger.info(f"🧠 Starting AI research for topic: {topic}")

            # Mock MCP server for demonstration
            class MockMCPServer:
                pass

            # Initialize Jina integration
            jina_integration = MCP_JinaIntegration(jina_api_key, MockMCPServer())

            # Research request
            research_request = {
                "topic": topic,
                "context": {"style": "professional", "quality": "high"},
                "max_keywords": 3,
                "urls_per_keyword": 5,
                "filter_criteria": {"max_targets": 10},
            }

            # Run discovery
            discovery_result = await jina_integration.auto_discover_scraping_targets(
                research_request
            )

            if discovery_result["status"] == "success":
                targets = discovery_result["filtered_targets"]
                logger.info(
                    f"✅ AI research successful: {len(targets)} targets discovered"
                )

                # Show discovered targets
                for i, target in enumerate(targets[:3], 1):
                    logger.info(
                        f"  {i}. {target['domain']} (Priority: {target.get('scraping_priority', 0)})"
                    )

                return targets
            else:
                logger.error(f"❌ AI research failed: {discovery_result.get('error')}")
                return []

        except Exception as e:
            logger.error(f"❌ AI research error: {e}")
            return []

    async def scrape_with_proxy_rotation(
        self, urls: List[str], max_images_per_url: int = 10
    ) -> Dict[str, Any]:
        """Demonstrate scraping with proxy rotation"""
        logger.info(f"🚀 Starting scraping with proxy rotation")
        logger.info(f"📋 URLs to scrape: {len(urls)}")

        scraping_results = {
            "successful_scrapes": 0,
            "failed_scrapes": 0,
            "total_images_found": 0,
            "scraping_details": [],
            "proxy_performance": {},
        }

        for i, url in enumerate(urls, 1):
            logger.info(f"🔍 Scraping {i}/{len(urls)}: {url}")

            try:
                # Choose appropriate scraper
                scraper = self.scrapers["generic"]
                if "pornpics.com" in url.lower():
                    scraper = self.scrapers.get("pornpics", self.scrapers["generic"])

                # Perform scraping
                result = await scraper.scrape_url(url, max_images_per_url)

                if result["status"] == "success":
                    scraping_results["successful_scrapes"] += 1
                    images_found = len(result.get("images", []))
                    scraping_results["total_images_found"] += images_found

                    scraping_results["scraping_details"].append(
                        {
                            "url": url,
                            "status": "success",
                            "images_found": images_found,
                            "title": result.get("title", "Unknown"),
                        }
                    )

                    logger.info(f"  ✅ Success: {images_found} images found")

                else:
                    scraping_results["failed_scrapes"] += 1
                    scraping_results["scraping_details"].append(
                        {
                            "url": url,
                            "status": "failed",
                            "error": result.get("message", "Unknown error"),
                        }
                    )

                    logger.warning(f"  ❌ Failed: {result.get('message')}")

                # Get proxy stats after each scrape
                if hasattr(scraper, "get_proxy_stats"):
                    stats = scraper.get_proxy_stats()
                    if stats:
                        scraping_results["proxy_performance"] = stats

                # Respectful delay between requests
                await asyncio.sleep(2)

            except Exception as e:
                scraping_results["failed_scrapes"] += 1
                logger.error(f"  ❌ Scraping error: {e}")

        # Log final summary
        logger.info(f"📊 Scraping Summary:")
        logger.info(f"  ✅ Successful: {scraping_results['successful_scrapes']}")
        logger.info(f"  ❌ Failed: {scraping_results['failed_scrapes']}")
        logger.info(f"  🖼️ Total Images: {scraping_results['total_images_found']}")

        return scraping_results

    def get_proxy_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive proxy health report"""
        if not self.proxy_rotator:
            return {"error": "Proxy system not initialized"}

        stats = self.proxy_rotator.get_proxy_stats()

        report = {
            "overview": {
                "total_proxies": stats["total_proxies"],
                "healthy_proxies": stats["healthy_proxies"],
                "health_percentage": (
                    (stats["healthy_proxies"] / stats["total_proxies"]) * 100
                    if stats["total_proxies"] > 0
                    else 0
                ),
            },
            "performance": {
                "best_proxy": None,
                "worst_proxy": None,
                "average_response_time": 0,
                "total_requests": 0,
            },
            "detailed_stats": stats["proxies"],
        }

        # Calculate performance metrics
        if stats["proxies"]:
            # Find best and worst performing proxies
            healthy_proxies = [p for p in stats["proxies"] if p["is_healthy"]]

            if healthy_proxies:
                best_proxy = max(healthy_proxies, key=lambda p: p["success_rate"])
                worst_proxy = min(healthy_proxies, key=lambda p: p["success_rate"])

                report["performance"][
                    "best_proxy"
                ] = f"{best_proxy['ip']}:{best_proxy['port']} ({best_proxy['success_rate']:.2%})"
                report["performance"][
                    "worst_proxy"
                ] = f"{worst_proxy['ip']}:{worst_proxy['port']} ({worst_proxy['success_rate']:.2%})"

                # Calculate averages
                total_response_time = sum(p["response_time"] for p in healthy_proxies)
                report["performance"]["average_response_time"] = (
                    total_response_time / len(healthy_proxies)
                )

                total_requests = sum(
                    p["success_count"] + p["failure_count"] for p in stats["proxies"]
                )
                report["performance"]["total_requests"] = total_requests

        return report

    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, "proxy_session"):
            self.proxy_session.close()
        logger.info("🧹 Cleanup completed")


async def main():
    """Main demonstration function"""
    logger.info("🚀 Professional AI-Driven Web Scraping Demonstration")
    logger.info("=" * 60)

    # Initialize pipeline
    pipeline = AdultContentScrapingPipeline()

    try:
        # Step 1: Initialize proxy system
        logger.info("\n📍 Step 1: Initialize Proxy System")
        if not pipeline.initialize_proxy_system():
            logger.error("Failed to initialize proxy system - aborting")
            return

        # Step 2: Initialize scrapers
        logger.info("\n📍 Step 2: Initialize Scrapers")
        if not pipeline.initialize_scrapers():
            logger.error("Failed to initialize scrapers - aborting")
            return

        # Step 3: Test proxy system
        logger.info("\n📍 Step 3: Test Proxy System")
        test_results = await pipeline.test_proxy_system(test_count=5)

        if test_results["successful_requests"] == 0:
            logger.error("All proxy tests failed - check configuration")
            return

        # Step 4: Demonstrate AI research (requires Jina API key)
        jina_api_key = "your_jina_api_key_here"  # Replace with actual key
        if jina_api_key != "your_jina_api_key_here":
            logger.info("\n📍 Step 4: AI-Driven URL Discovery")
            targets = await pipeline.demonstrate_ai_research(jina_api_key)
            urls_to_scrape = [target["url"] for target in targets[:3]]
        else:
            logger.info("\n📍 Step 4: Using Sample URLs (Jina API key not provided)")
            urls_to_scrape = [
                "https://example.com",  # Replace with actual test URLs
                "https://httpbin.org/html",
            ]

        # Step 5: Demonstrate scraping with proxy rotation
        logger.info("\n📍 Step 5: Scraping with Proxy Rotation")
        scraping_results = await pipeline.scrape_with_proxy_rotation(urls_to_scrape)

        # Step 6: Generate health report
        logger.info("\n📍 Step 6: Proxy Health Report")
        health_report = pipeline.get_proxy_health_report()

        logger.info(f"📊 Health Overview:")
        overview = health_report["overview"]
        logger.info(
            f"  Proxy Health: {overview['health_percentage']:.1f}% ({overview['healthy_proxies']}/{overview['total_proxies']})"
        )

        performance = health_report["performance"]
        if performance["best_proxy"]:
            logger.info(f"  Best Proxy: {performance['best_proxy']}")
            logger.info(f"  Avg Response: {performance['average_response_time']:.2f}s")
            logger.info(f"  Total Requests: {performance['total_requests']}")

        # Step 7: NEW - Demonstrate adult content researcher integration (if Jina API key available)
        if jina_api_key != "your_jina_api_key_here":
            logger.info(
                "\n📍 Step 7: NEW - Adult Content Researcher Integration Pipeline"
            )
            research_topics = [
                "hentai anime galleries",
                "nsfw image collections",
                "adult video content",
                "porn tube sites",
            ]
            try:
                # Set the API key for the pipeline
                pipeline.jina_api_key = jina_api_key
                await pipeline.demonstrate_researcher_integration(research_topics)
                logger.info("✅ Researcher integration demo completed!")
            except Exception as e:
                logger.error(f"❌ Researcher integration demo failed: {e}")
        else:
            logger.info(
                "\n📍 Step 7: Skipped - Researcher Integration (API key needed)"
            )
            logger.info(
                "💡 Set jina_api_key to enable advanced researcher integration demo"
            )

        logger.info("\n✅ Demonstration completed successfully!")

    except Exception as e:
        logger.error(f"❌ Demonstration failed: {e}")

    finally:
        # Cleanup
        pipeline.cleanup()


if __name__ == "__main__":
    """
    To run this demonstration:

    1. Install dependencies:
       pip install -r requirements.txt

    2. Configure your proxies in config/proxy_config.json

    3. (Optional) Add your Jina API key for AI research

    4. Run the script:
       python examples/professional_scraping_pipeline.py

    This will demonstrate:
    - Proxy rotation and health monitoring
    - AI-driven URL discovery (if API key provided)
    - Professional web scraping with error handling
    - Performance monitoring and reporting
    """
    asyncio.run(main())
