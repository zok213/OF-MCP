#!/usr/bin/env python3
"""
Proxy Management Module
Professional proxy rotation and health management for web scraping
"""

from .proxy_manager import (
    ProxyInfo,
    ProxyRotator, 
    ProxySession,
    AsyncProxySession,
    create_webshare_proxy_rotator
)

__all__ = [
    'ProxyInfo',
    'ProxyRotator',
    'ProxySession', 
    'AsyncProxySession',
    'create_webshare_proxy_rotator'
]
