#!/usr/bin/env python3
"""
Security Module Tests
Tests credential management, encryption, and validation
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.core.security import (
    SecureCredentialManager, APIRateLimiter, SecureConfigValidator,
    initialize_security, get_secure_credential, store_secure_credential,
    validate_api_key_format
)


class TestSecureCredentialManager:
    """Test secure credential management"""

    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir) / "test_credentials.enc"
        self.manager = SecureCredentialManager(self.storage_path)

    def teardown_method(self):
        """Cleanup after each test"""
        if self.storage_path.exists():
            os.remove(self.storage_path)
        key_file = self.storage_path.with_suffix('.key')
        if key_file.exists():
            os.remove(key_file)

    def test_initialization_without_password(self):
        """Test initialization without master password"""
        assert self.manager.initialize()
        assert self.manager._fernet is not None

    def test_initialization_with_password(self):
        """Test initialization with master password"""
        assert self.manager.initialize("test_password")
        assert self.manager._fernet is not None

    def test_store_and_retrieve_credential(self):
        """Test storing and retrieving credentials"""
        self.manager.initialize("test_password")

        # Store credential
        assert self.manager.store_credential("jina", "api_key", "test_key_123")

        # Retrieve credential
        retrieved = self.manager.get_credential("jina", "api_key")
        assert retrieved == "test_key_123"

    def test_nonexistent_credential(self):
        """Test retrieving nonexistent credential"""
        self.manager.initialize("test_password")
        assert self.manager.get_credential("nonexistent", "key") is None

    def test_api_key_validation(self):
        """Test API key format validation"""
        self.manager.initialize("test_password")

        # Valid Jina key
        assert self.manager.validate_api_key("jina", "jina_test_key_12345")

        # Invalid Jina key
        assert not self.manager.validate_api_key("jina", "invalid_key")

        # Valid OpenAI key
        assert self.manager.validate_api_key("openai", "sk-test_key_1234567890")

        # Invalid OpenAI key
        assert not self.manager.validate_api_key("openai", "invalid_key")

    def test_persistence_across_instances(self):
        """Test credential persistence across manager instances"""
        # First instance
        self.manager.initialize("test_password")
        self.manager.store_credential("test", "key", "value")

        # Second instance with same storage
        manager2 = SecureCredentialManager(self.storage_path)
        manager2.initialize("test_password")

        retrieved = manager2.get_credential("test", "key")
        assert retrieved == "value"


class TestAPIRateLimiter:
    """Test API rate limiting"""

    def setup_method(self):
        """Setup for each test"""
        self.limiter = APIRateLimiter(requests_per_minute=10)

    @patch('time.time')
    @pytest.mark.asyncio
    async def test_rate_limiting(self, mock_time):
        """Test rate limiting functionality"""
        mock_time.return_value = 1000.0

        # Should not wait initially
        await self.limiter.wait_if_needed()
        assert len(self.limiter.requests) == 1

        # Fill up the rate limit
        for i in range(9):
            await self.limiter.wait_if_needed()

        assert len(self.limiter.requests) == 10

        # Next request should wait
        mock_time.return_value = 1000.5  # Half second later
        with patch('asyncio.sleep') as mock_sleep:
            await self.limiter.wait_if_needed()
            mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_cleanup(self):
        """Test cleanup of old requests"""
        import time

        # Add old requests
        self.limiter.requests = [time.time() - 70] * 5  # 70 seconds ago

        # Add current request
        await self.limiter.wait_if_needed()

        # Should have cleaned up old requests
        assert len(self.limiter.requests) == 1


class TestSecureConfigValidator:
    """Test configuration security validation"""

    def test_valid_config(self):
        """Test validation of secure configuration"""
        config = {
            "legal": {"require_robots_check": True},
            "proxy_config": {"webshare_proxies": ["ip:port:user:pass"]}
        }

        result = SecureConfigValidator.validate_config(config)
        assert result["valid"]

    def test_config_with_exposed_credentials(self):
        """Test detection of exposed credentials"""
        config = {
            "jina_ai": {"api_key": "jina_exposed_key_12345"}
        }

        result = SecureConfigValidator.validate_config(config)
        assert not result["valid"]
        assert "Potential exposed credential" in str(result["warnings"])

    def test_config_without_robots_check(self):
        """Test detection of missing robots.txt compliance"""
        config = {
            "legal": {"require_robots_check": False}
        }

        result = SecureConfigValidator.validate_config(config)
        assert "robots.txt" in str(result["warnings"])


class TestGlobalSecurityFunctions:
    """Test global security utility functions"""

    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = tempfile.mkdtemp()
        os.environ['MCP_SCRAPER_STORAGE'] = self.temp_dir

    def teardown_method(self):
        """Cleanup after each test"""
        # Clean up any created files
        for file in Path(self.temp_dir).glob("*"):
            if file.exists():
                os.remove(file)
        os.rmdir(self.temp_dir)

    def test_api_key_validation_function(self):
        """Test global API key validation function"""
        assert validate_api_key_format("jina", "jina_test_key_123")
        assert not validate_api_key_format("jina", "invalid_key")

    @patch('src.core.security.security_manager')
    def test_secure_credential_functions(self, mock_manager):
        """Test secure credential functions"""
        mock_manager.store_credential.return_value = True
        mock_manager.get_credential.return_value = "test_value"

        # Test store
        result = store_secure_credential("test", "key", "value")
        mock_manager.store_credential.assert_called_once_with("test", "key", "value")
        assert result is True

        # Test retrieve
        result = get_secure_credential("test", "key")
        mock_manager.get_credential.assert_called_once_with("test", "key")
        assert result == "test_value"
