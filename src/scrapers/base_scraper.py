#!/usr/bin/env python3
"""
Base Scraper Implementation
Abstract base class for all website scrapers
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import requests
import time
import logging
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import asyncio

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for website scrapers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = requests.Session()
        self.setup_session()
        self.rate_limit_delay = config.get('delay', 1)
        self.max_retries = config.get('max_retries', 3)
        
    def setup_session(self):
        """Setup HTTP session with proper headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def check_robots_txt(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt"""
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            user_agent = self.session.headers.get('User-Agent', '*')
            return rp.can_fetch(user_agent, url)
            
        except Exception as e:
            logger.warning(f"Could not check robots.txt for {url}: {e}")
            return False
    
    def respect_rate_limits(self):
        """Implement rate limiting"""
        time.sleep(self.rate_limit_delay)
    
    def safe_request(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Make a safe HTTP request with retries"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=30, **kwargs)
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        return None
    
    def extract_images_from_soup(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Extract image URLs from BeautifulSoup object"""
        images = []
        
        # Find all img tags
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if not src:
                continue
                
            # Convert relative URLs to absolute
            if src.startswith('//'):
                src = f"https:{src}"
            elif src.startswith('/'):
                src = urljoin(base_url, src)
            elif not src.startswith(('http://', 'https://')):
                src = urljoin(base_url, src)
            
            # Get additional attributes
            alt_text = img.get('alt', '')
            title = img.get('title', '')
            width = img.get('width')
            height = img.get('height')
            
            images.append({
                'url': src,
                'alt': alt_text,
                'title': title,
                'width': width,
                'height': height,
                'filename': self.generate_filename(src)
            })
        
        return images
    
    def generate_filename(self, url: str) -> str:
        """Generate filename from URL"""
        parsed = urlparse(url)
        filename = parsed.path.split('/')[-1]
        
        if not filename or '.' not in filename:
            filename = f"image_{int(time.time())}.jpg"
            
        return filename
    
    def filter_images(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter images based on quality criteria"""
        filtered = []
        
        for img in images:
            url = img['url']
            
            # Skip small images (likely icons/thumbnails)
            if any(keyword in url.lower() for keyword in ['icon', 'logo', 'thumb', 'avatar']):
                continue
                
            # Skip common non-content extensions
            if any(url.lower().endswith(ext) for ext in ['.gif', '.svg']):
                continue
            
            # Check image dimensions if available
            width = img.get('width')
            height = img.get('height')
            
            if width and height:
                try:
                    w, h = int(width), int(height)
                    if w < 200 or h < 200:  # Skip small images
                        continue
                except ValueError:
                    pass
            
            filtered.append(img)
        
        return filtered
    
    @abstractmethod
    async def scrape_url(self, url: str, max_images: int = 50) -> Dict[str, Any]:
        """Scrape images from a URL - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> List[str]:
        """Search for URLs - must be implemented by subclasses"""
        pass


class GenericScraper(BaseScraper):
    """Generic scraper for any website"""
    
    async def scrape_url(self, url: str, max_images: int = 50) -> Dict[str, Any]:
        """Scrape images from any URL"""
        try:
            # Check robots.txt first
            if not self.check_robots_txt(url):
                return {
                    'url': url,
                    'status': 'blocked',
                    'message': 'Blocked by robots.txt',
                    'images': []
                }
            
            # Make request
            response = self.safe_request(url)
            if not response:
                return {
                    'url': url,
                    'status': 'error',
                    'message': 'Failed to fetch page',
                    'images': []
                }
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract page metadata
            title = soup.find('title')
            title_text = title.get_text().strip() if title else 'Unknown'
            
            # Extract images
            all_images = self.extract_images_from_soup(soup, url)
            filtered_images = self.filter_images(all_images)
            
            # Limit number of images
            final_images = filtered_images[:max_images]
            
            self.respect_rate_limits()
            
            return {
                'url': url,
                'status': 'success',
                'title': title_text,
                'total_images_found': len(all_images),
                'filtered_images': len(filtered_images),
                'images': final_images,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {
                'url': url,
                'status': 'error',
                'message': str(e),
                'images': []
            }
    
    async def search(self, query: str, limit: int = 20) -> List[str]:
        """Generic search - not implemented"""
        logger.warning("Generic search not implemented")
        return []


class PornPicsScraper(BaseScraper):
    """
    Scraper for PornPics.com
    Educational/Research purposes only - always respect ToS
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = "https://www.pornpics.com"
    
    async def scrape_url(self, url: str, max_images: int = 50) -> Dict[str, Any]:
        """Scrape images from PornPics URL"""
        try:
            # Check if this looks like a PornPics URL
            if 'pornpics.com' not in url.lower():
                return {
                    'url': url,
                    'status': 'error',
                    'message': 'Not a PornPics.com URL',
                    'images': []
                }
            
            # Check robots.txt
            if not self.check_robots_txt(url):
                return {
                    'url': url,
                    'status': 'blocked',
                    'message': 'Blocked by robots.txt',
                    'images': []
                }
            
            # Make request
            response = self.safe_request(url)
            if not response:
                return {
                    'url': url,
                    'status': 'error', 
                    'message': 'Failed to fetch page',
                    'images': []
                }
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract page info
            title = self.extract_page_title(soup)
            model_name = self.extract_model_name(soup)
            tags = self.extract_tags(soup)
            
            # Extract images (PornPics specific selectors)
            images = self.extract_pornpics_images(soup, url)
            filtered_images = self.filter_images(images)
            final_images = filtered_images[:max_images]
            
            self.respect_rate_limits()
            
            return {
                'url': url,
                'status': 'success',
                'title': title,
                'model_name': model_name,
                'tags': tags,
                'total_images_found': len(images),
                'filtered_images': len(filtered_images),
                'images': final_images,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error scraping PornPics URL {url}: {e}")
            return {
                'url': url,
                'status': 'error',
                'message': str(e),
                'images': []
            }
    
    def extract_page_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_elem = soup.find('title')
        if title_elem:
            return title_elem.get_text().strip()
        
        # Try h1 as backup
        h1_elem = soup.find('h1')
        if h1_elem:
            return h1_elem.get_text().strip()
            
        return 'Unknown'
    
    def extract_model_name(self, soup: BeautifulSoup) -> str:
        """Extract model name from page"""
        # Try different selectors for model name
        selectors = [
            '.model-name',
            '.pornstar-name', 
            'h1',
            '.title'
        ]
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                name = elem.get_text().strip()
                if name and len(name) < 100:  # Reasonable name length
                    return name
        
        return 'Unknown'
    
    def extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract tags from page"""
        tags = []
        
        # Look for tag elements
        tag_selectors = [
            '.tags a',
            '.tag',
            '.category a'
        ]
        
        for selector in tag_selectors:
            elements = soup.select(selector)
            for elem in elements:
                tag_text = elem.get_text().strip()
                if tag_text and tag_text not in tags:
                    tags.append(tag_text)
        
        return tags[:10]  # Limit number of tags
    
    def extract_pornpics_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Extract images using PornPics-specific selectors"""
        images = []
        
        # Try multiple selectors for PornPics images
        image_selectors = [
            '.thumbs img',
            '.gallery-item img',
            '.photo img',
            'img[data-src]',
            'img[src*="jpg"]',
            'img[src*="jpeg"]'
        ]
        
        for selector in image_selectors:
            img_elements = soup.select(selector)
            
            for img in img_elements:
                src = img.get('data-src') or img.get('src')
                if not src:
                    continue
                
                # Convert to absolute URL
                if src.startswith('//'):
                    src = f"https:{src}"
                elif src.startswith('/'):
                    src = urljoin(base_url, src)
                elif not src.startswith(('http://', 'https://')):
                    src = urljoin(base_url, src)
                
                # Get image info
                alt_text = img.get('alt', '')
                title = img.get('title', '')
                
                images.append({
                    'url': src,
                    'alt': alt_text,
                    'title': title,
                    'filename': self.generate_filename(src)
                })
        
        # Remove duplicates
        seen = set()
        unique_images = []
        for img in images:
            if img['url'] not in seen:
                seen.add(img['url'])
                unique_images.append(img)
        
        return unique_images
    
    async def search(self, query: str, limit: int = 20) -> List[str]:
        """Search for models/galleries on PornPics"""
        try:
            search_url = f"{self.base_url}/search/?q={query.replace(' ', '+')}"
            
            response = self.safe_request(search_url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract result URLs
            urls = []
            
            # Look for gallery/model links
            link_selectors = [
                'a[href*="/galleries/"]',
                'a[href*="/models/"]',
                'a[href*="/pornstars/"]'
            ]
            
            for selector in link_selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href:
                        if href.startswith('/'):
                            full_url = urljoin(self.base_url, href)
                        else:
                            full_url = href
                        
                        if full_url not in urls:
                            urls.append(full_url)
                            
                        if len(urls) >= limit:
                            break
                
                if len(urls) >= limit:
                    break
            
            self.respect_rate_limits()
            return urls[:limit]
            
        except Exception as e:
            logger.error(f"Error searching PornPics: {e}")
            return []
