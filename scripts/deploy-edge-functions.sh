#!/bin/bash

# Supabase Edge Functions Deployment Script for RFT Integration
# This script deploys all the edge functions required for the RFT pipeline

set -e

echo "🚀 Deploying Supabase Edge Functions for RFT Integration"
echo "========================================================"

# Check if Supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "❌ Supabase CLI not found. Please install it first:"
    echo "   npm install -g supabase"
    exit 1
fi

# Check if we're in a Supabase project
if [ ! -f "supabase/config.toml" ]; then
    echo "❌ Not in a Supabase project directory"
    echo "💡 Run 'supabase init' first or navigate to your project directory"
    exit 1
fi

echo "📋 Functions to deploy:"
echo "  1. upload - Image upload with metadata"
echo "  2. rft-responses - RFT responses management"
echo "  3. rft-rewards - RFT rewards management" 
echo "  4. rft-checkpoints - RFT checkpoints management"
echo ""

# Deploy upload function
echo "📤 Deploying upload function..."
if supabase functions deploy upload; then
    echo "✅ Upload function deployed successfully"
else
    echo "❌ Failed to deploy upload function"
    exit 1
fi

# Deploy RFT responses function
echo "📝 Deploying rft-responses function..."
if supabase functions deploy rft-responses; then
    echo "✅ RFT responses function deployed successfully"
else
    echo "❌ Failed to deploy rft-responses function"
    exit 1
fi

# Deploy RFT rewards function
echo "🎯 Deploying rft-rewards function..."
if supabase functions deploy rft-rewards; then
    echo "✅ RFT rewards function deployed successfully"
else
    echo "❌ Failed to deploy rft-rewards function"
    exit 1
fi

# Deploy RFT checkpoints function
echo "💾 Deploying rft-checkpoints function..."
if supabase functions deploy rft-checkpoints; then
    echo "✅ RFT checkpoints function deployed successfully"
else
    echo "❌ Failed to deploy rft-checkpoints function"
    exit 1
fi

echo ""
echo "🎉 All edge functions deployed successfully!"
echo ""
echo "📋 Next steps:"
echo "  1. Create storage bucket 'scraped-images' in Supabase dashboard"
echo "  2. Set up RLS (Row Level Security) policies for the tables"
echo "  3. Update your environment variables:"
echo "     - SUPABASE_URL"
echo "     - SUPABASE_ANON_KEY"
echo "     - SUPABASE_SERVICE_ROLE_KEY (for admin operations)"
echo ""
echo "🔗 Your functions are available at:"
echo "  • https://YOUR_PROJECT_ID.supabase.co/functions/v1/upload"
echo "  • https://YOUR_PROJECT_ID.supabase.co/functions/v1/rft-responses"
echo "  • https://YOUR_PROJECT_ID.supabase.co/functions/v1/rft-rewards"
echo "  • https://YOUR_PROJECT_ID.supabase.co/functions/v1/rft-checkpoints"
echo ""
echo "✨ RFT integration is ready to use!"
