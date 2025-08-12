#!/usr/bin/env python3
"""
Professional Playwright-based Web Scraper
Inspired by Microsoft's Playwright MCP best practices for adult content sites
Educational/Research Purpose Only - Always respect website ToS and legal requirements
"""

import asyncio
import json
import logging
import random
import time
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin, urlparse, parse_qs
import hashlib
import os
import aiohttp
from dataclasses import dataclass

from playwright.async_api import (
    async_playwright, Browser, BrowserContext, Page, 
    TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
)

logger = logging.getLogger(__name__)

@dataclass
class ScrapingResult:
    """Structured result from scraping operation"""
    status: str  # 'success', 'blocked', 'error', 'partial'
    message: str
    images: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    total_images_found: int = 0
    filtered_images: int = 0
    title: Optional[str] = None
    model_name: Optional[str] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass 
class ImageInfo:
    """Structured image information"""
    url: str
    filename: str
    alt_text: Optional[str] = None
    title: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    hash_md5: Optional[str] = None

class PlaywrightScraper:
    """Professional Playwright-based web scraper with adult site optimization"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
        # Professional browser configuration
        self.browser_config = {
            'headless': config.get('headless', True),
            'viewport': config.get('viewport', {'width': 1920, 'height': 1080}),
            'user_agent': config.get('user_agent', 
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'),
            'locale': config.get('locale', 'en-US'),
            'timezone_id': config.get('timezone', 'America/New_York'),
            'geolocation': config.get('geolocation'),
            'permissions': config.get('permissions', ['geolocation']),
            'color_scheme': config.get('color_scheme', 'no-preference')
        }
        
        # Adult site specific settings
        self.adult_site_config = {
            'bypass_age_verification': config.get('bypass_age_verification', True),
            'handle_cookie_banners': config.get('handle_cookie_banners', True),
            'wait_for_dynamic_content': config.get('wait_for_dynamic_content', True),
            'scroll_for_lazy_load': config.get('scroll_for_lazy_load', True)
        }
        
        # Rate limiting and politeness
        self.rate_limiting = {
            'request_delay_ms': config.get('request_delay_ms', 2000),
            'random_delay_variance': config.get('random_delay_variance', 1000),
            'max_concurrent_requests': config.get('max_concurrent_requests', 3),
            'respect_robots_txt': config.get('respect_robots_txt', True)
        }
        
        # Image quality filters
        self.image_filters = {
            'min_width': config.get('min_width', 800),
            'min_height': config.get('min_height', 600),
            'max_file_size_mb': config.get('max_file_size_mb', 50),
            'allowed_formats': config.get('allowed_formats', ['jpg', 'jpeg', 'png', 'webp']),
            'skip_thumbnails': config.get('skip_thumbnails', True),
            'skip_previews': config.get('skip_previews', True)
        }

        # Session persistence
        self.session_config = {
            'persistent_context': config.get('persistent_context', True),
            'user_data_dir': config.get('user_data_dir'),
            'storage_state': config.get('storage_state')
        }

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()

    async def initialize_browser(self):
        """Initialize Playwright browser with professional configuration"""
        try:
            playwright = await async_playwright().start()
            
            # Launch browser with stealth configuration
            self.browser = await playwright.chromium.launch(
                headless=self.browser_config['headless'],
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding'
                ]
            )
            
            # Create persistent context if configured
            if self.session_config.get('persistent_context') and self.session_config.get('user_data_dir'):
                self.context = await self.browser.new_context(
                    viewport=self.browser_config['viewport'],
                    user_agent=self.browser_config['user_agent'],
                    locale=self.browser_config['locale'],
                    timezone_id=self.browser_config['timezone_id'],
                    geolocation=self.browser_config['geolocation'],
                    permissions=self.browser_config['permissions'],
                    color_scheme=self.browser_config['color_scheme'],
                    storage_state=self.session_config.get('storage_state')
                )
            else:
                self.context = await self.browser.new_context(
                    viewport=self.browser_config['viewport'],
                    user_agent=self.browser_config['user_agent'],
                    locale=self.browser_config['locale'],
                    timezone_id=self.browser_config['timezone_id'],
                    geolocation=self.browser_config['geolocation'],
                    permissions=self.browser_config['permissions'],
                    color_scheme=self.browser_config['color_scheme']
                )
            
            # Set up request interception for optimization
            await self.setup_request_interception()
            
            logger.info("Playwright browser initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing browser: {e}")
            raise

    async def setup_request_interception(self):
        """Setup intelligent request interception for performance"""
        if not self.context:
            return
            
        async def handle_request(route, request):
            """Handle and filter requests intelligently"""
            url = request.url
            resource_type = request.resource_type
            
            # Block unnecessary resources for faster loading
            blocked_resources = ['font', 'stylesheet', 'script', 'other']
            if resource_type in blocked_resources:
                # Allow critical scripts for adult sites (age verification, etc.)
                if any(keyword in url.lower() for keyword in ['age', 'verify', 'confirm', 'adult']):
                    await route.continue_()
                else:
                    await route.abort()
                return
                
            # Allow images and documents
            await route.continue_()
        
        await self.context.route("**/*", handle_request)

    async def scrape_url(self, url: str, max_images: int = 50) -> ScrapingResult:
        """Scrape images from a URL with professional techniques"""
        try:
            if not self.context:
                await self.initialize_browser()
            
            page = await self.context.new_page()
            
            # Enable console and error logging
            page.on("console", lambda msg: logger.debug(f"Console [{msg.type}]: {msg.text}"))
            page.on("pageerror", lambda error: logger.warning(f"Page error: {error}"))
            
            logger.info(f"Scraping URL: {url}")
            
            # Navigate with professional error handling
            try:
                response = await page.goto(
                    url,
                    wait_until='domcontentloaded',
                    timeout=30000
                )
                
                if response and response.status >= 400:
                    return ScrapingResult(
                        status='error',
                        message=f"HTTP {response.status}: {response.status_text}",
                        images=[],
                        metadata={}
                    )
                    
            except PlaywrightTimeoutError:
                return ScrapingResult(
                    status='error',
                    message="Page load timeout",
                    images=[],
                    metadata={}
                )
            
            # Handle adult site specific elements
            await self.handle_adult_site_elements(page)
            
            # Extract page metadata
            metadata = await self.extract_page_metadata(page)
            
            # Find images with intelligent filtering
            images = await self.extract_images_intelligent(page, max_images)
            
            # Filter and rank images by quality
            filtered_images = await self.filter_and_rank_images(images, page)
            
            await page.close()
            
            return ScrapingResult(
                status='success',
                message=f"Successfully scraped {len(filtered_images)} images",
                images=filtered_images,
                metadata=metadata,
                total_images_found=len(images),
                filtered_images=len(filtered_images),
                title=metadata.get('title'),
                model_name=metadata.get('model_name'),
                tags=metadata.get('tags', [])
            )
            
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {e}")
            return ScrapingResult(
                status='error',
                message=str(e),
                images=[],
                metadata={}
            )

    async def handle_adult_site_elements(self, page: Page):
        """Handle adult site specific elements like age verification"""
        try:
            # Wait for page to stabilize
            await page.wait_for_load_state('networkidle', timeout=5000)
            
            # Handle age verification modals/overlays
            if self.adult_site_config['bypass_age_verification']:
                age_selectors = [
                    'button:has-text("I am 18")',
                    'button:has-text("Yes")',
                    'button:has-text("Enter")', 
                    'button:has-text("Continue")',
                    'button:has-text("Agree")',
                    '.age-verify button',
                    '.modal-age button',
                    '#age-gate button',
                    '[data-age-verify] button'
                ]
                
                for selector in age_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=2000)
                        if element:
                            await element.click()
                            logger.info(f"Clicked age verification: {selector}")
                            await page.wait_for_timeout(1000)
                            break
                    except PlaywrightTimeoutError:
                        continue
            
            # Handle cookie banners
            if self.adult_site_config['handle_cookie_banners']:
                cookie_selectors = [
                    'button:has-text("Accept")',
                    'button:has-text("OK")',
                    'button:has-text("Got it")',
                    '.cookie-banner button',
                    '#cookie-banner button'
                ]
                
                for selector in cookie_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=2000)
                        if element:
                            await element.click()
                            logger.info(f"Clicked cookie banner: {selector}")
                            break
                    except PlaywrightTimeoutError:
                        continue
            
            # Wait for dynamic content to load
            if self.adult_site_config['wait_for_dynamic_content']:
                await page.wait_for_timeout(3000)
                
        except Exception as e:
            logger.warning(f"Error handling adult site elements: {e}")

    async def extract_page_metadata(self, page: Page) -> Dict[str, Any]:
        """Extract comprehensive page metadata"""
        try:
            metadata = {}
            
            # Basic page info
            metadata['url'] = page.url
            metadata['title'] = await page.title()
            
            # Meta tags
            meta_description = await page.get_attribute('meta[name="description"]', 'content')
            if meta_description:
                metadata['description'] = meta_description
            
            # Model/performer name extraction (adult site specific)
            model_selectors = [
                'h1.model-name',
                '.performer-name',
                '.model-title',
                'h1:contains("Model:")',
                '.page-title .model',
                '[data-model-name]'
            ]
            
            for selector in model_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=1000)
                    if element:
                        model_name = await element.inner_text()
                        metadata['model_name'] = model_name.strip()
                        break
                except PlaywrightTimeoutError:
                    continue
            
            # Extract tags
            tag_selectors = [
                '.tags a',
                '.tag-list .tag',
                '.categories a',
                '.keywords .keyword'
            ]
            
            tags = []
            for selector in tag_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements[:20]:  # Limit to 20 tags
                        tag_text = await element.inner_text()
                        tags.append(tag_text.strip())
                except:
                    continue
            
            metadata['tags'] = list(set(tags))  # Remove duplicates
            
            # Extract image count if available
            count_selectors = [
                '.image-count',
                '.photo-count',
                '.gallery-count'
            ]
            
            for selector in count_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=1000)
                    if element:
                        count_text = await element.inner_text()
                        # Extract number from text
                        import re
                        numbers = re.findall(r'\d+', count_text)
                        if numbers:
                            metadata['total_images'] = int(numbers[0])
                        break
                except:
                    continue
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {}

    async def extract_images_intelligent(self, page: Page, max_images: int) -> List[Dict[str, Any]]:
        """Extract images using intelligent selectors for adult sites"""
        try:
            images = []
            
            # Scroll to load lazy images if configured
            if self.adult_site_config['scroll_for_lazy_load']:
                await self.smart_scroll(page)
            
            # Multiple selector strategies for different adult site layouts
            image_selectors = [
                'img[src*="jpg"], img[src*="jpeg"], img[src*="png"], img[src*="webp"]',
                '.gallery img',
                '.photo-grid img',
                '.image-container img',
                '.thumbnail img',
                '.photo img',
                'a[href*=".jpg"] img, a[href*=".jpeg"] img, a[href*=".png"] img',
                '[data-src*="jpg"], [data-src*="jpeg"], [data-src*="png"], [data-src*="webp"]'
            ]
            
            for selector in image_selectors:
                try:
                    img_elements = await page.query_selector_all(selector)
                    logger.info(f"Found {len(img_elements)} images with selector: {selector}")
                    
                    for img in img_elements:
                        if len(images) >= max_images:
                            break
                            
                        # Extract image info
                        img_info = await self.extract_image_info(img, page)
                        if img_info and self.is_valid_image(img_info):
                            images.append(img_info)
                            
                    if images:  # If we found images with this selector, we can stop
                        break
                        
                except Exception as e:
                    logger.warning(f"Error with selector {selector}: {e}")
                    continue
            
            # Also check for high-res image links
            await self.find_high_res_links(page, images, max_images)
            
            return images[:max_images]
            
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
            return []

    async def smart_scroll(self, page: Page):
        """Smart scrolling to trigger lazy loading"""
        try:
            # Get page height
            page_height = await page.evaluate("document.body.scrollHeight")
            viewport_height = page.viewport_size['height']
            
            # Scroll in increments
            scroll_position = 0
            scroll_increment = viewport_height // 2
            
            while scroll_position < page_height:
                await page.evaluate(f"window.scrollTo(0, {scroll_position})")
                await page.wait_for_timeout(1000)  # Wait for images to load
                
                # Check if new images loaded
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height > page_height:
                    page_height = new_height
                    
                scroll_position += scroll_increment
                
        except Exception as e:
            logger.warning(f"Error during smart scroll: {e}")

    async def extract_image_info(self, img_element, page: Page) -> Optional[Dict[str, Any]]:
        """Extract comprehensive information about an image"""
        try:
            # Get image attributes
            src = await img_element.get_attribute('src')
            data_src = await img_element.get_attribute('data-src')
            alt = await img_element.get_attribute('alt') or ''
            title = await img_element.get_attribute('title') or ''
            
            # Use data-src if src is placeholder
            image_url = data_src or src
            if not image_url:
                return None
                
            # Resolve relative URLs
            if image_url.startswith('/'):
                base_url = await page.evaluate("window.location.origin")
                image_url = base_url + image_url
            elif not image_url.startswith('http'):
                image_url = urljoin(page.url, image_url)
            
            # Get dimensions if possible
            try:
                bbox = await img_element.bounding_box()
                width = int(bbox['width']) if bbox else None
                height = int(bbox['height']) if bbox else None
            except:
                width = height = None
                
            # Generate filename
            parsed_url = urlparse(image_url)
            filename = os.path.basename(parsed_url.path)
            if not filename or '.' not in filename:
                filename = hashlib.md5(image_url.encode()).hexdigest() + '.jpg'
            
            return {
                'url': image_url,
                'filename': filename,
                'alt_text': alt,
                'title': title,
                'width': width,
                'height': height,
                'element_info': {
                    'tag': await img_element.evaluate("el => el.tagName.toLowerCase()"),
                    'classes': await img_element.get_attribute('class') or '',
                    'parent_tag': await img_element.evaluate("el => el.parentElement?.tagName.toLowerCase()")
                }
            }
            
        except Exception as e:
            logger.warning(f"Error extracting image info: {e}")
            return None

    async def find_high_res_links(self, page: Page, images: List[Dict], max_images: int):
        """Find links to high resolution images"""
        try:
            if len(images) >= max_images:
                return
                
            # Look for links that might contain high-res images
            link_selectors = [
                'a[href*=".jpg"], a[href*=".jpeg"], a[href*=".png"], a[href*=".webp"]',
                'a[href*="full"], a[href*="large"], a[href*="original"]',
                '.gallery-link', '.photo-link', '.zoom-link'
            ]
            
            for selector in link_selectors:
                try:
                    links = await page.query_selector_all(selector)
                    for link in links:
                        if len(images) >= max_images:
                            break
                            
                        href = await link.get_attribute('href')
                        if href and any(ext in href.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                            # Resolve URL
                            if href.startswith('/'):
                                base_url = await page.evaluate("window.location.origin")
                                href = base_url + href
                            elif not href.startswith('http'):
                                href = urljoin(page.url, href)
                            
                            # Create image info
                            filename = os.path.basename(urlparse(href).path)
                            if not filename or '.' not in filename:
                                filename = hashlib.md5(href.encode()).hexdigest() + '.jpg'
                                
                            images.append({
                                'url': href,
                                'filename': filename,
                                'alt_text': await link.get_attribute('title') or '',
                                'title': await link.inner_text() or '',
                                'width': None,
                                'height': None,
                                'source': 'high_res_link'
                            })
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.warning(f"Error finding high-res links: {e}")

    def is_valid_image(self, img_info: Dict[str, Any]) -> bool:
        """Validate image based on quality filters"""
        try:
            url = img_info['url'].lower()
            
            # Check file format
            allowed_formats = self.image_filters['allowed_formats']
            if not any(fmt in url for fmt in allowed_formats):
                return False
                
            # Skip thumbnails and previews if configured
            if self.image_filters['skip_thumbnails']:
                thumbnail_indicators = ['thumb', 'preview', 'small', 'mini', 'tiny']
                if any(indicator in url for indicator in thumbnail_indicators):
                    return False
                    
            # Check dimensions if available
            width = img_info.get('width')
            height = img_info.get('height')
            
            if width and height:
                if width < self.image_filters['min_width'] or height < self.image_filters['min_height']:
                    return False
                    
            # Additional quality checks based on URL patterns
            quality_indicators = ['full', 'large', 'original', 'hd', 'high']
            has_quality_indicator = any(indicator in url for indicator in quality_indicators)
            
            return True
            
        except Exception as e:
            logger.warning(f"Error validating image: {e}")
            return False

    async def filter_and_rank_images(self, images: List[Dict], page: Page) -> List[Dict]:
        """Filter and rank images by quality and relevance"""
        try:
            scored_images = []
            
            for img in images:
                score = await self.calculate_image_score(img, page)
                if score > 0:
                    img['quality_score'] = score
                    scored_images.append(img)
            
            # Sort by quality score
            scored_images.sort(key=lambda x: x['quality_score'], reverse=True)
            
            # Remove duplicates based on URL or filename
            unique_images = []
            seen_urls = set()
            seen_filenames = set()
            
            for img in scored_images:
                url = img['url']
                filename = img['filename']
                
                if url not in seen_urls and filename not in seen_filenames:
                    unique_images.append(img)
                    seen_urls.add(url)
                    seen_filenames.add(filename)
            
            return unique_images
            
        except Exception as e:
            logger.error(f"Error filtering images: {e}")
            return images

    async def calculate_image_score(self, img_info: Dict, page: Page) -> float:
        """Calculate quality score for image ranking"""
        try:
            score = 0.0
            url = img_info['url'].lower()
            
            # Quality indicators in URL
            quality_keywords = {
                'original': 10, 'full': 8, 'large': 6, 'hd': 7, 'high': 5,
                'big': 4, 'xlarge': 9, 'xxlarge': 10
            }
            
            for keyword, points in quality_keywords.items():
                if keyword in url:
                    score += points
                    
            # Penalty for low-quality indicators
            low_quality_keywords = {
                'thumb': -10, 'preview': -8, 'small': -6, 'mini': -10,
                'tiny': -10, 'avatar': -5
            }
            
            for keyword, penalty in low_quality_keywords.items():
                if keyword in url:
                    score += penalty
                    
            # Dimension-based scoring
            width = img_info.get('width', 0)
            height = img_info.get('height', 0)
            
            if width and height:
                # Prefer larger images
                area_score = min((width * height) / 1000000, 10)  # Max 10 points for very large images
                score += area_score
                
                # Aspect ratio preference (not too extreme)
                aspect_ratio = max(width, height) / min(width, height)
                if 1.2 <= aspect_ratio <= 2.0:  # Good aspect ratios
                    score += 2
                elif aspect_ratio > 3:  # Very wide/tall images
                    score -= 3
                    
            # File format preference
            format_scores = {'.webp': 3, '.png': 2, '.jpg': 1, '.jpeg': 1}
            for ext, points in format_scores.items():
                if ext in url:
                    score += points
                    break
                    
            # URL structure scoring (shorter paths often mean higher quality)
            path_parts = urlparse(img_info['url']).path.split('/')
            if len(path_parts) <= 4:  # Simple path structure
                score += 2
                
            return max(score, 0)  # Ensure non-negative score
            
        except Exception as e:
            logger.warning(f"Error calculating image score: {e}")
            return 0.0

    async def download_image(self, image_info: Dict, download_path: Path) -> Dict[str, Any]:
        """Download image with professional error handling and validation"""
        try:
            url = image_info['url']
            filename = image_info['filename']
            file_path = download_path / filename
            
            # Create directory if not exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download with aiohttp for better control
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Validate file size
                        file_size_mb = len(content) / (1024 * 1024)
                        if file_size_mb > self.image_filters['max_file_size_mb']:
                            return {
                                'status': 'error',
                                'message': f'File too large: {file_size_mb:.1f}MB',
                                'url': url
                            }
                        
                        # Write file
                        with open(file_path, 'wb') as f:
                            f.write(content)
                        
                        # Generate file hash for deduplication
                        file_hash = hashlib.md5(content).hexdigest()
                        
                        return {
                            'status': 'success',
                            'url': url,
                            'file_path': str(file_path),
                            'file_size': len(content),
                            'hash_md5': file_hash
                        }
                    else:
                        return {
                            'status': 'error',
                            'message': f'HTTP {response.status}',
                            'url': url
                        }
                        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'url': image_info.get('url', 'unknown')
            }

    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


class PornPicsPlaywrightScraper(PlaywrightScraper):
    """Specialized Playwright scraper optimized for PornPics.com"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # PornPics-specific configurations
        self.site_specific = {
            'gallery_selectors': [
                '.gallery-item img',
                '.photo-container img', 
                '.image-gallery img',
                '.thumb img'
            ],
            'high_res_patterns': [
                'data-original',
                'data-full',
                'data-large'
            ],
            'pagination_selector': '.pagination a',
            'model_name_selector': 'h1.model-name, .performer-name'
        }

    async def extract_images_intelligent(self, page: Page, max_images: int) -> List[Dict[str, Any]]:
        """PornPics-specific image extraction"""
        try:
            images = []
            
            # Handle pagination if needed
            await self.handle_pagination(page, max_images)
            
            # PornPics-specific selectors
            for selector in self.site_specific['gallery_selectors']:
                try:
                    img_elements = await page.query_selector_all(selector)
                    logger.info(f"PornPics: Found {len(img_elements)} images with {selector}")
                    
                    for img in img_elements:
                        if len(images) >= max_images:
                            break
                            
                        # Check for high-res versions
                        high_res_url = None
                        for pattern in self.site_specific['high_res_patterns']:
                            high_res_url = await img.get_attribute(pattern)
                            if high_res_url:
                                break
                        
                        # Extract standard image info
                        img_info = await self.extract_image_info(img, page)
                        if img_info:
                            # Replace with high-res URL if available
                            if high_res_url and high_res_url.startswith('http'):
                                img_info['url'] = high_res_url
                                img_info['source'] = 'high_res'
                            
                            if self.is_valid_image(img_info):
                                images.append(img_info)
                                
                    if images:
                        break
                        
                except Exception as e:
                    logger.warning(f"PornPics selector error {selector}: {e}")
                    continue
                    
            return images[:max_images]
            
        except Exception as e:
            logger.error(f"PornPics image extraction error: {e}")
            return []

    async def handle_pagination(self, page: Page, max_images: int):
        """Handle pagination for multi-page galleries"""
        try:
            # Check if pagination exists
            pagination_links = await page.query_selector_all(self.site_specific['pagination_selector'])
            
            if not pagination_links:
                return
                
            logger.info(f"Found {len(pagination_links)} pagination links")
            
            # For now, just scroll to load more content
            # In production, you might want to actually navigate pages
            await self.smart_scroll(page)
            
        except Exception as e:
            logger.warning(f"Error handling pagination: {e}")
