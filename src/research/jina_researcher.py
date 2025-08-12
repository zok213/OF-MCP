#!/usr/bin/env python3
"""
Jina AI Research Integration for MCP Web Scraper
Professional URL discovery and keyword generation system
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
    Professional Jina AI integration for intelligent URL discovery
    Automatically generates keywords and finds relevant URLs for scraping
    """
    
    def __init__(self, api_key: str, base_url: str = "https://eu-s-beta.jina.ai"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        
        # Professional headers for Jina API
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "MCP-WebScraper-Professional/1.0",
            "X-No-Cache": "true",
            "X-Respond-With": "no-content"
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def generate_research_keywords(self, base_topic: str, context: Dict = None) -> List[str]:
        """
        Generate intelligent research keywords using AI reasoning
        
        Args:
            base_topic: Primary research topic (e.g., "celebrity photos", "model portfolio")
            context: Additional context for keyword generation
            
        Returns:
            List of professionally generated keywords
        """
        try:
            # AI-driven keyword expansion logic
            keywords = [base_topic.lower()]
            
            # Context-aware keyword generation
            if context:
                if context.get('style') == 'professional':
                    keywords.extend([
                        f"{base_topic} professional photos",
                        f"{base_topic} portfolio",
                        f"{base_topic} high quality images",
                        f"{base_topic} photoshoot"
                    ])
                elif context.get('style') == 'fashion':
                    keywords.extend([
                        f"{base_topic} fashion",
                        f"{base_topic} modeling",
                        f"{base_topic} runway",
                        f"{base_topic} editorial"
                    ])
            
            # Add semantic variations
            semantic_expansions = [
                f"{base_topic} gallery",
                f"{base_topic} collection",
                f"{base_topic} archive",
                f"{base_topic} database",
                f"best {base_topic}",
                f"high resolution {base_topic}",
                f"{base_topic} HD images"
            ]
            
            keywords.extend(semantic_expansions)
            
            # Remove duplicates and clean
            keywords = list(set(k.strip() for k in keywords if k.strip()))
            
            logger.info(f"Generated {len(keywords)} research keywords from base topic: {base_topic}")
            return keywords[:15]  # Limit to top 15 most relevant
            
        except Exception as e:
            logger.error(f"Error generating keywords: {e}")
            return [base_topic]
    
    async def research_urls_with_jina(self, keyword: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Use Jina AI to discover relevant URLs for a keyword
        
        Args:
            keyword: Search keyword
            max_results: Maximum number of URLs to return
            
        Returns:
            Dictionary with research results and discovered URLs
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
                    valid_urls = await self._validate_urls(discovered_urls[:max_results])
                    
                    return {
                        "status": "success",
                        "keyword": keyword,
                        "total_found": len(discovered_urls),
                        "valid_urls": valid_urls,
                        "raw_response": data if len(str(data)) < 1000 else "Response too large"
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Jina API error {response.status}: {error_text}")
                    return {
                        "status": "error",
                        "keyword": keyword,
                        "error": f"API returned status {response.status}",
                        "valid_urls": []
                    }
                    
        except Exception as e:
            logger.error(f"Error researching URLs with Jina: {e}")
            return {
                "status": "error",
                "keyword": keyword,
                "error": str(e),
                "valid_urls": []
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
                for field in ['results', 'data', 'items', 'urls', 'links']:
                    if field in data:
                        field_data = data[field]
                        if isinstance(field_data, list):
                            for item in field_data:
                                if isinstance(item, dict):
                                    # Extract URL from various possible fields
                                    url = item.get('url') or item.get('link') or item.get('href')
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
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
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
                    "legal_considerations": self._get_legal_considerations(domain)
                }
                
                validated_urls.append(url_info)
                
            except Exception as e:
                logger.warning(f"Error validating URL {url}: {e}")
        
        # Sort by scraping priority (highest first)
        validated_urls.sort(key=lambda x: x['scraping_priority'], reverse=True)
        
        return validated_urls
    
    def _is_likely_image_site(self, domain: str) -> bool:
        """Determine if domain is likely to contain images"""
        image_indicators = [
            'photo', 'pic', 'image', 'gallery', 'portfolio', 
            'wallpaper', 'art', 'model', 'fashion', 'celebrity'
        ]
        return any(indicator in domain.lower() for indicator in image_indicators)
    
    def _classify_site_type(self, domain: str) -> str:
        """Classify the type of website"""
        if any(x in domain for x in ['instagram', 'facebook', 'twitter', 'tiktok']):
            return "social_media"
        elif any(x in domain for x in ['pinterest', 'flickr', 'deviantart']):
            return "image_platform"
        elif any(x in domain for x in ['wallhaven', 'unsplash', 'pexels']):
            return "stock_photos"
        elif any(x in domain for x in ['model', 'fashion', 'portfolio']):
            return "professional_portfolio"
        elif any(x in domain for x in ['adult', 'xxx', 'porn']):
            return "adult_content"
        else:
            return "general_website"
    
    def _calculate_scraping_priority(self, domain: str, url: str) -> int:
        """Calculate scraping priority score (0-100)"""
        score = 50  # Base score
        
        # Boost for image-related sites
        if self._is_likely_image_site(domain):
            score += 30
        
        # Boost for professional sites
        if any(x in domain for x in ['portfolio', 'professional', 'gallery']):
            score += 20
        
        # Penalty for social media (API preferred)
        if any(x in domain for x in ['instagram', 'facebook', 'twitter']):
            score -= 40
        
        # Boost for stock photo sites
        if any(x in domain for x in ['unsplash', 'pexels', 'wallhaven']):
            score += 25
        
        # URL structure analysis
        if any(x in url.lower() for x in ['gallery', 'photos', 'images']):
            score += 10
        
        return max(0, min(100, score))
    
    def _get_legal_considerations(self, domain: str) -> Dict[str, Any]:
        """Get legal considerations for scraping a domain"""
        
        # High-risk domains
        if any(x in domain for x in ['instagram', 'facebook', 'twitter']):
            return {
                "risk_level": "high",
                "recommendation": "Use official API instead",
                "requires_permission": True
            }
        
        # Medium-risk domains
        elif any(x in domain for x in ['pinterest', 'flickr']):
            return {
                "risk_level": "medium", 
                "recommendation": "Check ToS and consider API",
                "requires_permission": True
            }
        
        # Lower-risk domains
        elif any(x in domain for x in ['unsplash', 'pexels']):
            return {
                "risk_level": "low",
                "recommendation": "Usually allows scraping with attribution",
                "requires_permission": False
            }
        
        # Default
        else:
            return {
                "risk_level": "medium",
                "recommendation": "Check robots.txt and ToS",
                "requires_permission": True
            }
    
    async def intelligent_research_pipeline(self, 
                                          base_topic: str, 
                                          context: Dict = None,
                                          max_keywords: int = 5,
                                          urls_per_keyword: int = 5) -> Dict[str, Any]:
        """
        Complete intelligent research pipeline
        Combines keyword generation with URL discovery
        """
        try:
            logger.info(f"Starting intelligent research pipeline for: {base_topic}")
            
            # Step 1: Generate intelligent keywords
            keywords = await self.generate_research_keywords(base_topic, context)
            selected_keywords = keywords[:max_keywords]
            
            # Step 2: Research URLs for each keyword
            all_results = []
            total_valid_urls = 0
            
            for keyword in selected_keywords:
                logger.info(f"Researching keyword: {keyword}")
                research_result = await self.research_urls_with_jina(keyword, urls_per_keyword)
                
                if research_result["status"] == "success":
                    total_valid_urls += len(research_result["valid_urls"])
                    all_results.append(research_result)
                else:
                    logger.warning(f"Failed to research keyword '{keyword}': {research_result.get('error')}")
            
            # Step 3: Compile final results
            final_result = {
                "status": "success" if all_results else "partial_success",
                "base_topic": base_topic,
                "context": context,
                "keywords_generated": len(keywords),
                "keywords_researched": len(selected_keywords),
                "total_valid_urls": total_valid_urls,
                "research_results": all_results,
                "summary": self._create_research_summary(all_results)
            }
            
            logger.info(f"Research pipeline completed: {total_valid_urls} URLs discovered from {len(selected_keywords)} keywords")
            return final_result
            
        except Exception as e:
            logger.error(f"Error in intelligent research pipeline: {e}")
            return {
                "status": "error",
                "base_topic": base_topic,
                "error": str(e),
                "research_results": []
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
            "recommended_targets": [url for url in all_urls if url.get("scraping_priority", 0) >= 70][:5]
        }


class MCP_JinaIntegration:
    """
    Integration layer between MCP server and Jina AI research
    Provides intelligent URL discovery for the scraping system
    """
    
    def __init__(self, jina_api_key: str, mcp_server_instance=None):
        self.jina_api_key = jina_api_key
        self.mcp_server = mcp_server_instance
        
    async def auto_discover_scraping_targets(self, research_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Automatically discover scraping targets using Jina AI
        
        Args:
            research_request: {
                "topic": "celebrity photos",
                "context": {"style": "professional"},
                "max_targets": 20,
                "filter_criteria": {...}
            }
        """
        try:
            async with JinaResearcher(self.jina_api_key) as researcher:
                
                # Run intelligent research pipeline
                research_results = await researcher.intelligent_research_pipeline(
                    base_topic=research_request.get("topic", ""),
                    context=research_request.get("context", {}),
                    max_keywords=research_request.get("max_keywords", 5),
                    urls_per_keyword=research_request.get("urls_per_keyword", 5)
                )
                
                if research_results["status"] in ["success", "partial_success"]:
                    # Filter results based on criteria
                    filtered_targets = self._filter_scraping_targets(
                        research_results, 
                        research_request.get("filter_criteria", {})
                    )
                    
                    # Prepare for MCP scraping
                    scraping_plan = self._create_scraping_plan(filtered_targets)
                    
                    return {
                        "status": "success",
                        "research_results": research_results,
                        "filtered_targets": filtered_targets,
                        "scraping_plan": scraping_plan,
                        "ready_for_scraping": True
                    }
                else:
                    return {
                        "status": "error",
                        "error": research_results.get("error", "Research failed"),
                        "ready_for_scraping": False
                    }
                    
        except Exception as e:
            logger.error(f"Error in auto_discover_scraping_targets: {e}")
            return {
                "status": "error",
                "error": str(e),
                "ready_for_scraping": False
            }
    
    def _filter_scraping_targets(self, research_results: Dict, criteria: Dict) -> List[Dict]:
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
            "legal_review_required": False
        }
        
        for i, target in enumerate(targets):
            task = {
                "order": i + 1,
                "url": target["url"],
                "domain": target["domain"],
                "priority": target.get("scraping_priority", 0),
                "site_type": target.get("site_type", "unknown"),
                "estimated_images": self._estimate_image_count(target),
                "legal_check_required": target.get("legal_considerations", {}).get("requires_permission", True)
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
            "general_website": 15
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
    """Test function for Jina integration"""
    
    # Replace with your actual Jina API key
    api_key = "jina_6d7ebc1123864682af6f40ee3f1cb0cfh2B52EisCvTac-yJkU1tD6xv11Xf"
    
    try:
        async with JinaResearcher(api_key) as researcher:
            
            # Test keyword generation
            keywords = await researcher.generate_research_keywords(
                "celebrity photos",
                {"style": "professional"}
            )
            print(f"Generated keywords: {keywords}")
            
            # Test URL research
            research_result = await researcher.research_urls_with_jina("celebrity photos", 5)
            print(f"Research result: {research_result}")
            
            # Test full pipeline
            pipeline_result = await researcher.intelligent_research_pipeline(
                "model portfolio photos",
                {"style": "fashion"},
                max_keywords=3,
                urls_per_keyword=3
            )
            print(f"Pipeline result: {pipeline_result}")
            
    except Exception as e:
        print(f"Test error: {e}")


if __name__ == "__main__":
    asyncio.run(test_jina_integration())
