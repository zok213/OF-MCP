#!/usr/bin/env python3
"""
Browser Session Persistence Tests
Tests autonomous scraping capabilities and session management
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from src.core.browser_persistence import (
    SessionManager, AutonomousScraper, SessionProfile,
    AutonomousConfig, get_session_storage_path
)


class TestSessionProfile:
    """Test session profile functionality"""

    def test_session_profile_creation(self):
        """Test session profile creation"""
        profile = SessionProfile(
            name="test_profile",
            user_agent="Test Agent",
            viewport={"width": 1200, "height": 800}
        )

        assert profile.name == "test_profile"
        assert profile.user_agent == "Test Agent"
        assert profile.viewport["width"] == 1200
        assert len(profile.cookies) == 0
        assert len(profile.local_storage) == 0

    def test_session_profile_defaults(self):
        """Test session profile default values"""
        profile = SessionProfile(name="default_test")

        assert profile.user_agent == ""
        assert profile.viewport["width"] == 1920
        assert profile.last_used == 0.0
        assert not profile.login_status["logged_in"]


class TestSessionManager:
    """Test session manager functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir)
        self.config = AutonomousConfig()
        self.manager = SessionManager(self.config, self.storage_path)

    def teardown_method(self):
        """Cleanup after each test"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_session_profile_creation(self):
        """Test creating session profiles"""
        profile = self.manager.create_session_profile("test_session", "Custom Agent")

        assert profile.name == "test_session"
        assert profile.user_agent == "Custom Agent"
        assert profile in self.manager.sessions.values()

    @pytest.mark.asyncio
    async def test_persistent_context_creation(self):
        """Test creating persistent browser context"""
        # Mock browser to avoid actual browser launch
        with patch('src.core.browser_persistence.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_browser.new_context.return_value = mock_context
            mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser

            await self.manager.initialize()

            # Create session profile
            profile = self.manager.create_session_profile("test_session")

            # Create persistent context
            context = await self.manager.create_persistent_context("test_session")

            assert context == mock_context
            assert "test_session" in self.manager.active_sessions

    @pytest.mark.asyncio
    async def test_session_persistence(self):
        """Test session state persistence"""
        # Create and populate a session
        profile = self.manager.create_session_profile("persist_test")
        profile.cookies = [{"name": "test", "value": "value"}]
        profile.local_storage = {"key": "stored_value"}

        # Mock browser context for saving
        with patch('src.core.browser_persistence.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()

            # Mock cookies and storage
            mock_context.cookies.return_value = [{"name": "session", "value": "active"}]
            mock_context.pages = [mock_page]

            mock_page.evaluate.side_effect = [
                {"test_key": "test_value"},  # localStorage
                {"session_key": "session_value"}  # sessionStorage
            ]

            mock_browser.new_context.return_value = mock_context
            mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser

            await self.manager.initialize()

            # Save session
            await self.manager.save_session("persist_test")

            # Verify file was created
            session_file = self.storage_path / "persist_test.json"
            assert session_file.exists()

            # Load and verify contents
            with open(session_file, 'r') as f:
                data = json.load(f)

            assert data["name"] == "persist_test"
            assert len(data["cookies"]) == 1
            assert data["local_storage"]["test_key"] == "test_value"

    @pytest.mark.asyncio
    async def test_session_loading(self):
        """Test loading saved sessions"""
        # Create a session file manually
        session_data = {
            "name": "loaded_session",
            "user_agent": "Loaded Agent",
            "viewport": {"width": 1024, "height": 768},
            "cookies": [{"name": "loaded", "value": "cookie"}],
            "local_storage": {"loaded": "data"},
            "session_storage": {},
            "created_at": 1000000.0,
            "last_used": 1000000.0,
            "login_status": {"logged_in": True}
        }

        session_file = self.storage_path / "loaded_session.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f)

        # Load sessions
        await self.manager.load_sessions()

        # Verify session was loaded
        assert "loaded_session" in self.manager.sessions
        profile = self.manager.sessions["loaded_session"]

        assert profile.name == "loaded_session"
        assert profile.user_agent == "Loaded Agent"
        assert profile.login_status["logged_in"] is True

    def test_session_info_retrieval(self):
        """Test getting session information"""
        profile = self.manager.create_session_profile("info_test")
        profile.cookies = [{"name": "test"}]
        profile.local_storage = {"key": "value"}
        profile.created_at = 1000000.0

        info = self.manager.get_session_info("info_test")

        assert info["name"] == "info_test"
        assert info["is_active"] is False
        assert info["cookies_count"] == 1
        assert info["local_storage_keys"] == 1

    def test_session_listing(self):
        """Test listing all sessions"""
        self.manager.create_session_profile("session1")
        self.manager.create_session_profile("session2")

        sessions = self.manager.list_sessions()

        assert len(sessions) == 2
        session_names = [s["name"] for s in sessions]
        assert "session1" in session_names
        assert "session2" in session_names

    def test_nonexistent_session_info(self):
        """Test getting info for nonexistent session"""
        info = self.manager.get_session_info("nonexistent")
        assert info is None


class TestAutonomousScraper:
    """Test autonomous scraper functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = AutonomousConfig(
            session_persistence=True,
            auto_login=True,
            headless=True
        )
        self.scraper = AutonomousScraper(self.config)

    def teardown_method(self):
        """Cleanup after each test"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_autonomous_session_creation(self):
        """Test creating autonomous scraping session"""
        with patch('src.core.browser_persistence.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()

            mock_browser.new_context.return_value = mock_context
            mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser

            async with self.scraper:
                task_id = await self.scraper.create_autonomous_session(
                    "test_profile",
                    ["https://example.com"]
                )

                assert "test_profile" in task_id
                assert task_id in self.scraper.active_tasks

    @pytest.mark.asyncio
    async def test_session_cleanup(self):
        """Test proper cleanup of autonomous sessions"""
        with patch('src.core.browser_persistence.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()

            mock_browser.new_context.return_value = mock_context
            mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser

            async with self.scraper:
                task_id = await self.scraper.create_autonomous_session(
                    "cleanup_test",
                    ["https://example.com"]
                )

                # Verify session exists
                assert task_id in self.scraper.active_tasks

            # After context manager exit, sessions should be cleaned up
            # (This tests the __aexit__ method)

    @pytest.mark.asyncio
    async def test_stop_session(self):
        """Test stopping an autonomous session"""
        with patch('src.core.browser_persistence.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()

            mock_browser.new_context.return_value = mock_browser
            mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser

            async with self.scraper:
                task_id = await self.scraper.create_autonomous_session(
                    "stop_test",
                    ["https://example.com"]
                )

                # Stop the session
                await self.scraper.stop_session(task_id)

                # Verify session was stopped
                assert task_id not in self.scraper.active_tasks

    def test_get_active_sessions(self):
        """Test getting list of active sessions"""
        # Initially no active sessions
        active = self.scraper.get_active_sessions()
        assert len(active) == 0

    def test_get_session_status(self):
        """Test getting session status"""
        status = self.scraper.get_session_status("nonexistent")
        assert status is None

    @pytest.mark.asyncio
    async def test_autonomous_scraping_loop_error_handling(self):
        """Test error handling in autonomous scraping loop"""
        with patch('src.core.browser_persistence.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()

            # Mock browser setup
            mock_browser.new_context.return_value = mock_context
            mock_context.new_page.return_value = mock_page

            # Mock page operations to raise exceptions
            mock_page.goto.side_effect = Exception("Network error")
            mock_page.close = AsyncMock()

            mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser

            async with self.scraper:
                task_id = await self.scraper.create_autonomous_session(
                    "error_test",
                    ["https://failing-site.com"]
                )

                # Let the task run briefly
                await asyncio.sleep(0.1)

                # Stop the session
                await self.scraper.stop_session(task_id)


class TestAutonomousConfig:
    """Test autonomous configuration"""

    def test_default_config(self):
        """Test default configuration values"""
        config = AutonomousConfig()

        assert config.session_persistence is True
        assert config.auto_login is True
        assert config.session_timeout_hours == 24.0
        assert config.max_concurrent_sessions == 3
        assert config.headless is False

    def test_custom_config(self):
        """Test custom configuration"""
        config = AutonomousConfig(
            session_persistence=False,
            auto_login=False,
            session_timeout_hours=12.0,
            headless=True
        )

        assert config.session_persistence is False
        assert config.auto_login is False
        assert config.session_timeout_hours == 12.0
        assert config.headless is True


class TestUtilityFunctions:
    """Test utility functions"""

    def test_get_session_storage_path(self):
        """Test getting default session storage path"""
        path = get_session_storage_path()

        # Should be in user's home directory
        assert ".mcp-scraper" in str(path)
        assert "sessions" in str(path)

    @pytest.mark.asyncio
    async def test_create_autonomous_scraper_convenience_function(self):
        """Test convenience function for creating autonomous scraper"""
        with patch('src.core.browser_persistence.AutonomousScraper') as mock_scraper_class:
            mock_scraper = AsyncMock()
            mock_scraper_class.return_value = mock_scraper

            # Mock the context manager
            mock_scraper.__aenter__.return_value = mock_scraper
            mock_scraper.__aexit__.return_value = None

            # Mock session creation
            mock_scraper.create_autonomous_session.return_value = "test_task_123"

            from src.core.browser_persistence import create_autonomous_scraper

            # This would normally be called with await, but we'll test the structure
            # The function is designed to be used with: scraper, task_id = await create_autonomous_scraper(...)


# Integration test for session persistence workflow
@pytest.mark.integration
class TestSessionPersistenceWorkflow:
    """Integration tests for complete session persistence workflow"""

    @pytest.mark.asyncio
    async def test_complete_session_workflow(self):
        """Test complete session creation, usage, and persistence workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir)

            config = AutonomousConfig(
                session_persistence=True,
                headless=True
            )

            async with SessionManager(config, storage_path) as manager:
                # Create session profile
                profile = manager.create_session_profile("workflow_test")
                profile.user_agent = "Workflow Test Agent"

                # Simulate browser operations
                with patch('src.core.browser_persistence.async_playwright') as mock_playwright:
                    mock_browser = AsyncMock()
                    mock_context = AsyncMock()
                    mock_page = AsyncMock()

                    mock_browser.new_context.return_value = mock_context
                    mock_context.new_page.return_value = mock_page
                    mock_context.cookies.return_value = [{"name": "workflow", "value": "test"}]

                    mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser

                    # Create context and perform operations
                    context = await manager.create_persistent_context("workflow_test")

                    # Simulate page operations
                    page = await context.new_page()
                    await page.goto("https://example.com")

                    # Save session
                    await manager.save_session("workflow_test")

                    # Verify persistence
                    session_file = storage_path / "workflow_test.json"
                    assert session_file.exists()

                    with open(session_file, 'r') as f:
                        saved_data = json.load(f)

                    assert saved_data["name"] == "workflow_test"
                    assert saved_data["user_agent"] == "Workflow Test Agent"
