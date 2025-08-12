#!/usr/bin/env python3
"""
Professional Image Download Manager
Educational/Research Purpose Only
"""

import asyncio
import aiohttp
import hashlib
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
import json

logger = logging.getLogger(__name__)


class ImageDownloadManager:
    """Professional image download manager with deduplication and validation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.download_stats = {
            'total_requested': 0,
            'successful_downloads': 0,
            'skipped_duplicates': 0,
            'failed_downloads': 0,
            'total_bytes': 0
        }
        
        # Load existing hashes for deduplication
        self.image_hashes = self.load_image_hashes()
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()
        
    async def initialize_session(self):
        """Initialize aiohttp session with proper configuration"""
        timeout = aiohttp.ClientTimeout(
            total=self.config.get('download_timeout', 120),
            connect=30
        )
        
        connector = aiohttp.TCPConnector(
            limit=self.config.get('max_concurrent_downloads', 5),
            limit_per_host=3
        )
        
        headers = {
            'User-Agent': self.config.get('user_agent', 
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
            'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers=headers
        )
        
    def load_image_hashes(self) -> Dict[str, str]:
        """Load existing image hashes for deduplication"""
        try:
            hash_file = Path(self.config['storage']['metadata_path']) / 'image_hashes.json'
            if hash_file.exists():
                with open(hash_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load image hashes: {e}")
        return {}
        
    def save_image_hashes(self):
        """Save image hashes for deduplication"""
        try:
            hash_file = Path(self.config['storage']['metadata_path']) / 'image_hashes.json'
            hash_file.parent.mkdir(parents=True, exist_ok=True)
            with open(hash_file, 'w') as f:
                json.dump(self.image_hashes, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving image hashes: {e}")
    
    async def download_images_batch(self, images: List[Dict[str, Any]], 
                                   category: str = 'general') -> Dict[str, Any]:
        """Download a batch of images with professional handling"""
        try:
            if not images:
                return {
                    'status': 'success',
                    'message': 'No images to download',
                    'downloaded': [],
                    'failed': [],
                    'skipped': []
                }
                
            logger.info(f"Starting download of {len(images)} images for category: {category}")
            
            # Create category directory
            category_dir = Path(self.config['storage']['raw_path']) / category
            category_dir.mkdir(parents=True, exist_ok=True)
            
            # Update stats
            self.download_stats['total_requested'] += len(images)
            
            # Create download tasks
            semaphore = asyncio.Semaphore(self.config.get('max_concurrent_downloads', 5))
            tasks = [
                self.download_single_image(image, category_dir, semaphore)
                for image in images
            ]
            
            # Execute downloads
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            downloaded = []
            failed = []
            skipped = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed.append({
                        'url': images[i].get('url', 'unknown'),
                        'error': str(result)
                    })
                    self.download_stats['failed_downloads'] += 1
                elif result['status'] == 'success':
                    downloaded.append(result)
                    self.download_stats['successful_downloads'] += 1
                    self.download_stats['total_bytes'] += result.get('file_size', 0)
                elif result['status'] == 'skipped':
                    skipped.append(result)
                    self.download_stats['skipped_duplicates'] += 1
                else:
                    failed.append(result)
                    self.download_stats['failed_downloads'] += 1
            
            # Save updated hashes
            self.save_image_hashes()
            
            return {
                'status': 'success',
                'message': f'Downloaded {len(downloaded)} images, skipped {len(skipped)}, failed {len(failed)}',
                'downloaded': downloaded,
                'failed': failed,
                'skipped': skipped,
                'stats': self.download_stats.copy()
            }
            
        except Exception as e:
            logger.error(f"Error in batch download: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'downloaded': [],
                'failed': [],
                'skipped': []
            }
    
    async def download_single_image(self, image_info: Dict[str, Any], 
                                   download_dir: Path, 
                                   semaphore: asyncio.Semaphore) -> Dict[str, Any]:
        """Download a single image with validation and deduplication"""
        async with semaphore:
            try:
                url = image_info['url']
                filename = image_info['filename']
                
                # Sanitize filename
                filename = self.sanitize_filename(filename)
                file_path = download_dir / filename
                
                # Check if file already exists
                if file_path.exists():
                    return {
                        'status': 'skipped',
                        'message': 'File already exists',
                        'url': url,
                        'file_path': str(file_path)
                    }
                
                # Add rate limiting delay
                delay = self.config.get('download_delay', 1)
                await asyncio.sleep(delay)
                
                # Download image
                async with self.session.get(url) as response:
                    if response.status != 200:
                        return {
                            'status': 'error',
                            'message': f'HTTP {response.status}',
                            'url': url
                        }
                    
                    content = await response.read()
                    
                    # Validate content
                    validation_result = self.validate_image_content(content, image_info)
                    if not validation_result['valid']:
                        return {
                            'status': 'error',
                            'message': validation_result['reason'],
                            'url': url
                        }
                    
                    # Check for duplicates using hash
                    content_hash = hashlib.md5(content).hexdigest()
                    if content_hash in self.image_hashes:
                        return {
                            'status': 'skipped',
                            'message': f'Duplicate image (existing: {self.image_hashes[content_hash]})',
                            'url': url,
                            'hash': content_hash
                        }
                    
                    # Save image
                    with open(file_path, 'wb') as f:
                        f.write(content)
                    
                    # Record hash
                    self.image_hashes[content_hash] = str(file_path)
                    
                    # Create metadata
                    metadata = {
                        'url': url,
                        'filename': filename,
                        'file_path': str(file_path),
                        'file_size': len(content),
                        'hash_md5': content_hash,
                        'download_time': time.time(),
                        'mime_type': response.headers.get('Content-Type'),
                        'original_info': image_info
                    }
                    
                    # Save metadata
                    metadata_file = file_path.with_suffix('.json')
                    with open(metadata_file, 'w') as f:
                        json.dump(metadata, f, indent=2)
                    
                    return {
                        'status': 'success',
                        'message': 'Downloaded successfully',
                        'url': url,
                        'file_path': str(file_path),
                        'file_size': len(content),
                        'hash': content_hash,
                        'metadata': metadata
                    }
                    
            except asyncio.TimeoutError:
                return {
                    'status': 'error',
                    'message': 'Download timeout',
                    'url': image_info.get('url', 'unknown')
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': str(e),
                    'url': image_info.get('url', 'unknown')
                }
    
    def validate_image_content(self, content: bytes, image_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate downloaded image content"""
        try:
            # Check file size
            file_size_mb = len(content) / (1024 * 1024)
            max_size_mb = self.config.get('max_file_size_mb', 50)
            
            if file_size_mb > max_size_mb:
                return {
                    'valid': False,
                    'reason': f'File too large: {file_size_mb:.1f}MB > {max_size_mb}MB'
                }
            
            # Check minimum file size (avoid empty/corrupted files)
            if len(content) < 1024:  # Less than 1KB
                return {
                    'valid': False,
                    'reason': 'File too small (likely corrupted)'
                }
            
            # Check magic bytes for image formats
            if not self.is_valid_image_format(content):
                return {
                    'valid': False,
                    'reason': 'Invalid image format'
                }
            
            return {'valid': True, 'reason': 'Valid'}
            
        except Exception as e:
            return {
                'valid': False,
                'reason': f'Validation error: {str(e)}'
            }
    
    def is_valid_image_format(self, content: bytes) -> bool:
        """Check if content is a valid image based on magic bytes"""
        try:
            # Check magic bytes for common image formats
            magic_bytes = {
                b'\\xff\\xd8\\xff': 'jpeg',
                b'\\x89PNG\\r\\n\\x1a\\n': 'png',
                b'GIF87a': 'gif',
                b'GIF89a': 'gif',
                b'RIFF': 'webp'  # WebP starts with RIFF
            }
            
            for magic, format_name in magic_bytes.items():
                if content.startswith(magic):
                    return True
            
            # Check for WebP more specifically
            if content.startswith(b'RIFF') and b'WEBP' in content[:20]:
                return True
                
            return False
            
        except Exception:
            return False
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to be safe for filesystem"""
        import re
        
        # Remove or replace problematic characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'[\\x00-\\x1f]', '', filename)  # Remove control characters
        
        # Ensure filename isn't too long
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:190] + ext
        
        # Ensure filename has an extension
        if '.' not in filename:
            filename += '.jpg'
            
        return filename
    
    def get_download_stats(self) -> Dict[str, Any]:
        """Get current download statistics"""
        return {
            **self.download_stats,
            'unique_images': len(self.image_hashes),
            'success_rate': (
                self.download_stats['successful_downloads'] / 
                max(self.download_stats['total_requested'], 1)
            ) * 100,
            'total_size_mb': self.download_stats['total_bytes'] / (1024 * 1024)
        }
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            if self.session:
                await self.session.close()
                
            # Save final hashes
            self.save_image_hashes()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


async def download_images_from_scraping_result(scraping_result: Dict[str, Any], 
                                             config: Dict[str, Any],
                                             category: str = 'general') -> Dict[str, Any]:
    """Helper function to download images from a scraping result"""
    try:
        if scraping_result.get('status') != 'success':
            return {
                'status': 'error',
                'message': f"Scraping failed: {scraping_result.get('message', 'Unknown error')}",
                'downloaded': []
            }
        
        images = scraping_result.get('images', [])
        if not images:
            return {
                'status': 'success',
                'message': 'No images found to download',
                'downloaded': []
            }
        
        async with ImageDownloadManager(config) as downloader:
            result = await downloader.download_images_batch(images, category)
            return result
            
    except Exception as e:
        logger.error(f"Error downloading images: {e}")
        return {
            'status': 'error',
            'message': str(e),
            'downloaded': []
        }


# Example usage
async def main():
    """Example usage of the image download manager"""
    
    # Sample configuration
    config = {
        'storage': {
            'raw_path': './data/raw',
            'metadata_path': './data/metadata'
        },
        'max_concurrent_downloads': 3,
        'download_timeout': 60,
        'download_delay': 2,
        'max_file_size_mb': 25,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Sample image list
    sample_images = [
        {
            'url': 'https://example.com/image1.jpg',
            'filename': 'sample_image_1.jpg',
            'alt_text': 'Sample image'
        }
    ]
    
    async with ImageDownloadManager(config) as downloader:
        result = await downloader.download_images_batch(sample_images, 'test_category')
        print(json.dumps(result, indent=2))
        print("Download stats:", downloader.get_download_stats())


if __name__ == "__main__":
    asyncio.run(main())
