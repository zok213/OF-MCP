#!/usr/bin/env python3
import asyncio
from src.core.security import initialize_security
from src.core.cloud_storage import CloudStorageManager

async def test_cloud_storage():
    # Initialize security system first
    print('🔐 Initializing security system...')
    if not initialize_security():
        print('❌ Security initialization failed')
        return False

    config = {'bucket_name': 'ofbucket', 'region': 's3.ap-northeast-1.wasabisys.com'}
    cloud = CloudStorageManager(config)

    print('🔄 Initializing cloud storage...')
    success = await cloud.initialize()

    if success:
        print('✅ Cloud storage initialized successfully!')
        health = await cloud.get_health_status()
        print(f'🏥 Health status: {health}')
        return True
    else:
        print('❌ Cloud storage initialization failed')
        return False

if __name__ == "__main__":
    result = asyncio.run(test_cloud_storage())
    print(f'\n🎯 Cloud Storage Test: {"PASSED" if result else "FAILED"}')
