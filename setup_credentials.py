#!/usr/bin/env python3
"""
Secure Credential Setup Script
Sets up Wasabi S3 and Supabase credentials securely
"""

from src.core.security import store_secure_credential, get_secure_credential, initialize_security

def main():
    print("🔐 Setting up secure cloud credentials...")

    try:
        # Initialize security system first
        print("🔑 Initializing security system...")
        if not initialize_security():
            print("❌ Failed to initialize security system")
            return False
        # Store Wasabi credentials
        print("📦 Setting up Wasabi S3 credentials...")
        store_secure_credential('wasabi', 'access_key', 'QZKY1RP5B7WU8DIE92ZY')
        store_secure_credential('wasabi', 'secret_key', 'DaJHtz0QEpd9mgzruqSqUv4s2UKiUjUkTzzpCw5D')

        # Store Supabase credentials
        print("🗄️  Setting up Supabase credentials...")
        store_secure_credential('supabase', 'url', 'https://xewniavplpocctogfgnc.supabase.co')
        store_secure_credential('supabase', 'anon_key', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhld25pYXZwbHBvY2N0b2dmZ25jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTU2OTc0MjIsImV4cCI6MjA3MTI3MzQyMn0.ZpR_iqwYqFzueMjRcvUzS__L1GBT6Ak7HkA8x75KGpA')

        print("✅ Credentials stored securely!")

        # Verify credentials
        print("\n🔍 Verifying credential storage...")
        wasabi_key = get_secure_credential('wasabi', 'access_key')
        wasabi_secret = get_secure_credential('wasabi', 'secret_key')
        supabase_url = get_secure_credential('supabase', 'url')
        supabase_key = get_secure_credential('supabase', 'anon_key')

        print(f"Wasabi Access Key: {'✅' if wasabi_key else '❌'}")
        print(f"Wasabi Secret Key: {'✅' if wasabi_secret else '❌'}")
        print(f"Supabase URL: {'✅' if supabase_url else '❌'}")
        print(f"Supabase Key: {'✅' if supabase_key else '❌'}")

        if wasabi_key and wasabi_secret and supabase_url and supabase_key:
            print("\n🎉 All credentials verified successfully!")
            print("🚀 Ready to proceed with cloud integration testing!")
            return True
        else:
            print("\n❌ Some credentials failed verification!")
            return False

    except Exception as e:
        print(f"❌ Error setting up credentials: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
