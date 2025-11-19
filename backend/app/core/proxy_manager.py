# backend/app/core/proxy_manager.py
"""
Proxy manager for rotating proxy connections.
Supports multiple proxy types and automatic rotation.
"""

from typing import List, Dict, Any, Iterator
import random
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class ProxyManager:
    """
    Manages proxy rotation and assignment for Telegram clients.
    Supports SOCKS5 and HTTP proxies with authentication.
    """
    
    def __init__(self):
        self.proxies: List[Dict[str, Any]] = []
        self._load_proxies()
    
    def _load_proxies(self) -> None:
        """
        Load proxies from configuration.
        Expected format: socks5://user:pass@host:port or http://host:port
        """
        proxy_list = settings.get_proxy_list()
        
        for proxy_url in proxy_list:
            try:
                if proxy_url.startswith("socks5://"):
                    # Parse SOCKS5 proxy
                    # Format: socks5://[username:password@]host:port
                    proxy_info = self._parse_socks5_proxy(proxy_url)
                    self.proxies.append(proxy_info)
                    logger.info(f"Loaded SOCKS5 proxy: {proxy_info['host']}:{proxy_info['port']}")
                
                elif proxy_url.startswith("http://") or proxy_url.startswith("https://"):
                    # Parse HTTP proxy
                    proxy_info = self._parse_http_proxy(proxy_url)
                    self.proxies.append(proxy_info)
                    logger.info(f"Loaded HTTP proxy: {proxy_info['host']}:{proxy_info['port']}")
                
                else:
                    logger.warning(f"Unsupported proxy format: {proxy_url}")
            
            except Exception as e:
                logger.error(f"Failed to parse proxy {proxy_url}: {e}")
    
    def _parse_socks5_proxy(self, proxy_url: str) -> Dict[str, Any]:
        """
        Parse SOCKS5 proxy URL into components.
        
        Args:
            proxy_url: Full proxy URL
            
        Returns:
            Dictionary with proxy components
        """
        # Remove socks5:// prefix
        url = proxy_url.replace("socks5://", "")
        
        # Parse authentication if present
        if "@" in url:
            auth_part, host_part = url.split("@")
            username, password = auth_part.split(":")
        else:
            username, password = None, None
            host_part = url
        
        # Parse host and port
        host, port = host_part.split(":")
        
        proxy_info = {
            "type": "socks5",
            "host": host,
            "port": int(port),
            "username": username,
            "password": password
        }
        
        return proxy_info
    
    def _parse_http_proxy(self, proxy_url: str) -> Dict[str, Any]:
        """
        Parse HTTP proxy URL into components.
        
        Args:
            proxy_url: Full proxy URL
            
        Returns:
            Dictionary with proxy components
        """
        # Remove protocol prefix
        if proxy_url.startswith("https://"):
            protocol = "https"
            url = proxy_url.replace("https://", "")
        else:
            protocol = "http"
            url = proxy_url.replace("http://", "")
        
        # Parse authentication if present
        if "@" in url:
            auth_part, host_part = url.split("@")
            username, password = auth_part.split(":")
        else:
            username, password = None, None
            host_part = url
        
        # Parse host and port
        if ":" in host_part:
            host, port = host_part.split(":")
        else:
            host = host_part
            port = 8080 if protocol == "http" else 8443
        
        proxy_info = {
            "type": protocol,
            "host": host,
            "port": int(port),
            "username": username,
            "password": password
        }
        
        return proxy_info
    
    def get_proxy_iterator(self) -> Iterator[Dict[str, Any]]:
        """
        Create a cyclic iterator over available proxies.
        
        Returns:
            Infinite iterator over proxy configurations
        """
        if not self.proxies:
            logger.warning("No proxies configured, returning empty iterator")
            return iter([])
        
        # Shuffle proxies for initial random distribution
        shuffled_proxies = self.proxies.copy()
        random.shuffle(shuffled_proxies)
        
        # Create infinite cyclic iterator
        while True:
            for proxy in shuffled_proxies:
                yield proxy
    
    def get_proxy_for_client(self) -> Optional[Dict[str, Any]]:
        """
        Get a random proxy for a client.
        
        Returns:
            Random proxy configuration or None if no proxies available
        """
        if not self.proxies:
            return None
        
        return random.choice(self.proxies)
    
    def get_proxy_count(self) -> int:
        """
        Get the number of configured proxies.
        
        Returns:
            Number of proxies
        """
        return len(self.proxies)


# Global proxy manager instance
proxy_manager = ProxyManager()
