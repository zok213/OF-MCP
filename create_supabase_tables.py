#!/usr/bin/env python3
"""
Manually create Supabase tables for MCP Web Scraper
"""

import asyncio
from supabase import create_client, Client
from src.core.security import get_secure_credential, initialize_security

async def create_tables_manually():
    """Create tables by attempting insert operations (Supabase auto-creates)"""
    print("🔨 Creating Supabase tables through insert operations...")

    try:
        # Initialize security and get credentials
        if not initialize_security():
            print("❌ Failed to initialize security system")
            return False

        supabase_url = get_secure_credential('supabase', 'url')
        supabase_key = get_secure_credential('supabase', 'anon_key')

        if not supabase_url or not supabase_key:
            print("❌ Supabase credentials not found")
            return False

        # Initialize Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)

        print("📊 Creating scraping_sessions table...")
        try:
            # Try to insert a dummy record to create the table
            dummy_session = {
                "profile_name": "setup_test",
                "target_sites": ["https://example.com"],
                "status": "setup",
                "total_images": 0,
                "successful_downloads": 0,
                "failed_downloads": 0,
                "session_metadata": {}
            }
            result = supabase.table('scraping_sessions').insert(dummy_session).execute()
            print("✅ scraping_sessions table created and record inserted")

            # Clean up the dummy record
            if result.data:
                session_id = result.data[0]['id']
                supabase.table('scraping_sessions').delete().eq('id', session_id).execute()
                print("🧹 Cleaned up dummy record")

        except Exception as e:
            print(f"⚠️  scraping_sessions table creation: {e}")

        print("🖼️  Creating images table...")
        try:
            # Try to insert a dummy record to create the table
            dummy_image = {
                "session_id": "00000000-0000-0000-0000-000000000000",  # Dummy UUID
                "filename": "setup_test.jpg",
                "local_path": "/tmp/setup_test.jpg",
                "file_size": 1024,
                "file_hash": "setup_hash",
                "content_type": "image/jpeg",
                "source_url": "https://example.com/setup.jpg",
                "category": "setup",
                "tags": ["setup"],
                "quality_score": 1.0,
                "processing_status": "completed"
            }
            result = supabase.table('images').insert(dummy_image).execute()
            print("✅ images table created and record inserted")

            # Clean up the dummy record
            if result.data:
                image_id = result.data[0]['id']
                supabase.table('images').delete().eq('id', image_id).execute()
                print("🧹 Cleaned up dummy record")

        except Exception as e:
            print(f"⚠️  images table creation: {e}")

        print("👤 Creating persons table...")
        try:
            # Try to insert a dummy record to create the table
            dummy_person = {
                "name": "Setup Test Person",
                "face_encoding": [0.1, 0.2, 0.3],
                "image_count": 1,
                "confidence_score": 0.9
            }
            result = supabase.table('persons').insert(dummy_person).execute()
            print("✅ persons table created and record inserted")

            # Clean up the dummy record
            if result.data:
                person_id = result.data[0]['id']
                supabase.table('persons').delete().eq('id', person_id).execute()
                print("🧹 Cleaned up dummy record")

        except Exception as e:
            print(f"⚠️  persons table creation: {e}")

        print("\n🎉 Table creation process completed!")
        print("📋 Tables should now be available for the MCP Web Scraper.")
        return True

    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        return False

async def test_tables_exist():
    """Test if tables exist by trying to select from them"""
    print("\n🔍 Testing table existence...")

    try:
        # Initialize security and get credentials
        if not initialize_security():
            print("❌ Failed to initialize security system")
            return False

        supabase_url = get_secure_credential('supabase', 'url')
        supabase_key = get_secure_credential('supabase', 'anon_key')

        if not supabase_url or not supabase_key:
            print("❌ Supabase credentials not found")
            return False

        # Initialize Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)

        tables = ['scraping_sessions', 'images', 'persons']
        existing_tables = []

        for table in tables:
            try:
                result = supabase.table(table).select('count').limit(1).execute()
                existing_tables.append(table)
                print(f"✅ {table}: EXISTS")
            except Exception as e:
                if "Could not find the table" in str(e):
                    print(f"❌ {table}: DOES NOT EXIST")
                else:
                    print(f"⚠️  {table}: ERROR - {e}")

        if len(existing_tables) == len(tables):
            print(f"\n🎉 All {len(tables)} tables exist and are accessible!")
            return True
        else:
            print(f"\n⚠️  Only {len(existing_tables)}/{len(tables)} tables exist.")
            return False

    except Exception as e:
        print(f"❌ Table testing failed: {e}")
        return False

async def main():
    """Main function"""
    print("🚀 MCP Web Scraper - Supabase Table Creation")
    print("="*50)

    # First test current state
    tables_exist = await test_tables_exist()

    if not tables_exist:
        print("\n📋 Creating missing tables...")
        success = await create_tables_manually()

        if success:
            print("\n🔍 Re-testing table existence...")
            await test_tables_exist()
    else:
        print("\n✅ All tables already exist!")

    print("\n📋 Next steps:")
    print("   1. Run the cloud integration tests: python test_cloud_integration.py")
    print("   2. Start the MCP server: python -m src.server")
    print("   3. Use the new cloud tools: cloud_upload, cloud_download, database_stats")

if __name__ == "__main__":
    asyncio.run(main())
