#!/usr/bin/env python3
"""
Cloud Storage Integration Tests
Tests Wasabi S3-compatible storage with enterprise resilience
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from src.core.cloud_storage import (
    WasabiCloudStorage, CloudStorageManager, CloudFileMetadata
)


class TestCloudFileMetadata:
    """Test cloud file metadata functionality"""

    def test_cloud_file_metadata_creation(self):
        """Test cloud file metadata creation"""
        metadata = CloudFileMetadata(
            filename="test.jpg",
            s3_key="test/test.jpg",
            bucket="test-bucket",
            size=1024,
            content_type="image/jpeg",
            etag='"abc123"',
            last_modified="2024-01-01T00:00:00Z"
        )

        assert metadata.filename == "test.jpg"
        assert metadata.s3_key == "test/test.jpg"
        assert metadata.bucket == "test-bucket"
        assert metadata.size == 1024
        assert metadata.content_type == "image/jpeg"


class TestWasabiCloudStorage:
    """Test Wasabi cloud storage functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.config = {
            'bucket_name': 'test-bucket',
            'region': 's3.ap-northeast-1.wasabisys.com',
            'max_concurrent_uploads': 2,
            'failure_threshold': 2,
            'recovery_timeout': 30
        }
        self.storage = WasabiCloudStorage(self.config)

    @pytest.mark.asyncio
    async def test_initialization_without_credentials(self):
        """Test initialization without credentials"""
        with patch('src.core.cloud_storage.get_secure_credential') as mock_get:
            mock_get.return_value = None

            success = await self.storage.initialize()
            assert not success

    @pytest.mark.asyncio
    async def test_initialization_with_credentials(self):
        """Test initialization with valid credentials"""
        with patch('src.core.cloud_storage.get_secure_credential') as mock_get:
            mock_get.side_effect = lambda service, key: {
                ('wasabi', 'access_key'): 'test_access_key',
                ('wasabi', 'secret_key'): 'test_secret_key'
            }.get((service, key))

            with patch('src.core.cloud_storage.boto3') as mock_boto3:
                mock_client = MagicMock()
                mock_boto3.client.return_value = mock_client

                success = await self.storage.initialize()
                assert success
                assert self.storage.client == mock_client

    @pytest.mark.asyncio
    async def test_upload_file_success(self):
        """Test successful file upload"""
        # Setup mock client
        mock_client = MagicMock()
        self.storage.client = mock_client
        self.storage.circuit_breaker.state = self.storage.circuit_breaker.CircuitBreakerState.CLOSED

        # Create test file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_path = Path(temp_file.name)

        try:
            with patch('src.core.cloud_storage.AsyncRetry') as mock_retry:
                mock_retry.return_value = lambda func: func

                # Mock upload response
                mock_response = {"ETag": '"test-etag"', "LastModified": "2024-01-01T00:00:00Z"}
                mock_client.upload_file.return_value = mock_response

                result = await self.storage.upload_file(temp_path, "test-key")

                assert result is not None
                assert result.filename == temp_path.name
                assert result.s3_key == "test-key"
                assert result.size == len(b"test content")

        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_upload_file_circuit_breaker_open(self):
        """Test upload when circuit breaker is open"""
        self.storage.client = MagicMock()
        self.storage.circuit_breaker.state = self.storage.circuit_breaker.CircuitBreakerState.OPEN

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_path = Path(temp_file.name)

        try:
            result = await self.storage.upload_file(temp_path)
            assert result is None  # Should return None when circuit breaker is open

        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_download_file_success(self):
        """Test successful file download"""
        mock_client = MagicMock()
        self.storage.client = mock_client
        self.storage.circuit_breaker.state = self.storage.circuit_breaker.CircuitBreakerState.CLOSED

        # Mock download and head_object
        mock_client.download_file.return_value = None
        mock_client.head_object.return_value = {
            'ContentLength': 100,
            'ContentType': 'image/jpeg',
            'ETag': '"test-etag"',
            'LastModified': "2024-01-01T00:00:00Z"
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            local_path = Path(temp_dir) / "test.jpg"

            with patch('src.core.cloud_storage.AsyncRetry') as mock_retry:
                mock_retry.return_value = lambda func: func

                result = await self.storage.download_file("test-key", local_path)

                assert result is not None
                assert result.filename == "test.jpg"
                assert result.size == 100
                assert result.content_type == "image/jpeg"

    @pytest.mark.asyncio
    async def test_list_files_success(self):
        """Test successful file listing"""
        mock_client = MagicMock()
        self.storage.client = mock_client

        # Mock list_objects_v2 response
        mock_client.list_objects_v2.return_value = {
            'Contents': [
                {
                    'Key': 'test/file1.jpg',
                    'Size': 1000,
                    'ETag': '"etag1"',
                    'LastModified': "2024-01-01T00:00:00Z"
                },
                {
                    'Key': 'test/file2.jpg',
                    'Size': 2000,
                    'ETag': '"etag2"',
                    'LastModified': "2024-01-01T00:00:00Z"
                }
            ],
            'IsTruncated': False
        }

        with patch('src.core.cloud_storage.AsyncRetry') as mock_retry:
            mock_retry.return_value = lambda func: func

            files = await self.storage.list_files(prefix="test/")

            assert len(files) == 2
            assert files[0].filename == "file1.jpg"
            assert files[0].s3_key == "test/file1.jpg"
            assert files[1].filename == "file2.jpg"

    @pytest.mark.asyncio
    async def test_get_storage_stats_success(self):
        """Test getting storage statistics"""
        mock_client = MagicMock()
        self.storage.client = mock_client

        # Mock responses
        mock_client.head_bucket.return_value = {}
        mock_client.list_objects_v2.return_value = {'KeyCount': 5, 'IsTruncated': False}

        stats = await self.storage.get_storage_stats()

        assert stats['healthy'] is True
        assert stats['bucket_name'] == 'test-bucket'
        assert stats['estimated_object_count'] == 5

    @pytest.mark.asyncio
    async def test_get_storage_stats_failure(self):
        """Test storage stats when service is unavailable"""
        mock_client = MagicMock()
        self.storage.client = mock_client

        mock_client.head_bucket.side_effect = Exception("Service unavailable")

        stats = await self.storage.get_storage_stats()

        assert stats['healthy'] is False
        assert 'Service unavailable' in stats['error']


class TestCloudStorageManager:
    """Test cloud storage manager functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.config = {
            'bucket_name': 'test-bucket',
            'region': 's3.ap-northeast-1.wasabisys.com',
            'max_concurrent_uploads': 3
        }
        self.manager = CloudStorageManager(self.config)

    @pytest.mark.asyncio
    async def test_initialization_success(self):
        """Test successful initialization"""
        with patch.object(self.manager.wasabi, 'initialize') as mock_init:
            mock_init.return_value = True

            success = await self.manager.initialize()
            assert success
            assert self.manager.initialized

    @pytest.mark.asyncio
    async def test_initialization_failure(self):
        """Test initialization failure"""
        with patch.object(self.manager.wasabi, 'initialize') as mock_init:
            mock_init.return_value = False

            success = await self.manager.initialize()
            assert not success
            assert not self.manager.initialized

    @pytest.mark.asyncio
    async def test_upload_batch_success(self):
        """Test successful batch upload"""
        self.manager.initialized = True

        # Create test files
        test_files = []
        for i in range(2):
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(f"test content {i}".encode())
                test_files.append(Path(temp_file.name))

        try:
            with patch.object(self.manager.wasabi, 'upload_file') as mock_upload:
                mock_upload.return_value = CloudFileMetadata(
                    filename=f"test{i}.txt",
                    s3_key=f"test/test{i}.txt",
                    bucket="test-bucket",
                    size=20,
                    content_type="text/plain",
                    etag=f'"etag{i}"',
                    last_modified="2024-01-01T00:00:00Z"
                )

                results = await self.manager.upload_batch(test_files, "test/")

                assert len(results) == 2
                assert all(result is not None for result in results)
                assert mock_upload.call_count == 2

        finally:
            for file_path in test_files:
                os.unlink(file_path)

    @pytest.mark.asyncio
    async def test_sync_local_to_cloud(self):
        """Test syncing local directory to cloud"""
        self.manager.initialized = True

        with tempfile.TemporaryDirectory() as temp_dir:
            local_dir = Path(temp_dir)

            # Create test files
            (local_dir / "file1.jpg").write_text("content1")
            (local_dir / "file2.png").write_text("content2")
            (local_dir / "subdir").mkdir()
            (local_dir / "subdir" / "file3.txt").write_text("content3")

            with patch.object(self.manager.wasabi, 'upload_file') as mock_upload:
                mock_upload.return_value = CloudFileMetadata(
                    filename="test.jpg",
                    s3_key="test/test.jpg",
                    bucket="test-bucket",
                    size=10,
                    content_type="image/jpeg",
                    etag='"etag"',
                    last_modified="2024-01-01T00:00:00Z"
                )

                result = await self.manager.sync_local_to_cloud(local_dir, "sync/")

                assert result['total_files'] == 3  # Should find all files recursively
                assert result['cloud_prefix'] == "sync/"
                assert mock_upload.call_count == 3

    @pytest.mark.asyncio
    async def test_get_health_status_initialized(self):
        """Test health status when initialized"""
        self.manager.initialized = True

        with patch.object(self.manager.wasabi, 'get_storage_stats') as mock_stats:
            mock_stats.return_value = {
                "healthy": True,
                "bucket_name": "test-bucket"
            }

            health = await self.manager.get_health_status()

            assert health['healthy'] is True
            assert health['initialized'] is True
            assert 'wasabi' in health

    @pytest.mark.asyncio
    async def test_get_health_status_not_initialized(self):
        """Test health status when not initialized"""
        self.manager.initialized = False

        health = await self.manager.get_health_status()

        assert health['healthy'] is False
        assert health['initialized'] is False
        assert health['error'] == "Not initialized"


class TestIntegrationScenarios:
    """Test integration scenarios for cloud storage"""

    @pytest.mark.asyncio
    async def test_complete_upload_download_cycle(self):
        """Test complete upload and download cycle"""
        config = {
            'bucket_name': 'test-bucket',
            'region': 's3.ap-northeast-1.wasabisys.com'
        }

        with patch('src.core.cloud_storage.get_secure_credential') as mock_get:
            mock_get.side_effect = lambda service, key: {
                ('wasabi', 'access_key'): 'test_access',
                ('wasabi', 'secret_key'): 'test_secret'
            }.get((service, key))

            with patch('src.core.cloud_storage.boto3') as mock_boto3:
                mock_client = MagicMock()
                mock_boto3.client.return_value = mock_client

                manager = CloudStorageManager(config)
                await manager.initialize()

                # Create test file
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    test_content = b"test file content for upload/download"
                    temp_file.write(test_content)
                    upload_path = Path(temp_file.name)

                try:
                    download_path = upload_path.with_suffix('.downloaded')

                    # Mock upload
                    with patch('src.core.cloud_storage.AsyncRetry') as mock_retry:
                        mock_retry.return_value = lambda func: func

                        mock_client.upload_file.return_value = {
                            'ETag': '"test-etag"',
                            'LastModified': "2024-01-01T00:00:00Z"
                        }

                        # Upload file
                        upload_result = await manager.wasabi.upload_file(
                            upload_path, "test-cycle.txt"
                        )
                        assert upload_result is not None
                        assert upload_result.filename == upload_path.name

                        # Mock download
                        mock_client.download_file.return_value = None
                        mock_client.head_object.return_value = {
                            'ContentLength': len(test_content),
                            'ContentType': 'text/plain',
                            'ETag': '"test-etag"',
                            'LastModified': "2024-01-01T00:00:00Z"
                        }

                        # Download file
                        download_result = await manager.wasabi.download_file(
                            "test-cycle.txt", download_path
                        )
                        assert download_result is not None
                        assert download_result.size == len(test_content)

                finally:
                    os.unlink(upload_path)
                    if download_path.exists():
                        os.unlink(download_path)


# Performance test
@pytest.mark.performance
class TestPerformanceScenarios:
    """Test performance scenarios for cloud storage"""

    @pytest.mark.asyncio
    async def test_concurrent_uploads(self):
        """Test concurrent upload performance"""
        config = {
            'bucket_name': 'test-bucket',
            'region': 's3.ap-northeast-1.wasabisys.com',
            'max_concurrent_uploads': 5
        }

        with patch('src.core.cloud_storage.get_secure_credential') as mock_get:
            mock_get.side_effect = lambda service, key: {
                ('wasabi', 'access_key'): 'test_access',
                ('wasabi', 'secret_key'): 'test_secret'
            }.get((service, key))

            with patch('src.core.cloud_storage.boto3') as mock_boto3:
                mock_client = MagicMock()
                mock_boto3.client.return_value = mock_client

                manager = CloudStorageManager(config)
                await manager.initialize()

                # Create multiple test files
                test_files = []
                for i in range(5):
                    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                        temp_file.write(f"test content {i}".encode())
                        test_files.append(Path(temp_file.name))

                try:
                    with patch.object(manager.wasabi, 'upload_file') as mock_upload:
                        mock_upload.return_value = CloudFileMetadata(
                            filename="test.txt",
                            s3_key="test/test.txt",
                            bucket="test-bucket",
                            size=20,
                            content_type="text/plain",
                            etag='"etag"',
                            last_modified="2024-01-01T00:00:00Z"
                        )

                        import time
                        start_time = time.time()

                        results = await manager.upload_batch(test_files)

                        end_time = time.time()
                        duration = end_time - start_time

                        assert len(results) == 5
                        assert duration < 5.0  # Should complete within 5 seconds
                        assert mock_upload.call_count == 5

                finally:
                    for file_path in test_files:
                        os.unlink(file_path)
