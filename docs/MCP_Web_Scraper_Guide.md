# 🚀 MCP Web Scraper - Complete Setup Guide

## Overview
This guide will help you create a Model Context Protocol (MCP) server for automated web scraping, image collection, and intelligent categorization for AI training datasets.

## 🎯 Project Goals
1. **Web Scraping**: Extract images from websites (Instagram, PornPics, etc.)
2. **Auto-Categorization**: Organize images by person/category
3. **Legal Compliance**: Ensure proper attribution and licensing
4. **Quality Control**: Filter and validate collected data
5. **MCP Integration**: Provide structured data through MCP protocol

## 📋 Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [MCP Server Setup](#mcp-server-setup)
3. [Scraping Components](#scraping-components)
4. [Auto-Categorization System](#auto-categorization-system)
5. [Legal & Ethical Guidelines](#legal--ethical-guidelines)
6. [Implementation Workflow](#implementation-workflow)
7. [Testing & Validation](#testing--validation)

---

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │◄──►│   MCP Server    │◄──►│  Web Scrapers   │
│   (VS Code)     │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                               ▼
                    ┌─────────────────┐
                    │  Categorization │
                    │     Engine      │
                    └─────────────────┘
                               │
                               ▼
                    ┌─────────────────┐
                    │   Data Storage  │
                    │   & Metadata    │
                    └─────────────────┘
```

### Core Components:
- **MCP Server**: Handles client requests and coordinates scraping
- **Web Scrapers**: Modular scrapers for different websites
- **Categorization Engine**: AI-powered image classification
- **Storage Manager**: Organized file system with metadata
- **Legal Compliance**: Attribution and licensing tracking

---

## 🛠️ MCP Server Setup

### 1. Project Structure
```
mcp-web-scraper/
├── src/
│   ├── server.py           # Main MCP server
│   ├── scrapers/           # Website-specific scrapers
│   │   ├── __init__.py
│   │   ├── instagram.py
│   │   ├── pornpics.py
│   │   └── base_scraper.py
│   ├── categorization/     # Auto-categorization
│   │   ├── __init__.py
│   │   ├── face_detector.py
│   │   ├── person_classifier.py
│   │   └── category_manager.py
│   ├── storage/           # Data management
│   │   ├── __init__.py
│   │   ├── file_manager.py
│   │   └── metadata_manager.py
│   └── utils/             # Utilities
│       ├── __init__.py
│       ├── legal_checker.py
│       └── quality_filter.py
├── config/
│   ├── scraper_config.json
│   └── mcp_config.json
├── data/
│   ├── raw/              # Downloaded images
│   ├── processed/        # Filtered images
│   ├── categorized/      # Organized by person/category
│   └── metadata/         # JSON metadata files
├── requirements.txt
├── README.md
└── setup.py
```

### 2. Dependencies
```python
# requirements.txt
mcp>=0.5.0
fastapi>=0.104.0
uvicorn>=0.24.0
requests>=2.31.0
beautifulsoup4>=4.12.0
selenium>=4.15.0
opencv-python>=4.8.0
face-recognition>=1.3.0
numpy>=1.24.0
Pillow>=10.0.0
torch>=2.1.0
torchvision>=0.16.0
transformers>=4.35.0
scikit-learn>=1.3.0
tqdm>=4.66.0
python-dotenv>=1.0.0
aiohttp>=3.9.0
asyncio-mqtt>=0.16.0
```

---

## 🌐 Scraping Components

### Base Scraper Class
```python
# src/scrapers/base_scraper.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import time
import logging

class BaseScraper(ABC):
    def __init__(self, config: Dict):
        self.config = config
        self.session = requests.Session()
        self.setup_session()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def setup_session(self):
        """Setup session with headers and proxies"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    @abstractmethod
    async def scrape_profile(self, profile_url: str) -> Dict:
        """Scrape a specific profile/page"""
        pass
    
    @abstractmethod
    async def search_profiles(self, query: str, limit: int = 100) -> List[str]:
        """Search for profiles matching query"""
        pass
    
    @abstractmethod
    async def get_images(self, profile_data: Dict) -> List[Dict]:
        """Extract images from profile data"""
        pass
    
    def respect_rate_limits(self):
        """Implement rate limiting"""
        time.sleep(self.config.get('delay', 1))
    
    def validate_image_url(self, url: str) -> bool:
        """Validate image URL"""
        try:
            response = requests.head(url, timeout=10)
            return response.status_code == 200
        except:
            return False
```

### Instagram Scraper (Public Content Only)
```python
# src/scrapers/instagram.py
from .base_scraper import BaseScraper
import json
import re

class InstagramScraper(BaseScraper):
    """
    IMPORTANT: Only scrapes public content that's legally accessible
    Always check Instagram's Terms of Service and respect robots.txt
    """
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.base_url = "https://www.instagram.com"
    
    async def scrape_profile(self, profile_url: str) -> Dict:
        """Scrape public Instagram profile"""
        try:
            # Check if profile is public
            if not self.is_public_profile(profile_url):
                self.logger.warning(f"Profile is private: {profile_url}")
                return {}
            
            response = self.session.get(f"{profile_url}?__a=1")
            if response.status_code != 200:
                return {}
            
            data = response.json()
            profile_data = {
                'username': data['graphql']['user']['username'],
                'full_name': data['graphql']['user']['full_name'],
                'bio': data['graphql']['user']['biography'],
                'followers': data['graphql']['user']['edge_followed_by']['count'],
                'posts_count': data['graphql']['user']['edge_owner_to_timeline_media']['count'],
                'is_verified': data['graphql']['user']['is_verified'],
                'profile_pic': data['graphql']['user']['profile_pic_url_hd'],
                'posts': []
            }
            
            # Get recent posts
            posts = data['graphql']['user']['edge_owner_to_timeline_media']['edges']
            for post in posts[:self.config.get('max_posts', 50)]:
                post_data = self.extract_post_data(post['node'])
                if post_data:
                    profile_data['posts'].append(post_data)
            
            self.respect_rate_limits()
            return profile_data
            
        except Exception as e:
            self.logger.error(f"Error scraping profile {profile_url}: {e}")
            return {}
    
    def is_public_profile(self, profile_url: str) -> bool:
        """Check if profile is public"""
        # Implementation to check profile privacy
        # Return False for private profiles
        pass
    
    def extract_post_data(self, post_node: Dict) -> Dict:
        """Extract relevant data from post"""
        return {
            'id': post_node['id'],
            'shortcode': post_node['shortcode'],
            'caption': post_node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', ''),
            'like_count': post_node['edge_liked_by']['count'],
            'comment_count': post_node['edge_media_to_comment']['count'],
            'timestamp': post_node['taken_at_timestamp'],
            'image_url': post_node['display_url'],
            'is_video': post_node['is_video'],
            'dimensions': {
                'height': post_node['dimensions']['height'],
                'width': post_node['dimensions']['width']
            }
        }
```

### PornPics Scraper
```python
# src/scrapers/pornpics.py
from .base_scraper import BaseScraper
from urllib.parse import urljoin, urlparse
import re

class PornPicsScraper(BaseScraper):
    """
    Scraper for PornPics.com
    WARNING: This is for educational purposes only
    Always respect website terms of service and applicable laws
    """
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.base_url = "https://www.pornpics.com"
    
    async def scrape_profile(self, profile_url: str) -> Dict:
        """Scrape profile/model page"""
        try:
            response = self.session.get(profile_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract profile information
            profile_data = {
                'url': profile_url,
                'name': self.extract_model_name(soup),
                'description': self.extract_description(soup),
                'tags': self.extract_tags(soup),
                'galleries': self.extract_galleries(soup)
            }
            
            self.respect_rate_limits()
            return profile_data
            
        except Exception as e:
            self.logger.error(f"Error scraping profile {profile_url}: {e}")
            return {}
    
    async def search_profiles(self, query: str, limit: int = 100) -> List[str]:
        """Search for models/profiles"""
        try:
            search_url = f"{self.base_url}/search/?q={query}"
            response = self.session.get(search_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            profile_links = []
            for link in soup.find_all('a', href=re.compile(r'/models/')):
                full_url = urljoin(self.base_url, link.get('href'))
                if full_url not in profile_links:
                    profile_links.append(full_url)
                    if len(profile_links) >= limit:
                        break
            
            return profile_links
            
        except Exception as e:
            self.logger.error(f"Error searching profiles: {e}")
            return []
    
    def extract_model_name(self, soup):
        """Extract model name from page"""
        name_elem = soup.find('h1')
        return name_elem.get_text().strip() if name_elem else "Unknown"
    
    def extract_description(self, soup):
        """Extract description/bio"""
        desc_elem = soup.find('div', class_='description')
        return desc_elem.get_text().strip() if desc_elem else ""
    
    def extract_tags(self, soup):
        """Extract tags/categories"""
        tags = []
        for tag_elem in soup.find_all('a', class_='tag'):
            tags.append(tag_elem.get_text().strip())
        return tags
    
    def extract_galleries(self, soup):
        """Extract gallery URLs"""
        galleries = []
        for gallery_link in soup.find_all('a', href=re.compile(r'/galleries/')):
            gallery_url = urljoin(self.base_url, gallery_link.get('href'))
            galleries.append({
                'url': gallery_url,
                'title': gallery_link.get('title', ''),
                'thumbnail': gallery_link.find('img').get('src') if gallery_link.find('img') else None
            })
        return galleries
```

---

## 🤖 Auto-Categorization System

### Face Detection & Recognition
```python
# src/categorization/face_detector.py
import face_recognition
import cv2
import numpy as np
from typing import List, Dict, Tuple

class FaceDetector:
    def __init__(self, config: Dict):
        self.config = config
        self.known_faces = {}  # person_id -> face_encodings
        self.face_threshold = config.get('face_threshold', 0.6)
    
    def detect_faces(self, image_path: str) -> List[Dict]:
        """Detect all faces in image"""
        image = face_recognition.load_image_file(image_path)
        face_locations = face_recognition.face_locations(image)
        face_encodings = face_recognition.face_encodings(image, face_locations)
        
        faces = []
        for i, (encoding, location) in enumerate(zip(face_encodings, face_locations)):
            faces.append({
                'id': i,
                'encoding': encoding,
                'location': location,  # (top, right, bottom, left)
                'confidence': 1.0
            })
        
        return faces
    
    def identify_person(self, face_encoding: np.ndarray) -> Tuple[str, float]:
        """Identify person from face encoding"""
        if not self.known_faces:
            return "unknown", 0.0
        
        best_match_id = None
        best_distance = float('inf')
        
        for person_id, known_encodings in self.known_faces.items():
            distances = face_recognition.face_distance(known_encodings, face_encoding)
            min_distance = min(distances)
            
            if min_distance < best_distance:
                best_distance = min_distance
                best_match_id = person_id
        
        if best_distance < self.face_threshold:
            confidence = 1.0 - best_distance
            return best_match_id, confidence
        else:
            return "unknown", 0.0
    
    def add_known_person(self, person_id: str, face_encodings: List[np.ndarray]):
        """Add known person with face encodings"""
        self.known_faces[person_id] = face_encodings
    
    def learn_from_folder(self, folder_path: str, person_id: str):
        """Learn faces from a folder of images"""
        import os
        from pathlib import Path
        
        encodings = []
        folder = Path(folder_path)
        
        for image_file in folder.glob('*.{jpg,jpeg,png}'):
            try:
                image = face_recognition.load_image_file(str(image_file))
                face_encodings = face_recognition.face_encodings(image)
                if face_encodings:
                    encodings.extend(face_encodings)
            except Exception as e:
                print(f"Error processing {image_file}: {e}")
        
        if encodings:
            self.add_known_person(person_id, encodings)
            return len(encodings)
        return 0
```

### Category Manager
```python
# src/categorization/category_manager.py
from typing import Dict, List, Optional
import json
from pathlib import Path
import shutil

class CategoryManager:
    def __init__(self, config: Dict):
        self.config = config
        self.base_path = Path(config['categorized_path'])
        self.categories = self.load_categories()
        self.setup_directories()
    
    def setup_directories(self):
        """Create category directories"""
        for category in self.categories.keys():
            category_path = self.base_path / category
            category_path.mkdir(parents=True, exist_ok=True)
    
    def load_categories(self) -> Dict:
        """Load category configuration"""
        return {
            "people": {
                "unknown": {"path": "people/unknown", "description": "Unidentified persons"},
                "verified": {"path": "people/verified", "description": "Verified identity"}
            },
            "content_type": {
                "portrait": {"path": "content/portraits", "description": "Portrait photos"},
                "full_body": {"path": "content/full_body", "description": "Full body photos"},
                "group": {"path": "content/group", "description": "Multiple people"},
                "artistic": {"path": "content/artistic", "description": "Artistic content"}
            },
            "quality": {
                "high": {"path": "quality/high", "description": "High quality images"},
                "medium": {"path": "quality/medium", "description": "Medium quality images"},
                "low": {"path": "quality/low", "description": "Low quality images"}
            }
        }
    
    def categorize_image(self, image_path: str, metadata: Dict) -> str:
        """Categorize image and move to appropriate folder"""
        # Determine person category
        person_id = metadata.get('person_id', 'unknown')
        if person_id != 'unknown':
            person_category = f"people/{person_id}"
        else:
            person_category = "people/unknown"
        
        # Create person directory
        person_path = self.base_path / person_category
        person_path.mkdir(parents=True, exist_ok=True)
        
        # Move image
        image_file = Path(image_path)
        destination = person_path / image_file.name
        
        # Avoid overwrite
        counter = 1
        while destination.exists():
            stem = image_file.stem
            suffix = image_file.suffix
            destination = person_path / f"{stem}_{counter}{suffix}"
            counter += 1
        
        shutil.copy2(image_path, destination)
        
        # Save metadata
        metadata_file = destination.with_suffix('.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        return str(destination)
    
    def get_statistics(self) -> Dict:
        """Get categorization statistics"""
        stats = {}
        
        for category_type, categories in self.categories.items():
            stats[category_type] = {}
            for category_name, category_info in categories.items():
                category_path = self.base_path / category_info['path']
                if category_path.exists():
                    image_count = len(list(category_path.glob('*.{jpg,jpeg,png}')))
                    stats[category_type][category_name] = image_count
                else:
                    stats[category_type][category_name] = 0
        
        return stats
```

---

## ⚖️ Legal & Ethical Guidelines

### Legal Compliance Checker
```python
# src/utils/legal_checker.py
from typing import Dict, List, Optional
import requests
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse

class LegalComplianceChecker:
    def __init__(self, config: Dict):
        self.config = config
        self.robots_cache = {}
    
    def check_robots_txt(self, url: str, user_agent: str = '*') -> bool:
        """Check if URL is allowed by robots.txt"""
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            if robots_url not in self.robots_cache:
                rp = RobotFileParser()
                rp.set_url(robots_url)
                rp.read()
                self.robots_cache[robots_url] = rp
            
            return self.robots_cache[robots_url].can_fetch(user_agent, url)
        except:
            return False
    
    def check_terms_of_service(self, domain: str) -> Dict:
        """Check ToS compliance for domain"""
        tos_rules = {
            "instagram.com": {
                "allowed": False,
                "reason": "Instagram ToS prohibits automated data collection",
                "legal_alternatives": ["Instagram Basic Display API", "Instagram Graph API"]
            },
            "pornpics.com": {
                "allowed": True,
                "conditions": ["Non-commercial use", "Attribution required", "Rate limiting"],
                "restrictions": ["No bulk downloading", "Respect robots.txt"]
            }
        }
        
        return tos_rules.get(domain, {
            "allowed": None,
            "reason": "Terms of Service need manual review",
            "recommendation": "Contact website owner for permissions"
        })
    
    def generate_attribution(self, source_data: Dict) -> str:
        """Generate proper attribution text"""
        source_url = source_data.get('source_url', '')
        source_name = source_data.get('source_name', 'Unknown')
        author = source_data.get('author', 'Unknown')
        license_type = source_data.get('license', 'Unknown')
        
        attribution = f"Source: {source_name} ({source_url})\n"
        attribution += f"Author: {author}\n"
        attribution += f"License: {license_type}\n"
        attribution += f"Retrieved: {source_data.get('timestamp', 'Unknown')}"
        
        return attribution
    
    def validate_image_license(self, image_metadata: Dict) -> bool:
        """Validate if image can be used for AI training"""
        license_type = image_metadata.get('license', '').lower()
        
        # Check for AI-training friendly licenses
        allowed_licenses = [
            'creative commons',
            'public domain',
            'ai training permitted',
            'commercial use allowed'
        ]
        
        for allowed in allowed_licenses:
            if allowed in license_type:
                return True
        
        return False
```

---

## 🖥️ MCP Server Implementation

### Main Server
```python
# src/server.py
import asyncio
from typing import Any, Sequence
import logging

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from scrapers import InstagramScraper, PornPicsScraper
from categorization import FaceDetector, CategoryManager
from storage import FileManager, MetadataManager
from utils import LegalComplianceChecker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-web-scraper")

class WebScraperMCPServer:
    def __init__(self, config: dict):
        self.config = config
        self.server = Server("web-scraper")
        self.scrapers = {
            'instagram': InstagramScraper(config.get('instagram', {})),
            'pornpics': PornPicsScraper(config.get('pornpics', {}))
        }
        self.face_detector = FaceDetector(config.get('face_detection', {}))
        self.category_manager = CategoryManager(config.get('categorization', {}))
        self.file_manager = FileManager(config.get('storage', {}))
        self.metadata_manager = MetadataManager(config.get('metadata', {}))
        self.legal_checker = LegalComplianceChecker(config.get('legal', {}))
        
        self.setup_tools()
    
    def setup_tools(self):
        """Setup MCP tools"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            return [
                types.Tool(
                    name="scrape_profile",
                    description="Scrape a profile/page from supported websites",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "website": {"type": "string", "enum": ["instagram", "pornpics"]},
                            "profile_url": {"type": "string"},
                            "max_images": {"type": "integer", "default": 50}
                        },
                        "required": ["website", "profile_url"]
                    }
                ),
                types.Tool(
                    name="search_profiles",
                    description="Search for profiles on supported websites",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "website": {"type": "string", "enum": ["instagram", "pornpics"]},
                            "query": {"type": "string"},
                            "limit": {"type": "integer", "default": 20}
                        },
                        "required": ["website", "query"]
                    }
                ),
                types.Tool(
                    name="categorize_images",
                    description="Automatically categorize downloaded images",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "input_folder": {"type": "string"},
                            "learn_faces": {"type": "boolean", "default": True}
                        },
                        "required": ["input_folder"]
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
                    description="Check legal compliance for a website/URL",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {"type": "string"},
                            "check_robots": {"type": "boolean", "default": True},
                            "check_tos": {"type": "boolean", "default": True}
                        },
                        "required": ["url"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict | None
        ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            
            if name == "scrape_profile":
                return await self.handle_scrape_profile(arguments)
            elif name == "search_profiles":
                return await self.handle_search_profiles(arguments)
            elif name == "categorize_images":
                return await self.handle_categorize_images(arguments)
            elif name == "get_statistics":
                return await self.handle_get_statistics(arguments)
            elif name == "check_legal_compliance":
                return await self.handle_check_legal_compliance(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def handle_scrape_profile(self, arguments: dict) -> list[types.TextContent]:
        """Handle profile scraping request"""
        try:
            website = arguments['website']
            profile_url = arguments['profile_url']
            max_images = arguments.get('max_images', 50)
            
            # Check legal compliance first
            legal_check = self.legal_checker.check_robots_txt(profile_url)
            if not legal_check:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Legal compliance check failed for {profile_url}. Check robots.txt and ToS."
                )]
            
            # Get scraper
            scraper = self.scrapers.get(website)
            if not scraper:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Unsupported website: {website}"
                )]
            
            # Scrape profile
            logger.info(f"Scraping profile: {profile_url}")
            profile_data = await scraper.scrape_profile(profile_url)
            
            if not profile_data:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Failed to scrape profile: {profile_url}"
                )]
            
            # Extract and download images
            images = await scraper.get_images(profile_data)
            downloaded_count = 0
            
            for image_data in images[:max_images]:
                try:
                    # Download image
                    image_path = await self.file_manager.download_image(
                        image_data['url'], 
                        image_data.get('filename')
                    )
                    
                    # Save metadata
                    metadata = {
                        'source_url': profile_url,
                        'image_url': image_data['url'],
                        'local_path': image_path,
                        'profile_data': profile_data,
                        'scraping_timestamp': time.time()
                    }
                    
                    await self.metadata_manager.save_metadata(image_path, metadata)
                    downloaded_count += 1
                    
                except Exception as e:
                    logger.error(f"Error downloading image {image_data['url']}: {e}")
            
            result_text = f"✅ Successfully scraped {profile_data.get('name', 'profile')}\n"
            result_text += f"📥 Downloaded {downloaded_count}/{len(images)} images\n"
            result_text += f"👤 Profile: {profile_data.get('name', 'Unknown')}\n"
            result_text += f"📊 Total posts: {len(profile_data.get('posts', []))}\n"
            
            return [types.TextContent(type="text", text=result_text)]
            
        except Exception as e:
            logger.error(f"Error in scrape_profile: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Error scraping profile: {str(e)}"
            )]
    
    async def handle_categorize_images(self, arguments: dict) -> list[types.TextContent]:
        """Handle image categorization request"""
        try:
            input_folder = arguments['input_folder']
            learn_faces = arguments.get('learn_faces', True)
            
            # Get all images in folder
            image_files = self.file_manager.get_images_in_folder(input_folder)
            
            categorized_count = 0
            face_learned_count = 0
            
            for image_path in image_files:
                try:
                    # Load existing metadata
                    metadata = await self.metadata_manager.load_metadata(image_path)
                    
                    # Detect faces
                    faces = self.face_detector.detect_faces(image_path)
                    
                    # Identify persons
                    for face in faces:
                        person_id, confidence = self.face_detector.identify_person(face['encoding'])
                        face['person_id'] = person_id
                        face['confidence'] = confidence
                    
                    # Update metadata
                    metadata['faces'] = faces
                    metadata['primary_person'] = faces[0]['person_id'] if faces else 'unknown'
                    
                    # Categorize image
                    new_path = self.category_manager.categorize_image(image_path, metadata)
                    
                    # Update metadata with new path
                    metadata['categorized_path'] = new_path
                    await self.metadata_manager.save_metadata(new_path, metadata)
                    
                    categorized_count += 1
                    
                    # Learn faces if requested
                    if learn_faces and faces:
                        for face in faces:
                            if face['person_id'] == 'unknown':
                                # Create new person ID
                                new_person_id = f"person_{int(time.time())}_{face['id']}"
                                self.face_detector.add_known_person(new_person_id, [face['encoding']])
                                face_learned_count += 1
                    
                except Exception as e:
                    logger.error(f"Error categorizing {image_path}: {e}")
            
            result_text = f"✅ Categorization complete!\n"
            result_text += f"📁 Processed: {len(image_files)} images\n"
            result_text += f"🏷️ Categorized: {categorized_count} images\n"
            result_text += f"👥 New faces learned: {face_learned_count}\n"
            
            # Add statistics
            stats = self.category_manager.get_statistics()
            result_text += f"\n📊 Category Statistics:\n"
            for category_type, categories in stats.items():
                result_text += f"  {category_type.title()}:\n"
                for category_name, count in categories.items():
                    result_text += f"    - {category_name}: {count} images\n"
            
            return [types.TextContent(type="text", text=result_text)]
            
        except Exception as e:
            logger.error(f"Error in categorize_images: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Error categorizing images: {str(e)}"
            )]
    
    async def handle_check_legal_compliance(self, arguments: dict) -> list[types.TextContent]:
        """Handle legal compliance check"""
        try:
            url = arguments['url']
            check_robots = arguments.get('check_robots', True)
            check_tos = arguments.get('check_tos', True)
            
            result_text = f"🔍 Legal Compliance Check for: {url}\n\n"
            
            if check_robots:
                robots_allowed = self.legal_checker.check_robots_txt(url)
                result_text += f"🤖 Robots.txt: {'✅ Allowed' if robots_allowed else '❌ Blocked'}\n"
            
            if check_tos:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                tos_info = self.legal_checker.check_terms_of_service(domain)
                
                result_text += f"📋 Terms of Service:\n"
                if tos_info.get('allowed') is True:
                    result_text += f"  ✅ Generally allowed\n"
                    if 'conditions' in tos_info:
                        result_text += f"  📝 Conditions: {', '.join(tos_info['conditions'])}\n"
                    if 'restrictions' in tos_info:
                        result_text += f"  ⚠️ Restrictions: {', '.join(tos_info['restrictions'])}\n"
                elif tos_info.get('allowed') is False:
                    result_text += f"  ❌ Not allowed\n"
                    result_text += f"  📝 Reason: {tos_info.get('reason', 'Unknown')}\n"
                    if 'legal_alternatives' in tos_info:
                        result_text += f"  🔄 Alternatives: {', '.join(tos_info['legal_alternatives'])}\n"
                else:
                    result_text += f"  ⚠️ Requires manual review\n"
                    result_text += f"  📝 {tos_info.get('reason', 'Terms need to be reviewed manually')}\n"
                    result_text += f"  💡 {tos_info.get('recommendation', 'Contact website owner')}\n"
            
            # General recommendations
            result_text += f"\n💡 General Recommendations:\n"
            result_text += f"  • Always respect rate limits and be polite\n"
            result_text += f"  • Consider contacting website owners for permission\n"
            result_text += f"  • Use official APIs when available\n"
            result_text += f"  • Document sources and maintain attribution\n"
            result_text += f"  • Review applicable copyright and privacy laws\n"
            
            return [types.TextContent(type="text", text=result_text)]
            
        except Exception as e:
            logger.error(f"Error in check_legal_compliance: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Error checking legal compliance: {str(e)}"
            )]

async def main():
    """Main server entry point"""
    import json
    
    # Load configuration
    try:
        with open('config/mcp_config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {
            "storage": {"base_path": "./data"},
            "face_detection": {"face_threshold": 0.6},
            "categorization": {"categorized_path": "./data/categorized"},
            "metadata": {"metadata_path": "./data/metadata"},
            "legal": {},
            "instagram": {"delay": 2, "max_posts": 50},
            "pornpics": {"delay": 1, "max_images": 100}
        }
    
    # Create server
    server_instance = WebScraperMCPServer(config)
    
    # Run server
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
```

---

## 🚀 Implementation Workflow

### Step 1: Environment Setup
```bash
# Create project directory
mkdir mcp-web-scraper
cd mcp-web-scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create project structure
mkdir -p src/{scrapers,categorization,storage,utils}
mkdir -p config data/{raw,processed,categorized,metadata}
```

### Step 2: Configuration
```json
# config/mcp_config.json
{
  "storage": {
    "base_path": "./data",
    "max_file_size": 10485760,
    "allowed_formats": ["jpg", "jpeg", "png", "webp"]
  },
  "face_detection": {
    "face_threshold": 0.6,
    "min_face_size": 50,
    "max_faces_per_image": 10
  },
  "categorization": {
    "categorized_path": "./data/categorized",
    "auto_learn_faces": true,
    "min_confidence": 0.8
  },
  "legal": {
    "require_robots_check": true,
    "require_attribution": true,
    "user_agent": "MCP-WebScraper/1.0"
  },
  "instagram": {
    "delay": 2,
    "max_posts": 50,
    "public_only": true
  },
  "pornpics": {
    "delay": 1,
    "max_images": 100,
    "respect_rate_limits": true
  }
}
```

### Step 3: MCP Integration
```json
# VS Code settings.json
{
  "mcp.servers": {
    "web-scraper": {
      "command": "python",
      "args": ["C:/path/to/mcp-web-scraper/src/server.py"],
      "cwd": "C:/path/to/mcp-web-scraper"
    }
  }
}
```

### Step 4: Usage Examples

#### Scraping a Profile
```python
# Use MCP tool
await call_tool("scrape_profile", {
    "website": "pornpics", 
    "profile_url": "https://www.pornpics.com/models/example-model/",
    "max_images": 50
})
```

#### Auto-Categorizing Images
```python
# Use MCP tool  
await call_tool("categorize_images", {
    "input_folder": "./data/raw",
    "learn_faces": true
})
```

#### Legal Compliance Check
```python
# Use MCP tool
await call_tool("check_legal_compliance", {
    "url": "https://www.pornpics.com/models/example/",
    "check_robots": true,
    "check_tos": true
})
```

---

## 🧪 Testing & Validation

### Test Script
```python
# test_mcp_server.py
import asyncio
import json
from src.server import WebScraperMCPServer

async def test_server():
    config = {
        "storage": {"base_path": "./test_data"},
        "face_detection": {"face_threshold": 0.6},
        "categorization": {"categorized_path": "./test_data/categorized"},
    }
    
    server = WebScraperMCPServer(config)
    
    # Test legal compliance
    result = await server.handle_check_legal_compliance({
        "url": "https://www.pornpics.com/",
        "check_robots": True,
        "check_tos": True
    })
    
    print("Legal compliance test:")
    print(result[0].text)
    
    # Add more tests...

if __name__ == "__main__":
    asyncio.run(test_server())
```

### Quality Validation
- **Image Quality**: Minimum resolution, clarity checks
- **Face Detection**: Accuracy validation with known datasets  
- **Legal Compliance**: Automated robots.txt and ToS checking
- **Rate Limiting**: Respect website guidelines
- **Error Handling**: Robust error recovery

---

## ⚠️ Important Legal & Ethical Notes

### ❌ DO NOT:
- Scrape private or password-protected content
- Ignore robots.txt or website ToS
- Use scraped content for commercial purposes without permission
- Scrape personal data without consent
- Overwhelm servers with requests

### ✅ DO:
- Always check robots.txt and Terms of Service
- Implement proper rate limiting
- Maintain attribution and source tracking
- Use official APIs when available
- Respect copyright and privacy laws
- Get explicit permission for commercial use

### 📋 Legal Checklist:
- [ ] Robots.txt compliance verified
- [ ] Terms of Service reviewed
- [ ] Rate limiting implemented
- [ ] Attribution system in place
- [ ] Privacy considerations addressed
- [ ] Copyright compliance ensured
- [ ] Data retention policies defined

---

## 🔧 Maintenance & Monitoring

### Monitoring Tools
```python
# src/utils/monitor.py
class ScrapingMonitor:
    def __init__(self):
        self.metrics = {
            "requests_per_hour": 0,
            "success_rate": 0.0,
            "error_count": 0,
            "legal_violations": 0
        }
    
    def log_request(self, url: str, success: bool):
        """Log scraping request"""
        pass
    
    def check_rate_limits(self, domain: str) -> bool:
        """Check if rate limits are being respected"""
        pass
    
    def generate_report(self) -> Dict:
        """Generate monitoring report"""
        pass
```

### Backup & Recovery
- Regular metadata backups
- Image file integrity checks  
- Configuration versioning
- Error log rotation

---

This comprehensive guide provides you with everything needed to create a robust MCP server for web scraping with automatic categorization. Remember to always prioritize legal compliance and ethical considerations in your implementation!
