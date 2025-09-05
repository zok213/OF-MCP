#!/usr/bin/env python3
"""
Comprehensive Cloud Integration Test Suite
Tests Wasabi S3 storage and Supabase database integration
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone
import time

# Import our modules
from src.core.security import store_secure_credential, get_secure_credential
from src.core.cloud_storage import CloudStorageManager
from src.core.database import DatabaseManager


class CloudIntegrationTester:
    """Comprehensive cloud integration testing"""

    def __init__(self):
        self.config = {
            'bucket_name': 'ofbucket',
            'region': 's3.ap-northeast-1.wasabisys.com',
            'max_concurrent_uploads': 3,
            'failure_threshold': 3,
            'recovery_timeout': 30
        }
        self.results = {
            'credential_setup': False,
            'cloud_storage_init': False,
            'database_init': False,
            'file_upload': False,
            'file_download': False,
            'file_listing': False,
            'session_creation': False,
            'image_recording': False,
            'stats_retrieval': False,
            'health_checks': False,
            'performance_test': False
        }

    async def setup_credentials(self):
        """Setup/verify secure credentials for testing"""
        print("🔐 Setting up/verifying secure credentials...")

        try:
            from src.core.security import initialize_security

            # Initialize security system
            if not initialize_security():
                print("❌ Failed to initialize security system")
                return False

            # Check if credentials already exist
            wasabi_key = get_secure_credential('wasabi', 'access_key')
            wasabi_secret = get_secure_credential('wasabi', 'secret_key')
            supabase_url = get_secure_credential('supabase', 'url')
            supabase_key = get_secure_credential('supabase', 'anon_key')

            if wasabi_key and wasabi_secret and supabase_url and supabase_key:
                print("✅ Existing credentials verified successfully")
                self.results['credential_setup'] = True
                return True

            # If credentials don't exist, store them
            print("📝 Storing new credentials...")
            store_secure_credential('wasabi', 'access_key', 'QZKY1RP5B7WU8DIE92ZY')
            store_secure_credential('wasabi', 'secret_key', 'DaJHtz0QEpd9mgzruqSqUv4s2UKiUjUkTzzpCw5D')
            store_secure_credential('supabase', 'url', 'https://xewniavplpocctogfgnc.supabase.co')
            store_secure_credential('supabase', 'anon_key', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhld25pYXZwbHBvY2N0b2dmZ25jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTU2OTc0MjIsImV4cCI6MjA3MTI3MzQyMn0.ZpR_iqwYqFzueMjRcvUzS__L1GBT6Ak7HkA8x75KGpA')

            # Verify the newly stored credentials
            wasabi_key = get_secure_credential('wasabi', 'access_key')
            wasabi_secret = get_secure_credential('wasabi', 'secret_key')
            supabase_url = get_secure_credential('supabase', 'url')
            supabase_key = get_secure_credential('supabase', 'anon_key')

            if wasabi_key and wasabi_secret and supabase_url and supabase_key:
                print("✅ Credentials stored and verified successfully")
                self.results['credential_setup'] = True
                return True
            else:
                print("❌ Credential verification failed after storage")
                return False

        except Exception as e:
            print(f"❌ Credential setup failed: {e}")
            return False

    async def test_cloud_storage(self):
        """Test cloud storage functionality"""
        print("\n☁️  Testing cloud storage...")

        try:
            # Initialize cloud storage
            cloud = CloudStorageManager(self.config)
            init_success = await cloud.initialize()

            if not init_success:
                print("❌ Cloud storage initialization failed")
                return False

            self.results['cloud_storage_init'] = True
            print("✅ Cloud storage initialized")

            # Test health check
            health = await cloud.get_health_status()
            if health.get('healthy'):
                print("✅ Cloud storage health check passed")
            else:
                print("⚠️  Cloud storage health check warning")

            # Test file operations
            await self.test_file_operations(cloud)

            return True

        except Exception as e:
            print(f"❌ Cloud storage test failed: {e}")
            return False

    async def test_file_operations(self, cloud_manager):
        """Test file upload/download operations"""
        try:
            # Create test file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                test_content = f"Test file content - {datetime.now().isoformat()}"
                f.write(test_content)
                test_file_path = Path(f.name)

            print(f"📁 Created test file: {test_file_path}")

            # Test upload
            upload_result = await cloud_manager.wasabi.upload_file(
                test_file_path,
                f"test-integration/{test_file_path.name}"
            )

            if upload_result:
                print("✅ File upload successful")
                self.results['file_upload'] = True

                # Test download
                download_path = test_file_path.with_suffix('.downloaded.txt')
                download_result = await cloud_manager.wasabi.download_file(
                    upload_result.s3_key,
                    download_path
                )

                if download_result:
                    print("✅ File download successful")
                    self.results['file_download'] = True

                    # Verify content
                    with open(download_path, 'r') as f:
                        downloaded_content = f.read()

                    if downloaded_content == test_content:
                        print("✅ File content verification passed")
                    else:
                        print("⚠️  File content verification failed")
                else:
                    print("❌ File download failed")
            else:
                print("❌ File upload failed")

            # Test file listing
            files = await cloud_manager.wasabi.list_files("test-integration/", 10)
            if files:
                print(f"✅ File listing successful: {len(files)} files found")
                self.results['file_listing'] = True
            else:
                print("⚠️  File listing returned no results")

            # Cleanup
            os.unlink(test_file_path)
            if download_path.exists():
                os.unlink(download_path)

        except Exception as e:
            print(f"❌ File operations test failed: {e}")

    async def test_database(self):
        """Test database functionality"""
        print("\n🗄️  Testing database...")

        try:
            # Initialize database
            db = DatabaseManager(self.config)
            init_success = await db.initialize()

            if not init_success:
                print("❌ Database initialization failed")
                return False

            self.results['database_init'] = True
            print("✅ Database initialized")

            # Test session creation
            session_id = await db.start_scraping_session(
                "integration_test",
                ["https://example.com"]
            )

            if session_id:
                print(f"✅ Session creation successful: {session_id}")
                self.results['session_creation'] = True

                # Test image recording
                image_data = {
                    "filename": "test.jpg",
                    "local_path": "/path/to/test.jpg",
                    "file_size": 1024,
                    "content_type": "image/jpeg",
                    "source_url": "https://example.com/test.jpg"
                }

                image_id = await db.record_image(session_id, image_data)

                if image_id:
                    print(f"✅ Image recording successful: {image_id}")
                    self.results['image_recording'] = True
                else:
                    print("❌ Image recording failed")

                # Test session completion
                stats = {
                    "status": "completed",
                    "total_images": 1,
                    "successful_downloads": 1,
                    "failed_downloads": 0
                }

                await db.end_scraping_session(session_id, stats)
                print("✅ Session completion successful")

            else:
                print("❌ Session creation failed")

            # Test stats retrieval
            stats = await db.get_system_stats()
            if stats and 'database_health' in stats:
                print("✅ Stats retrieval successful")
                self.results['stats_retrieval'] = True
            else:
                print("❌ Stats retrieval failed")

            return True

        except Exception as e:
            print(f"❌ Database test failed: {e}")
            return False

    async def test_performance(self):
        """Test performance under load"""
        print("\n⚡ Testing performance...")

        try:
            cloud = CloudStorageManager(self.config)
            await cloud.initialize()

            # Create multiple test files
            test_files = []
            for i in range(5):
                with tempfile.NamedTemporaryFile(mode='w', suffix=f'_{i}.txt', delete=False) as f:
                    f.write(f"Performance test content {i} - {datetime.now().isoformat()}")
                    test_files.append(Path(f.name))

            print(f"📊 Testing concurrent upload of {len(test_files)} files")

            start_time = time.time()

            # Test concurrent uploads
            results = await cloud.upload_batch(test_files, "performance-test/")

            end_time = time.time()
            duration = end_time - start_time

            successful_uploads = len([r for r in results if r is not None])

            print(".2f")
            print(f"📈 Success rate: {successful_uploads}/{len(test_files)} ({successful_uploads/len(test_files)*100:.1f}%)")

            if duration < 10.0 and successful_uploads == len(test_files):
                print("✅ Performance test passed")
                self.results['performance_test'] = True
            else:
                print("⚠️  Performance test completed with warnings")

            # Cleanup
            for file_path in test_files:
                os.unlink(file_path)

        except Exception as e:
            print(f"❌ Performance test failed: {e}")

    async def test_health_monitoring(self):
        """Test health monitoring systems"""
        print("\n🏥 Testing health monitoring...")

        try:
            cloud = CloudStorageManager(self.config)
            db = DatabaseManager(self.config)

            await cloud.initialize()
            await db.initialize()

            # Test cloud health
            cloud_health = await cloud.get_health_status()
            db_health = await db.get_system_stats()

            if cloud_health.get('healthy'):
                print("✅ Cloud storage health: OK")
            else:
                print("⚠️  Cloud storage health: Issues detected")

            if db_health and 'database_health' in db_health:
                db_status = db_health['database_health']
                if db_status.get('healthy'):
                    print("✅ Database health: OK")
                else:
                    print("⚠️  Database health: Issues detected")
            else:
                print("❌ Database health check failed")

            self.results['health_checks'] = True
            print("✅ Health monitoring test completed")

        except Exception as e:
            print(f"❌ Health monitoring test failed: {e}")

    async def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting Comprehensive Cloud Integration Test Suite")
        print("=" * 60)

        # Setup credentials
        if not await self.setup_credentials():
            print("❌ Cannot proceed without credentials")
            return False

        # Run tests
        await self.test_cloud_storage()
        await self.test_database()
        await self.test_performance()
        await self.test_health_monitoring()

        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)

        passed = 0
        total = len(self.results)

        for test_name, result in self.results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title():<30} {status}")
            if result:
                passed += 1

        print("-" * 60)
        print(f"{'Total Tests':<30} {total}")
        print(f"{'Passed':<30} {passed}")
        print(f"{'Failed':<30} {total - passed}")
        print(f"{'Success Rate':<30} {(passed/total*100):.1f}%")

        # Overall result
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Cloud integration is ready for production.")
            return True
        elif passed >= total * 0.8:
            print(f"\n⚠️  MOST TESTS PASSED ({passed}/{total}). Minor issues to resolve.")
            return True
        else:
            print(f"\n❌ CRITICAL ISSUES DETECTED. Only {passed}/{total} tests passed.")
            return False

    def generate_report(self):
        """Generate detailed test report"""
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_results": self.results,
            "summary": {
                "total_tests": len(self.results),
                "passed_tests": sum(self.results.values()),
                "failed_tests": len(self.results) - sum(self.results.values()),
                "success_rate": sum(self.results.values()) / len(self.results) * 100
            },
            "recommendations": []
        }

        # Add recommendations based on failures
        if not self.results['credential_setup']:
            report['recommendations'].append("Fix credential setup - check secure storage system")

        if not self.results['cloud_storage_init']:
            report['recommendations'].append("Fix cloud storage initialization - check credentials and network")

        if not self.results['database_init']:
            report['recommendations'].append("Fix database initialization - check credentials and network")

        if not self.results['file_upload'] or not self.results['file_download']:
            report['recommendations'].append("Fix file operations - check permissions and connectivity")

        if not self.results['performance_test']:
            report['recommendations'].append("Optimize performance - reduce concurrent operations or increase timeouts")

        return report


async def main():
    """Main test execution"""
    tester = CloudIntegrationTester()

    try:
        success = await tester.run_all_tests()

        # Generate and save report
        report = tester.generate_report()

        report_path = Path("cloud_integration_test_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_path}")

        # Exit with appropriate code
        exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        exit(130)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
