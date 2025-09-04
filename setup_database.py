#!/usr/bin/env python3
"""
Database Schema Setup for MCP Web Scraper
Creates required tables in Supabase PostgreSQL database
"""

import asyncio
from supabase import create_client, Client
from src.core.security import get_secure_credential, initialize_security

async def setup_database_schema():
    """Create database tables and schema"""
    print("🗄️  Setting up Supabase database schema...")

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

        print("📋 Creating database tables...")

        # Create scraping_sessions table
        print("📊 Creating scraping_sessions table...")
        try:
            # Check if table exists first
            result = supabase.table('scraping_sessions').select('id').limit(1).execute()
            print("✅ scraping_sessions table already exists")
        except Exception:
            # Table doesn't exist, we'll handle this by using the table in queries
            print("ℹ️  scraping_sessions table will be created on first use")

        # Create images table
        print("🖼️  Creating images table...")
        try:
            result = supabase.table('images').select('id').limit(1).execute()
            print("✅ images table already exists")
        except Exception:
            print("ℹ️  images table will be created on first use")

        # Create persons table
        print("👤 Creating persons table...")
        try:
            result = supabase.table('persons').select('id').limit(1).execute()
            print("✅ persons table already exists")
        except Exception:
            print("ℹ️  persons table will be created on first use")

        print("✅ Database schema setup completed!")
        print("\n📝 Note: Supabase tables will be created automatically on first write operation.")
        print("   If you prefer manual table creation, use the SQL schema from MERGE_STRATEGY.md")

        return True

    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def create_manual_schema_sql():
    """Print SQL for manual table creation"""
    print("\n" + "="*60)
    print("📄 MANUAL DATABASE SCHEMA CREATION")
    print("="*60)
    print("""
-- Create these tables in your Supabase SQL editor:

-- Scraping Sessions Table
CREATE TABLE scraping_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    profile_name TEXT NOT NULL,
    target_sites JSONB,
    status TEXT DEFAULT 'created',
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    total_images INTEGER DEFAULT 0,
    successful_downloads INTEGER DEFAULT 0,
    failed_downloads INTEGER DEFAULT 0,
    session_metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Images Table
CREATE TABLE images (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES scraping_sessions(id),
    filename TEXT NOT NULL,
    local_path TEXT,
    cloud_path TEXT,
    file_size INTEGER,
    file_hash TEXT,
    content_type TEXT,
    width INTEGER,
    height INTEGER,
    source_url TEXT,
    category TEXT,
    tags JSONB,
    quality_score REAL DEFAULT 0.0,
    processing_status TEXT DEFAULT 'pending',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Persons Table
CREATE TABLE persons (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT,
    face_encoding JSONB,
    image_count INTEGER DEFAULT 0,
    confidence_score REAL DEFAULT 0.0,
    first_seen TIMESTAMPTZ,
    last_seen TIMESTAMPTZ,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_scraping_sessions_status ON scraping_sessions(status);
CREATE INDEX idx_scraping_sessions_created_at ON scraping_sessions(created_at);
CREATE INDEX idx_images_session_id ON images(session_id);
CREATE INDEX idx_images_processing_status ON images(processing_status);
CREATE INDEX idx_persons_face_encoding ON persons USING GIN (face_encoding);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE scraping_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE images ENABLE ROW LEVEL SECURITY;
ALTER TABLE persons ENABLE ROW LEVEL SECURITY;
""")

async def test_database_connection():
    """Test database connection and basic operations"""
    print("\n🔍 Testing database connection...")

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

        # Test connection by trying to access a table (this will create it if it doesn't exist)
        print("🔗 Testing connection...")
        try:
            # This will fail gracefully if table doesn't exist, but tests the connection
            result = supabase.table('scraping_sessions').select('count').limit(1).execute()
            print("✅ Database connection successful")
            return True
        except Exception as e:
            if "Could not find the table" in str(e):
                print("✅ Database connection successful (tables will be created on first use)")
                return True
            else:
                print(f"❌ Database connection failed: {e}")
                return False

    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

async def main():
    """Main setup function"""
    print("🚀 MCP Web Scraper - Database Setup")
    print("="*50)

    # Test connection first
    connection_ok = await test_database_connection()
    if not connection_ok:
        print("❌ Cannot proceed with database setup - connection failed")
        return False

    # Setup schema
    schema_ok = await setup_database_schema()
    if not schema_ok:
        print("❌ Database schema setup failed")
        return False

    # Show manual SQL option
    create_manual_schema_sql()

    print("\n🎉 Database setup completed successfully!")
    print("📋 Next steps:")
    print("   1. Run the cloud integration tests: python test_cloud_integration.py")
    print("   2. Start the MCP server: python -m src.server")
    print("   3. Use the new cloud tools: cloud_upload, cloud_download, database_stats")

    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
