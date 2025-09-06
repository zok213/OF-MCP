#!/usr/bin/env python3
"""
Jina AI Adult Content Research Integration for MCP Web Scraper
Specialized URL discovery and keyword generation for NSFW content
Focuses exclusively on adult entertainment: porn, hentai, and NSFW material
"""

import aiohttp
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, urljoin
import re

logger = logging.getLogger("jina-researcher")


class JinaResearcher:
    """
    Adult Content AI Research Integration for MCP Web Scraper
    Specialized for adult content URL discovery and keyword generation
    Focuses exclusively on NSFW, porn, hentai, and adult entertainment content
    """

    def __init__(self, api_key: str, base_url: str = "https://eu-s-beta.jina.ai"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None

        # Professional headers for Jina API - Adult Content Focused
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "MCP-AdultContent-Scraper/1.0",
            "X-No-Cache": "true",
            "X-Respond-With": "no-content",
        }

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def generate_research_keywords(
        self, base_topic: str, context: Dict = None
    ) -> List[str]:
        """
        Generate adult content research keywords using AI reasoning
        Exclusively focused on NSFW, porn, hentai, and adult entertainment

        Args:
            base_topic: Primary adult content topic (e.g., "anime girls", "milf", "teens")
            context: Additional context for adult keyword generation

        Returns:
            List of adult content keywords
        """
        try:
            # Adult content keyword expansion logic
            keywords = [base_topic.lower()]

            # Force adult content generation - this pipeline is adult-only
            adult_keywords = [
                f"{base_topic} porn",
                f"{base_topic} hentai",
                f"{base_topic} nsfw",
                f"{base_topic} adult content",
                f"{base_topic} xxx",
                f"{base_topic} erotic",
                f"{base_topic} nude",
                f"{base_topic} sexy",
                f"{base_topic} 18+",
                f"porn {base_topic}",
                f"hentai {base_topic}",
                f"nsfw {base_topic}",
                f"adult {base_topic}",
                f"xxx {base_topic}",
                f"nude {base_topic}",
                f"sexy {base_topic}",
                f"hot {base_topic}",
            ]
            keywords.extend(adult_keywords)

            # Adult content specific variations - always included
            adult_expansions = [
                "porn videos",
                "hentai anime",
                "nsfw content",
                "adult videos",
                "xxx movies",
                "erotic photos",
                "nude galleries",
                "18+ content",
                "hardcore porn",
                "softcore erotica",
                "hentai manga",
                "nsfw art",
                "adult entertainment",
                "sex videos",
                "porn sites",
                "adult websites",
                "nsfw images",
                "erotic art",
                "adult comics",
                "porn galleries",
            ]
            keywords.extend(adult_expansions)

            # Add base topic variations with adult terms
            topic_variations = [
                f"{base_topic} sex",
                f"{base_topic} fucking",
                f"{base_topic} naked",
                f"{base_topic} topless",
                f"{base_topic} bikini",
                f"{base_topic} lingerie",
                f"{base_topic} uncensored",
            ]
            keywords.extend(topic_variations)

            # Remove duplicates and clean
            keywords = list(set(k.strip() for k in keywords if k.strip()))

            logger.info(
                f"Generated {len(keywords)} adult content keywords from base topic: {base_topic}"
            )
            return keywords[:25]  # Return top 25 most relevant adult keywords

        except Exception as e:
            logger.error(f"Error generating adult keywords: {e}")
            return [f"{base_topic} porn", f"{base_topic} nsfw", base_topic]

    async def research_urls_with_jina(
        self, keyword: str, max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Use Jina AI to discover adult content URLs for a keyword
        Exclusively searches for NSFW, porn, hentai and adult entertainment sites

        Args:
            keyword: Adult content search keyword
            max_results: Maximum number of adult URLs to return

        Returns:
            Dictionary with adult content research results and discovered URLs
        """
        try:
            if not self.session:
                raise ValueError("JinaResearcher must be used as async context manager")

            # Construct Jina API query
            query_params = {"q": keyword}

            logger.info(f"Researching URLs for keyword: {keyword}")

            async with self.session.get(self.base_url, params=query_params) as response:
                if response.status == 200:
                    data = await response.json()

                    # Extract URLs from Jina response
                    discovered_urls = self._extract_urls_from_jina_response(data)

                    # Filter and validate URLs
                    valid_urls = await self._validate_urls(
                        discovered_urls[:max_results]
                    )

                    return {
                        "status": "success",
                        "keyword": keyword,
                        "total_found": len(discovered_urls),
                        "valid_urls": valid_urls,
                        "raw_response": (
                            data if len(str(data)) < 1000 else "Response too large"
                        ),
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Jina API error {response.status}: {error_text}")
                    return {
                        "status": "error",
                        "keyword": keyword,
                        "error": f"API returned status {response.status}",
                        "valid_urls": [],
                    }

        except Exception as e:
            logger.error(f"Error researching URLs with Jina: {e}")
            return {
                "status": "error",
                "keyword": keyword,
                "error": str(e),
                "valid_urls": [],
            }

    def _extract_urls_from_jina_response(self, data: Dict) -> List[str]:
        """
        Extract URLs from Jina API response
        Professional parsing of various response formats
        """
        urls = []

        try:
            # Handle different Jina response formats
            if isinstance(data, dict):
                # Look for URLs in common response fields
                for field in ["results", "data", "items", "urls", "links"]:
                    if field in data:
                        field_data = data[field]
                        if isinstance(field_data, list):
                            for item in field_data:
                                if isinstance(item, dict):
                                    # Extract URL from various possible fields
                                    url = (
                                        item.get("url")
                                        or item.get("link")
                                        or item.get("href")
                                    )
                                    if url:
                                        urls.append(url)
                                elif isinstance(item, str) and self._is_valid_url(item):
                                    urls.append(item)

                # Also check for direct URL strings in the response
                response_text = str(data)
                found_urls = re.findall(r'https?://[^\s<>"\']+', response_text)
                urls.extend(found_urls)

            # Remove duplicates while preserving order
            seen = set()
            unique_urls = []
            for url in urls:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)

            logger.info(f"Extracted {len(unique_urls)} URLs from Jina response")
            return unique_urls

        except Exception as e:
            logger.error(f"Error extracting URLs from Jina response: {e}")
            return []

    def _is_valid_url(self, url: str) -> bool:
        """Check if string is a valid URL"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in [
                "http",
                "https",
            ]
        except:
            return False

    async def _validate_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Validate and enrich discovered URLs
        Professional URL analysis and filtering
        """
        validated_urls = []

        for url in urls:
            try:
                if not self._is_valid_url(url):
                    continue

                parsed = urlparse(url)
                domain = parsed.netloc.lower()

                # Professional URL analysis
                url_info = {
                    "url": url,
                    "domain": domain,
                    "is_image_site": self._is_likely_image_site(domain),
                    "site_type": self._classify_site_type(domain),
                    "scraping_priority": self._calculate_scraping_priority(domain, url),
                    "legal_considerations": self._get_legal_considerations(domain),
                }

                validated_urls.append(url_info)

            except Exception as e:
                logger.warning(f"Error validating URL {url}: {e}")

        # Sort by scraping priority (highest first)
        validated_urls.sort(key=lambda x: x["scraping_priority"], reverse=True)

        return validated_urls

    def _is_likely_image_site(self, domain: str) -> bool:
        """Determine if domain is likely to contain adult images/videos"""
        adult_indicators = [
            "porn",
            "hentai",
            "nsfw",
            "adult",
            "xxx",
            "erotic",
            "nude",
            "sex",
            "tube",
            "hub",
            "xnxx",
            "pornhub",
            "xvideos",
            "youporn",
            "redtube",
            "chaturbate",
            "cam",
            "webcam",
            "onlyfans",
            "manyvids",
            "clips4sale",
            "gallery",
            "pic",
            "image",
            "photo",
            "video",
            "movie",
            "film",
        ]
        return any(indicator in domain.lower() for indicator in adult_indicators)

    def _classify_site_type(self, domain: str) -> str:
        """Classify the type of adult website"""
        if any(
            x in domain
            for x in ["pornhub", "xvideos", "xnxx", "youporn", "redtube", "tube8"]
        ):
            return "porn_tube_site"
        elif any(
            x in domain
            for x in ["onlyfans", "manyvids", "clips4sale", "chaturbate", "cam4"]
        ):
            return "cam_premium_site"
        elif any(x in domain for x in ["hentai", "nhentai", "hanime", "anime"]):
            return "hentai_site"
        elif any(x in domain for x in ["reddit", "twitter", "tumblr", "instagram"]):
            return "social_media_nsfw"
        elif any(x in domain for x in ["imagefap", "imgur", "photobucket", "gallery"]):
            return "image_gallery"
        elif any(
            x in domain
            for x in ["xxx", "porn", "adult", "nsfw", "erotic", "nude", "sex"]
        ):
            return "general_adult_content"
        else:
            return "potential_adult_site"

    def _calculate_scraping_priority(self, domain: str, url: str) -> int:
        """Calculate adult content scraping priority score (0-100)"""
        score = 30  # Lower base score - we're picky about adult content

        # High boost for adult image/video sites
        if self._is_likely_image_site(domain):
            score += 40

        # Maximum boost for premium adult sites
        if any(
            x in domain for x in ["pornhub", "xvideos", "xnxx", "youporn", "onlyfans"]
        ):
            score += 35

        # High boost for hentai sites
        if any(x in domain for x in ["hentai", "nhentai", "hanime"]):
            score += 30

        # Boost for general adult content
        if any(x in domain for x in ["xxx", "porn", "adult", "nsfw", "erotic", "nude"]):
            score += 25

        # Boost for image galleries
        if any(x in domain for x in ["gallery", "imagefap", "imgur"]):
            score += 20

        # Small penalty for social media (harder to scrape)
        if any(x in domain for x in ["reddit", "twitter", "tumblr"]):
            score -= 10

        # URL structure analysis for adult content
        if any(
            x in url.lower()
            for x in [
                "gallery",
                "photos",
                "videos",
                "porn",
                "hentai",
                "nsfw",
                "xxx",
                "nude",
            ]
        ):
            score += 15

        return max(0, min(100, score))

    def _get_legal_considerations(self, domain: str) -> Dict[str, Any]:
        """Get legal considerations for scraping adult content domains"""

        # Premium adult sites - usually protected
        if any(
            x in domain for x in ["onlyfans", "manyvids", "chaturbate", "clips4sale"]
        ):
            return {
                "risk_level": "very_high",
                "recommendation": "Requires paid subscription and respects DRM",
                "requires_permission": True,
                "note": "Premium content - likely protected",
            }

        # Major tube sites - check ToS
        elif any(x in domain for x in ["pornhub", "xvideos", "xnxx", "youporn"]):
            return {
                "risk_level": "high",
                "recommendation": "Check ToS, respect rate limits",
                "requires_permission": True,
                "note": "Large commercial sites with strict policies",
            }

        # Social media with adult content
        elif any(x in domain for x in ["reddit", "twitter", "tumblr"]):
            return {
                "risk_level": "high",
                "recommendation": "Use official API when possible",
                "requires_permission": True,
                "note": "Social platforms - API preferred",
            }

        # Image galleries and smaller sites
        elif any(x in domain for x in ["imagefap", "imgur", "gallery"]):
            return {
                "risk_level": "medium",
                "recommendation": "Respect robots.txt and rate limits",
                "requires_permission": False,
                "note": "Usually more permissive for scraping",
            }

        # Hentai/anime sites
        elif any(x in domain for x in ["nhentai", "hanime", "hentai"]):
            return {
                "risk_level": "medium",
                "recommendation": "Check ToS, respect rate limits",
                "requires_permission": False,
                "note": "Anime content - varies by site",
            }

        # Default
        else:
            return {
                "risk_level": "medium",
                "recommendation": "Check robots.txt and ToS",
                "requires_permission": True,
            }

    async def intelligent_research_pipeline(
        self,
        base_topic: str,
        context: Dict = None,
        max_keywords: int = 5,
        urls_per_keyword: int = 5,
    ) -> Dict[str, Any]:
        """
        Complete adult content research pipeline
        Combines adult keyword generation with NSFW URL discovery
        Exclusively targets adult entertainment websites
        """
        try:
            logger.info(f"Starting adult content research pipeline for: {base_topic}")

            # Force adult context if not provided
            if not context:
                context = {"style": "adult", "content_type": "nsfw"}
            elif (
                context.get("style") != "adult"
                and context.get("content_type") != "nsfw"
            ):
                context["style"] = "adult"
                context["content_type"] = "nsfw"

            # Step 1: Generate adult keywords
            keywords = await self.generate_research_keywords(base_topic, context)
            selected_keywords = keywords[:max_keywords]

            # Step 2: Research adult URLs for each keyword
            all_results = []
            total_valid_urls = 0

            for keyword in selected_keywords:
                logger.info(f"Researching adult keyword: {keyword}")
                research_result = await self.research_urls_with_jina(
                    keyword, urls_per_keyword
                )

                if research_result["status"] == "success":
                    total_valid_urls += len(research_result["valid_urls"])
                    all_results.append(research_result)
                else:
                    logger.warning(
                        f"Failed to research keyword '{keyword}': {research_result.get('error')}"
                    )

            # Step 3: Compile final results
            final_result = {
                "status": "success" if all_results else "partial_success",
                "base_topic": base_topic,
                "context": context,
                "keywords_generated": len(keywords),
                "keywords_researched": len(selected_keywords),
                "total_valid_urls": total_valid_urls,
                "research_results": all_results,
                "summary": self._create_research_summary(all_results),
            }

            logger.info(
                f"Research pipeline completed: {total_valid_urls} URLs discovered from {len(selected_keywords)} keywords"
            )
            return final_result

        except Exception as e:
            logger.error(f"Error in intelligent research pipeline: {e}")
            return {
                "status": "error",
                "base_topic": base_topic,
                "error": str(e),
                "research_results": [],
            }

    def _create_research_summary(self, results: List[Dict]) -> Dict[str, Any]:
        """Create summary of research results"""
        if not results:
            return {"message": "No results to summarize"}

        # Aggregate statistics
        all_urls = []
        site_types = {}
        priority_distribution = {"high": 0, "medium": 0, "low": 0}

        for result in results:
            for url_info in result.get("valid_urls", []):
                all_urls.append(url_info)

                # Count site types
                site_type = url_info.get("site_type", "unknown")
                site_types[site_type] = site_types.get(site_type, 0) + 1

                # Count priority distribution
                priority = url_info.get("scraping_priority", 0)
                if priority >= 70:
                    priority_distribution["high"] += 1
                elif priority >= 40:
                    priority_distribution["medium"] += 1
                else:
                    priority_distribution["low"] += 1

        return {
            "total_urls": len(all_urls),
            "site_type_distribution": site_types,
            "priority_distribution": priority_distribution,
            "top_domains": list(set(url["domain"] for url in all_urls[:10])),
            "recommended_targets": [
                url for url in all_urls if url.get("scraping_priority", 0) >= 70
            ][:5],
        }


class MCP_JinaIntegration:
    """
    Adult Content Integration layer between MCP server and Jina AI research
    Provides intelligent adult URL discovery for NSFW scraping system
    Exclusively targets adult entertainment websites
    """

    def __init__(self, jina_api_key: str, mcp_server_instance=None):
        self.jina_api_key = jina_api_key
        self.mcp_server = mcp_server_instance

    async def auto_discover_scraping_targets(
        self, research_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Automatically discover adult content scraping targets using Jina AI

        Args:
            research_request: {
                "topic": "anime girls",
                "context": {"style": "adult", "content_type": "nsfw"},
                "max_targets": 20,
                "filter_criteria": {...}
            }
        """
        try:
            async with JinaResearcher(self.jina_api_key) as researcher:

                # Force adult context
                if "context" not in research_request:
                    research_request["context"] = {
                        "style": "adult",
                        "content_type": "nsfw",
                    }
                else:
                    research_request["context"]["style"] = "adult"
                    research_request["context"]["content_type"] = "nsfw"

                # Run adult content research pipeline
                research_results = await researcher.intelligent_research_pipeline(
                    base_topic=research_request.get("topic", ""),
                    context=research_request.get("context", {}),
                    max_keywords=research_request.get("max_keywords", 5),
                    urls_per_keyword=research_request.get("urls_per_keyword", 5),
                )

                if research_results["status"] in ["success", "partial_success"]:
                    # Filter results based on criteria
                    filtered_targets = self._filter_scraping_targets(
                        research_results, research_request.get("filter_criteria", {})
                    )

                    # Prepare for MCP scraping
                    scraping_plan = self._create_scraping_plan(filtered_targets)

                    return {
                        "status": "success",
                        "research_results": research_results,
                        "filtered_targets": filtered_targets,
                        "scraping_plan": scraping_plan,
                        "ready_for_scraping": True,
                    }
                else:
                    return {
                        "status": "error",
                        "error": research_results.get("error", "Research failed"),
                        "ready_for_scraping": False,
                    }

        except Exception as e:
            logger.error(f"Error in auto_discover_scraping_targets: {e}")
            return {"status": "error", "error": str(e), "ready_for_scraping": False}

    def _filter_scraping_targets(
        self, research_results: Dict, criteria: Dict
    ) -> List[Dict]:
        """Filter research results based on criteria"""
        filtered = []

        for result in research_results.get("research_results", []):
            for url_info in result.get("valid_urls", []):

                # Apply filters
                passes_filter = True

                if criteria.get("min_priority"):
                    if url_info.get("scraping_priority", 0) < criteria["min_priority"]:
                        passes_filter = False

                if criteria.get("allowed_site_types"):
                    if url_info.get("site_type") not in criteria["allowed_site_types"]:
                        passes_filter = False

                if criteria.get("exclude_high_risk", True):
                    legal = url_info.get("legal_considerations", {})
                    if legal.get("risk_level") == "high":
                        passes_filter = False

                if passes_filter:
                    filtered.append(url_info)

        # Sort by priority and limit results
        filtered.sort(key=lambda x: x.get("scraping_priority", 0), reverse=True)
        max_targets = criteria.get("max_targets", 20)

        return filtered[:max_targets]

    def _create_scraping_plan(self, targets: List[Dict]) -> Dict[str, Any]:
        """Create an execution plan for scraping discovered targets"""

        plan = {
            "total_targets": len(targets),
            "execution_order": [],
            "estimated_time": 0,
            "legal_review_required": False,
        }

        for i, target in enumerate(targets):
            task = {
                "order": i + 1,
                "url": target["url"],
                "domain": target["domain"],
                "priority": target.get("scraping_priority", 0),
                "site_type": target.get("site_type", "unknown"),
                "estimated_images": self._estimate_image_count(target),
                "legal_check_required": target.get("legal_considerations", {}).get(
                    "requires_permission", True
                ),
            }

            plan["execution_order"].append(task)

            # Estimate time (rough calculation)
            estimated_images = task["estimated_images"]
            task_time = max(30, estimated_images * 2)  # 2 seconds per image minimum
            plan["estimated_time"] += task_time

            # Check if legal review needed
            if task["legal_check_required"]:
                plan["legal_review_required"] = True

        return plan

    def _estimate_image_count(self, target: Dict) -> int:
        """Estimate number of images available at target URL"""
        site_type = target.get("site_type", "unknown")
        priority = target.get("scraping_priority", 0)

        # Rough estimates based on site type
        base_estimates = {
            "image_platform": 50,
            "professional_portfolio": 30,
            "stock_photos": 100,
            "social_media": 20,
            "adult_content": 40,
            "general_website": 15,
        }

        base_count = base_estimates.get(site_type, 20)

        # Adjust based on priority
        if priority >= 80:
            return int(base_count * 1.5)
        elif priority >= 60:
            return base_count
        else:
            return int(base_count * 0.7)


# Example usage and testing functions
async def test_jina_integration():
    """Test function for Adult Content Jina integration"""

    # Replace with your actual Jina API key
    api_key = "jina_6d7ebc1123864682af6f40ee3f1cb0cfh2B52EisCvTac-yJkU1tD6xv11Xf"

    try:
        async with JinaResearcher(api_key) as researcher:

            # Test adult content keyword generation
            adult_keywords = await researcher.generate_research_keywords(
                "anime girls", {"style": "adult", "content_type": "nsfw"}
            )
            print(f"Generated adult keywords: {adult_keywords}")

            # Test hentai keyword generation
            hentai_keywords = await researcher.generate_research_keywords(
                "hentai", {"style": "adult"}
            )
            print(f"Generated hentai keywords: {hentai_keywords}")

            # Test adult content research
            adult_research = await researcher.research_urls_with_jina("hentai anime", 5)
            print(f"Adult research result: {adult_research}")

            # Test porn research
            porn_research = await researcher.research_urls_with_jina("porn videos", 3)
            print(f"Porn research result: {porn_research}")

            # Test full pipeline
            pipeline_result = await researcher.intelligent_research_pipeline(
                "model portfolio photos",
                {"style": "fashion"},
                max_keywords=3,
                urls_per_keyword=3,
            )
            print(f"Pipeline result: {pipeline_result}")

            # Test adult content pipeline
            adult_pipeline = await researcher.intelligent_research_pipeline(
                "anime girls",
                {"style": "adult", "content_type": "nsfw"},
                max_keywords=2,
                urls_per_keyword=2,
            )
            print(f"Adult pipeline result: {adult_pipeline}")

    except Exception as e:
        print(f"Test error: {e}")


if __name__ == "__main__":
    asyncio.run(test_jina_integration())
