#!/usr/bin/env python3
"""
Professional Proxy Management System
Handles proxy rotation, health checking, and retry logic for web scraping
"""

import random
import time
import logging
import requests
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class ProxyInfo:
    """Data class for proxy information"""
    ip: str
    port: int
    username: str
    password: str
    protocol: str = "http"
    is_healthy: bool = True
    response_time: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    last_used: float = field(default_factory=time.time)
    last_check: float = field(default_factory=time.time)
    
    @property
    def proxy_url(self) -> str:
        """Generate proxy URL for requests"""
        return f"{self.protocol}://{self.username}:{self.password}@{self.ip}:{self.port}"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.success_count + self.failure_count
        return (self.success_count / total) if total > 0 else 1.0
    
    @property
    def proxy_dict(self) -> Dict[str, str]:
        """Generate proxy dictionary for requests library"""
        proxy_url = self.proxy_url
        return {
            "http": proxy_url,
            "https": proxy_url
        }


class ProxyRotator:
    """Professional proxy rotation and health management"""
    
    def __init__(self, proxies: List[str], health_check_interval: int = 300):
        """
        Initialize proxy rotator
        
        Args:
            proxies: List of proxy strings in format "ip:port:username:password"
            health_check_interval: Seconds between health checks
        """
        self.proxies: List[ProxyInfo] = []
        self.healthy_proxies: List[ProxyInfo] = []
        self.current_index = 0
        self.health_check_interval = health_check_interval
        self.last_health_check = 0
        self.lock = threading.Lock()
        
        # Parse proxy strings
        for proxy_str in proxies:
            try:
                parts = proxy_str.strip().split(':')
                if len(parts) >= 4:
                    proxy = ProxyInfo(
                        ip=parts[0],
                        port=int(parts[1]),
                        username=parts[2],
                        password=parts[3]
                    )
                    self.proxies.append(proxy)
                    logger.info(f"Added proxy: {proxy.ip}:{proxy.port}")
                else:
                    logger.warning(f"Invalid proxy format: {proxy_str}")
            except Exception as e:
                logger.error(f"Error parsing proxy {proxy_str}: {e}")
        
        if not self.proxies:
            raise ValueError("No valid proxies provided")
        
        # Initialize all proxies as healthy
        self.healthy_proxies = self.proxies.copy()
        logger.info(f"Initialized with {len(self.proxies)} proxies")
    
    def get_next_proxy(self) -> ProxyInfo:
        """Get next healthy proxy with rotation"""
        with self.lock:
            # Check if health check is needed
            if time.time() - self.last_health_check > self.health_check_interval:
                self._schedule_health_check()
            
            if not self.healthy_proxies:
                logger.warning("No healthy proxies available, using all proxies")
                self.healthy_proxies = self.proxies.copy()
            
            # Get next proxy
            proxy = self.healthy_proxies[self.current_index % len(self.healthy_proxies)]
            self.current_index += 1
            proxy.last_used = time.time()
            
            return proxy
    
    def get_random_proxy(self) -> ProxyInfo:
        """Get random healthy proxy"""
        with self.lock:
            if not self.healthy_proxies:
                self.healthy_proxies = self.proxies.copy()
            
            return random.choice(self.healthy_proxies)
    
    def mark_proxy_success(self, proxy: ProxyInfo, response_time: float = 0.0):
        """Mark proxy as successful"""
        with self.lock:
            proxy.success_count += 1
            proxy.response_time = response_time
            if not proxy.is_healthy:
                proxy.is_healthy = True
                if proxy not in self.healthy_proxies:
                    self.healthy_proxies.append(proxy)
                    logger.info(f"Proxy {proxy.ip}:{proxy.port} is back online")
    
    def mark_proxy_failure(self, proxy: ProxyInfo):
        """Mark proxy as failed"""
        with self.lock:
            proxy.failure_count += 1
            
            # Remove from healthy list if failure rate is too high
            if proxy.success_rate < 0.5 and proxy.failure_count > 3:
                proxy.is_healthy = False
                if proxy in self.healthy_proxies:
                    self.healthy_proxies.remove(proxy)
                    logger.warning(f"Removed unhealthy proxy: {proxy.ip}:{proxy.port}")
    
    def _schedule_health_check(self):
        """Schedule health check for all proxies"""
        self.last_health_check = time.time()
        # Run health check in background thread
        threading.Thread(target=self._run_health_check, daemon=True).start()
    
    def _run_health_check(self):
        """Run health check on all proxies"""
        logger.info("Starting proxy health check...")
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(self._check_proxy_health, proxy)
                for proxy in self.proxies
            ]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Health check error: {e}")
        
        healthy_count = len(self.healthy_proxies)
        logger.info(f"Health check complete: {healthy_count}/{len(self.proxies)} proxies healthy")
    
    def _check_proxy_health(self, proxy: ProxyInfo) -> bool:
        """Check individual proxy health"""
        test_url = "https://httpbin.org/ip"
        timeout = 10
        
        try:
            start_time = time.time()
            
            response = requests.get(
                test_url,
                proxies=proxy.proxy_dict,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.mark_proxy_success(proxy, response_time)
                proxy.last_check = time.time()
                logger.debug(f"Proxy {proxy.ip}:{proxy.port} healthy ({response_time:.2f}s)")
                return True
            else:
                self.mark_proxy_failure(proxy)
                return False
                
        except Exception as e:
            self.mark_proxy_failure(proxy)
            logger.debug(f"Proxy {proxy.ip}:{proxy.port} failed health check: {e}")
            return False
    
    def get_proxy_stats(self) -> Dict[str, Any]:
        """Get proxy statistics"""
        with self.lock:
            return {
                'total_proxies': len(self.proxies),
                'healthy_proxies': len(self.healthy_proxies),
                'unhealthy_proxies': len(self.proxies) - len(self.healthy_proxies),
                'proxies': [
                    {
                        'ip': p.ip,
                        'port': p.port,
                        'is_healthy': p.is_healthy,
                        'success_rate': p.success_rate,
                        'response_time': p.response_time,
                        'success_count': p.success_count,
                        'failure_count': p.failure_count
                    }
                    for p in self.proxies
                ]
            }


class ProxySession:
    """HTTP session with automatic proxy rotation and retry logic"""
    
    def __init__(self, proxy_rotator: ProxyRotator, max_retries: int = 3):
        """
        Initialize proxy session
        
        Args:
            proxy_rotator: ProxyRotator instance
            max_retries: Maximum number of retries per request
        """
        self.proxy_rotator = proxy_rotator
        self.max_retries = max_retries
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        })
    
    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """GET request with proxy rotation and retry logic"""
        return self._request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> Optional[requests.Response]:
        """POST request with proxy rotation and retry logic"""
        return self._request('POST', url, **kwargs)
    
    def _request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """Internal request method with proxy rotation"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            proxy = self.proxy_rotator.get_next_proxy()
            
            try:
                # Set proxy for this request
                kwargs['proxies'] = proxy.proxy_dict
                kwargs.setdefault('timeout', 30)
                
                start_time = time.time()
                
                # Make request
                response = self.session.request(method, url, **kwargs)
                
                response_time = time.time() - start_time
                
                # Check response
                response.raise_for_status()
                
                # Mark proxy as successful
                self.proxy_rotator.mark_proxy_success(proxy, response_time)
                
                logger.debug(f"Request successful via {proxy.ip}:{proxy.port} ({response_time:.2f}s)")
                return response
                
            except Exception as e:
                last_exception = e
                self.proxy_rotator.mark_proxy_failure(proxy)
                
                logger.warning(f"Request failed via {proxy.ip}:{proxy.port} (attempt {attempt + 1}): {e}")
                
                # Add delay before retry
                if attempt < self.max_retries - 1:
                    delay = min(2 ** attempt, 10)  # Exponential backoff, max 10 seconds
                    time.sleep(delay)
        
        logger.error(f"All {self.max_retries} attempts failed for {url}: {last_exception}")
        return None
    
    def close(self):
        """Close the session"""
        self.session.close()


class AsyncProxySession:
    """Async HTTP session with proxy rotation"""
    
    def __init__(self, proxy_rotator: ProxyRotator, max_retries: int = 3):
        self.proxy_rotator = proxy_rotator
        self.max_retries = max_retries
        self.connector = None
        self.session = None
    
    async def __aenter__(self):
        self.connector = aiohttp.TCPConnector(limit=100, limit_per_host=20)
        self.session = aiohttp.ClientSession(
            connector=self.connector,
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.connector:
            await self.connector.close()
    
    async def get(self, url: str, **kwargs) -> Optional[aiohttp.ClientResponse]:
        """Async GET request with proxy rotation"""
        return await self._request('GET', url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> Optional[aiohttp.ClientResponse]:
        """Async POST request with proxy rotation"""
        return await self._request('POST', url, **kwargs)
    
    async def _request(self, method: str, url: str, **kwargs) -> Optional[aiohttp.ClientResponse]:
        """Internal async request method"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            proxy = self.proxy_rotator.get_next_proxy()
            
            try:
                # Set proxy for aiohttp
                kwargs['proxy'] = proxy.proxy_url
                
                start_time = time.time()
                
                async with self.session.request(method, url, **kwargs) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        self.proxy_rotator.mark_proxy_success(proxy, response_time)
                        return response
                    else:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status
                        )
                        
            except Exception as e:
                last_exception = e
                self.proxy_rotator.mark_proxy_failure(proxy)
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(min(2 ** attempt, 10))
        
        logger.error(f"All {self.max_retries} async attempts failed for {url}: {last_exception}")
        return None


def create_webshare_proxy_rotator(proxy_list: List[str]) -> ProxyRotator:
    """
    Create proxy rotator specifically configured for Webshare proxies
    
    Args:
        proxy_list: List of proxy strings in format "ip:port:username:password"
    
    Returns:
        ProxyRotator instance
    """
    return ProxyRotator(
        proxies=proxy_list,
        health_check_interval=300  # Check health every 5 minutes
    )


# Example usage and testing
if __name__ == "__main__":
    # Test proxy configuration
    webshare_proxies = [
        "23.95.150.145:6114:hmtdviqy:oipyyzu8cad4",
        "198.23.239.134:6540:hmtdviqy:oipyyzu8cad4",
        "45.38.107.97:6014:hmtdviqy:oipyyzu8cad4",
        "207.244.217.165:6712:hmtdviqy:oipyyzu8cad4",
        "107.172.163.27:6543:hmtdviqy:oipyyzu8cad4",
        "104.222.161.211:6343:hmtdviqy:oipyyzu8cad4",
        "64.137.96.74:6641:hmtdviqy:oipyyzu8cad4",
        "216.10.27.159:6837:hmtdviqy:oipyyzu8cad4",
        "136.0.207.84:6661:hmtdviqy:oipyyzu8cad4",
        "142.147.128.93:6593:hmtdviqy:oipyyzu8cad4"
    ]
    
    # Test basic functionality
    proxy_rotator = create_webshare_proxy_rotator(webshare_proxies)
    
    # Test with requests
    session = ProxySession(proxy_rotator)
    
    try:
        # Test IP checking
        response = session.get("https://httpbin.org/ip")
        if response:
            print(f"IP check response: {response.text}")
        
        # Get proxy stats
        stats = proxy_rotator.get_proxy_stats()
        print(f"Proxy stats: {stats}")
        
    finally:
        session.close()
