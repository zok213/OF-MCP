#!/usr/bin/env python3
"""
Database Integration Tests
Tests Supabase database integration with enterprise resilience
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock

from src.core.database import (
    SupabaseDatabase, DatabaseManager, ScrapingSession,
    ImageRecord, PersonRecord
)


class TestDatabaseModels:
    """Test database model classes"""

    def test_scraping_session_creation(self):
        """Test scraping session model creation"""
        session = ScrapingSession(
            profile_name="test_profile",
            target_sites=["site1.com", "site2.com"],
            status="running",
            total_images=10,
            successful_downloads=8,
            failed_downloads=2
        )

        assert session.profile_name == "test_profile"
        assert len(session.target_sites) == 2
        assert session.status == "running"
        assert session.total_images == 10

    def test_image_record_creation(self):
        """Test image record model creation"""
        image = ImageRecord(
            session_id="session_123",
            filename="test.jpg",
            local_path="/path/to/test.jpg",
            file_size=1024,
            file_hash="abc123",
            content_type="image/jpeg",
            width=1920,
            height=1080,
            source_url="https://example.com/image.jpg",
            category="test",
            tags=["tag1", "tag2"],
            quality_score=0.85
        )

        assert image.session_id == "session_123"
        assert image.filename == "test.jpg"
        assert image.width == 1920
        assert image.height == 1080
        assert image.quality_score == 0.85

    def test_person_record_creation(self):
        """Test person record model creation"""
        person = PersonRecord(
            name="John Doe",
            image_count=5,
            confidence_score=0.92,
            face_encoding=[0.1, 0.2, 0.3]  # Simplified for test
        )

        assert person.name == "John Doe"
        assert person.image_count == 5
        assert person.confidence_score == 0.92


class TestSupabaseDatabase:
    """Test Supabase database functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.config = {
            'supabase_url': 'https://test.supabase.co',
            'supabase_key': 'test_key',
            'max_retries': 3,
            'failure_threshold': 3,
            'recovery_timeout': 60
        }
        self.db = SupabaseDatabase(self.config)

    @pytest.mark.asyncio
    async def test_initialization_without_credentials(self):
        """Test initialization without credentials"""
        with patch('src.core.database.get_secure_credential') as mock_get:
            mock_get.return_value = None

            success = await self.db.initialize()
            assert not success

    @pytest.mark.asyncio
    async def test_initialization_with_credentials(self):
        """Test initialization with valid credentials"""
        with patch('src.core.database.get_secure_credential') as mock_get:
            mock_get.side_effect = lambda service, key: {
                ('supabase', 'url'): 'https://test.supabase.co',
                ('supabase', 'anon_key'): 'test_key'
            }.get((service, key))

            with patch('src.core.database.create_client') as mock_create:
                mock_client = MagicMock()
                mock_create.return_value = mock_client

                # Mock test connection
                mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock()

                success = await self.db.initialize()
                assert success
                assert self.db.client == mock_client

    @pytest.mark.asyncio
    async def test_create_scraping_session_success(self):
        """Test successful scraping session creation"""
        mock_client = MagicMock()
        self.db.client = mock_client
        self.db.circuit_breaker.state = self.db.circuit_breaker.CircuitBreakerState.CLOSED

        session = ScrapingSession(
            profile_name="test_profile",
            target_sites=["site1.com"],
            status="running"
        )

        # Mock database response
        mock_result = MagicMock()
        mock_result.data = [{'id': 'session_123'}]
        mock_client.table.return_value.insert.return_value.execute.return_value = mock_result

        with patch('src.core.database.AsyncRetry') as mock_retry:
            mock_retry.return_value = lambda func: func

            session_id = await self.db.create_scraping_session(session)

            assert session_id == 'session_123'
            mock_client.table.assert_called_with('scraping_sessions')

    @pytest.mark.asyncio
    async def test_update_scraping_session_success(self):
        """Test successful scraping session update"""
        mock_client = MagicMock()
        self.db.client = mock_client

        updates = {"status": "completed", "total_images": 100}

        mock_result = MagicMock()
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_result

        with patch('src.core.database.AsyncRetry') as mock_retry:
            mock_retry.return_value = lambda func: func

            success = await self.db.update_scraping_session("session_123", updates)

            assert success is True
            mock_client.table.assert_called_with('scraping_sessions')

    @pytest.mark.asyncio
    async def test_get_scraping_session_success(self):
        """Test successful scraping session retrieval"""
        mock_client = MagicMock()
        self.db.client = mock_client

        mock_data = {
            'id': 'session_123',
            'profile_name': 'test_profile',
            'target_sites': ['site1.com'],
            'status': 'completed',
            'total_images': 100,
            'successful_downloads': 95,
            'failed_downloads': 5,
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T01:00:00Z'
        }

        mock_result = MagicMock()
        mock_result.data = [mock_data]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        with patch('src.core.database.AsyncRetry') as mock_retry:
            mock_retry.return_value = lambda func: func

            session = await self.db.get_scraping_session("session_123")

            assert session is not None
            assert session.id == 'session_123'
            assert session.profile_name == 'test_profile'
            assert session.total_images == 100

    @pytest.mark.asyncio
    async def test_create_image_record_success(self):
        """Test successful image record creation"""
        mock_client = MagicMock()
        self.db.client = mock_client
        self.db.circuit_breaker.state = self.db.circuit_breaker.CircuitBreakerState.CLOSED

        image = ImageRecord(
            session_id="session_123",
            filename="test.jpg",
            local_path="/path/to/test.jpg",
            file_size=1024,
            file_hash="abc123",
            content_type="image/jpeg"
        )

        mock_result = MagicMock()
        mock_result.data = [{'id': 'image_123'}]
        mock_client.table.return_value.insert.return_value.execute.return_value = mock_result

        with patch('src.core.database.AsyncRetry') as mock_retry:
            mock_retry.return_value = lambda func: func

            image_id = await self.db.create_image_record(image)

            assert image_id == 'image_123'
            mock_client.table.assert_called_with('images')

    @pytest.mark.asyncio
    async def test_create_person_record_success(self):
        """Test successful person record creation"""
        mock_client = MagicMock()
        self.db.client = mock_client

        person = PersonRecord(
            name="John Doe",
            face_encoding=[0.1, 0.2, 0.3],
            image_count=1,
            confidence_score=0.9
        )

        mock_result = MagicMock()
        mock_result.data = [{'id': 'person_123'}]
        mock_client.table.return_value.insert.return_value.execute.return_value = mock_result

        with patch('src.core.database.AsyncRetry') as mock_retry:
            mock_retry.return_value = lambda func: func

            person_id = await self.db.create_person_record(person)

            assert person_id == 'person_123'
            mock_client.table.assert_called_with('persons')

    @pytest.mark.asyncio
    async def test_get_person_by_encoding_success(self):
        """Test finding person by face encoding"""
        mock_client = MagicMock()
        self.db.client = mock_client

        # Mock existing person data
        mock_data = {
            'id': 'person_123',
            'name': 'John Doe',
            'face_encoding': '[0.1, 0.2, 0.3]',
            'image_count': 5,
            'confidence_score': 0.9,
            'created_at': '2024-01-01T00:00:00Z'
        }

        mock_result = MagicMock()
        mock_result.data = [mock_data]
        mock_client.table.return_value.select.return_value.not_.return_value.is_.return_value.execute.return_value = mock_result

        test_encoding = [0.1, 0.2, 0.3]

        with patch('src.core.database.AsyncRetry') as mock_retry:
            mock_retry.return_value = lambda func: func

            person = await self.db.get_person_by_encoding(test_encoding)

            assert person is not None
            assert person.id == 'person_123'
            assert person.name == 'John Doe'

    @pytest.mark.asyncio
    async def test_get_scraping_stats_success(self):
        """Test getting scraping statistics"""
        mock_client = MagicMock()
        self.db.client = mock_client

        # Mock session data
        session_data = [
            {
                'status': 'completed',
                'start_time': '2024-01-01T00:00:00Z',
                'end_time': '2024-01-01T01:00:00Z',
                'profile_name': 'profile1'
            },
            {
                'status': 'failed',
                'start_time': '2024-01-02T00:00:00Z',
                'end_time': '2024-01-02T00:30:00Z',
                'profile_name': 'profile2'
            }
        ]

        # Mock image data
        image_data = [
            {'processing_status': 'completed'},
            {'processing_status': 'completed'},
            {'processing_status': 'failed'}
        ]

        mock_sessions = MagicMock()
        mock_sessions.data = session_data
        mock_images = MagicMock()
        mock_images.data = image_data

        mock_client.table.side_effect = [mock_sessions, mock_images]

        with patch('src.core.database.AsyncRetry') as mock_retry:
            mock_retry.return_value = lambda func: func

            stats = await self.db.get_scraping_stats(days=7)

            assert stats['period_days'] == 7
            assert stats['sessions']['total'] == 2
            assert stats['sessions']['completed'] == 1
            assert stats['images']['total'] == 3
            assert stats['images']['successful'] == 2

    @pytest.mark.asyncio
    async def test_get_database_health_success(self):
        """Test database health check"""
        mock_client = MagicMock()
        self.db.client = mock_client

        # Mock table operations
        mock_table_op = MagicMock()
        mock_table_op.data = [{'count': 1}]
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = mock_table_op

        health = await self.db.get_database_health()

        assert health['healthy'] is True
        assert 'table_counts' in health
        assert 'last_check' in health

    @pytest.mark.asyncio
    async def test_circuit_breaker_behavior(self):
        """Test circuit breaker behavior under failure"""
        mock_client = MagicMock()
        self.db.client = mock_client

        # Force failures to trigger circuit breaker
        mock_client.table.return_value.insert.return_value.execute.side_effect = Exception("Database error")

        session = ScrapingSession(profile_name="test", target_sites=["test.com"])

        # First few attempts should work (with retries)
        with patch('src.core.database.AsyncRetry') as mock_retry:
            mock_retry.return_value = lambda func: func

            # Simulate multiple failures
            for i in range(self.db.circuit_breaker.failure_threshold + 1):
                try:
                    await self.db.create_scraping_session(session)
                except:
                    pass

            # Circuit breaker should now be open
            assert self.db.circuit_breaker.state.value == "open"


class TestDatabaseManager:
    """Test database manager functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.config = {
            'supabase_url': 'https://test.supabase.co',
            'supabase_key': 'test_key'
        }
        self.manager = DatabaseManager(self.config)

    @pytest.mark.asyncio
    async def test_initialization_success(self):
        """Test successful initialization"""
        with patch.object(self.manager.supabase, 'initialize') as mock_init:
            mock_init.return_value = True

            success = await self.manager.initialize()
            assert success
            assert self.manager.initialized

    @pytest.mark.asyncio
    async def test_start_scraping_session(self):
        """Test starting a scraping session"""
        self.manager.initialized = True

        with patch.object(self.manager.supabase, 'create_scraping_session') as mock_create:
            mock_create.return_value = 'session_123'

            session_id = await self.manager.start_scraping_session(
                "test_profile", ["site1.com", "site2.com"]
            )

            assert session_id == 'session_123'
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_end_scraping_session(self):
        """Test ending a scraping session"""
        self.manager.initialized = True

        stats = {
            "status": "completed",
            "total_images": 100,
            "successful_downloads": 95,
            "failed_downloads": 5
        }

        with patch.object(self.manager.supabase, 'update_scraping_session') as mock_update:
            mock_update.return_value = True

            await self.manager.end_scraping_session("session_123", stats)

            mock_update.assert_called_once_with("session_123", {
                "status": "completed",
                "end_time": mock_update.call_args[0][1]["end_time"],  # datetime object
                "total_images": 100,
                "successful_downloads": 95,
                "failed_downloads": 5
            })

    @pytest.mark.asyncio
    async def test_record_image(self):
        """Test recording an image"""
        self.manager.initialized = True

        image_data = {
            "filename": "test.jpg",
            "local_path": "/path/to/test.jpg",
            "file_size": 1024,
            "content_type": "image/jpeg"
        }

        with patch.object(self.manager.supabase, 'create_image_record') as mock_create:
            mock_create.return_value = 'image_123'

            image_id = await self.manager.record_image("session_123", image_data)

            assert image_id == 'image_123'
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_or_create_person_new(self):
        """Test creating a new person record"""
        self.manager.initialized = True

        # Mock no existing person found
        with patch.object(self.manager.supabase, 'get_person_by_encoding') as mock_get:
            mock_get.return_value = None

            with patch.object(self.manager.supabase, 'create_person_record') as mock_create:
                mock_create.return_value = 'person_123'

                person_id = await self.manager.find_or_create_person(
                    [0.1, 0.2, 0.3], "John Doe", 0.9
                )

                assert person_id == 'person_123'
                mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_or_create_person_existing(self):
        """Test finding existing person record"""
        self.manager.initialized = True

        existing_person = PersonRecord(
            id='person_123',
            name='John Doe',
            image_count=5,
            confidence_score=0.8
        )

        with patch.object(self.manager.supabase, 'get_person_by_encoding') as mock_get:
            mock_get.return_value = existing_person

            with patch.object(self.manager.supabase, 'update_person') as mock_update:
                mock_update.return_value = True

                person_id = await self.manager.find_or_create_person(
                    [0.1, 0.2, 0.3], None, 0.9
                )

                assert person_id == 'person_123'
                mock_update.assert_called_once()


class TestIntegrationScenarios:
    """Test integration scenarios for database operations"""

    @pytest.mark.asyncio
    async def test_complete_session_workflow(self):
        """Test complete scraping session workflow"""
        config = {
            'supabase_url': 'https://test.supabase.co',
            'supabase_key': 'test_key'
        }

        with patch('src.core.database.get_secure_credential') as mock_get:
            mock_get.side_effect = lambda service, key: {
                ('supabase', 'url'): 'https://test.supabase.co',
                ('supabase', 'anon_key'): 'test_key'
            }.get((service, key))

            with patch('src.core.database.create_client') as mock_create:
                mock_client = MagicMock()
                mock_create.return_value = mock_client

                manager = DatabaseManager(config)
                await manager.initialize()

                # Mock all database operations
                with patch.object(manager.supabase, 'create_scraping_session') as mock_create_session:
                    mock_create_session.return_value = 'session_123'

                    with patch.object(manager.supabase, 'update_scraping_session') as mock_update_session:
                        mock_update_session.return_value = True

                        with patch.object(manager.supabase, 'create_image_record') as mock_create_image:
                            mock_create_image.return_value = 'image_123'

                            # Start session
                            session_id = await manager.start_scraping_session(
                                "test_profile", ["example.com"]
                            )
                            assert session_id == 'session_123'

                            # Record image
                            image_data = {
                                "filename": "test.jpg",
                                "local_path": "/path/test.jpg",
                                "file_size": 1024,
                                "content_type": "image/jpeg"
                            }
                            image_id = await manager.record_image(session_id, image_data)
                            assert image_id == 'image_123'

                            # End session
                            stats = {"status": "completed", "total_images": 1}
                            await manager.end_scraping_session(session_id, stats)

                            # Verify all operations were called
                            mock_create_session.assert_called_once()
                            mock_create_image.assert_called_once()
                            mock_update_session.assert_called_once()


# Performance test
@pytest.mark.performance
class TestPerformanceScenarios:
    """Test performance scenarios for database operations"""

    @pytest.mark.asyncio
    async def test_bulk_image_recording(self):
        """Test bulk image recording performance"""
        config = {
            'supabase_url': 'https://test.supabase.co',
            'supabase_key': 'test_key'
        }

        with patch('src.core.database.get_secure_credential') as mock_get:
            mock_get.side_effect = lambda service, key: {
                ('supabase', 'url'): 'https://test.supabase.co',
                ('supabase', 'anon_key'): 'test_key'
            }.get((service, key))

            with patch('src.core.database.create_client') as mock_create:
                mock_client = MagicMock()
                mock_create.return_value = mock_client

                manager = DatabaseManager(config)
                await manager.initialize()

                # Create multiple image records
                image_data_list = []
                for i in range(10):
                    image_data_list.append({
                        "filename": f"test_{i}.jpg",
                        "local_path": f"/path/test_{i}.jpg",
                        "file_size": 1024 + i,
                        "content_type": "image/jpeg",
                        "source_url": f"https://example.com/image_{i}.jpg",
                        "category": "test",
                        "tags": ["tag1", "tag2"],
                        "quality_score": 0.8 + (i * 0.01)
                    })

                with patch.object(manager.supabase, 'create_image_record') as mock_create:
                    mock_create.return_value = lambda: f"image_{len(mock_create.call_args_list)}"

                    import time
                    start_time = time.time()

                    # Record all images concurrently
                    tasks = [
                        manager.record_image("session_123", image_data)
                        for image_data in image_data_list
                    ]
                    results = await asyncio.gather(*tasks)

                    end_time = time.time()
                    duration = end_time - start_time

                    assert len(results) == 10
                    assert duration < 2.0  # Should complete within 2 seconds
                    assert mock_create.call_count == 10
