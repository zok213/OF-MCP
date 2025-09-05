# 🛠️ Installation & Quick Fix Guide

## 🚀 Quick Setup (Recommended)

Run the automated setup script:

```bash
python setup.py
```

This will:

- ✅ Install all dependencies
- ✅ Create necessary directories
- ✅ Set up environment files
- ✅ Validate installation

## 🔧 Manual Installation

If the automated setup fails, follow these steps:

### 1. Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Install environment loading utility
pip install python-dotenv>=1.0.0
```

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use your preferred editor
```

Required environment variables:

```bash
# Jina AI (for intelligent research)
JINA_API_KEY=your_jina_api_key_here

# Supabase (for RFT integration)
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here
```

### 3. Create Directories

```bash
mkdir -p data/{raw,processed,categorized,metadata}
mkdir -p logs
```

### 4. Setup Supabase Database

```bash
# Run the migration
supabase migration up

# Or manually create tables (see docs/RFT_INTEGRATION.md)
```

## 🐛 Common Issues & Fixes

### Issue: "Import mcp could not be resolved"

**Fix:**

```bash
pip install mcp>=1.1.0
```

### Issue: "Import aiohttp could not be resolved"

**Fix:**

```bash
pip install aiohttp>=3.9.0
```

### Issue: "JINA_API_KEY not configured"

**Fix:**

1. Get API key from https://jina.ai
2. Add to .env file: `JINA_API_KEY=your_key_here`

### Issue: "Supabase integration failed"

**Fix:**

1. Get keys from Supabase project settings
2. Add to .env file:
   ```
   SUPABASE_ANON_KEY=eyJhbGciOiJI...
   SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJI...
   ```
3. Run database migration

### Issue: TypeScript errors in edge functions

**Status:** ⚠️ Expected behavior - these run in Deno runtime, not Node.js

## 🔍 Validation Commands

Test your installation:

```bash
# Check environment health
python -c "from src.utils.env_loader import check_environment_health; print(check_environment_health())"

# Test server startup
python src/server.py --test

# Validate RFT integration
python -c "from src.rft_integration import RFTSupabaseClient; print('RFT OK')"
```

## 🎯 Success Indicators

You should see:

- ✅ All imports resolve without errors
- ✅ Environment variables loaded correctly
- ✅ Supabase connection working
- ✅ MCP server starts without issues

## 📞 Need Help?

If you encounter issues:

1. Check the logs in `logs/` directory
2. Run `python setup.py` again
3. Verify all environment variables are set
4. Check Supabase database tables exist

## 🔒 Security Notes

- Never commit `.env` files to version control
- Use strong, unique API keys
- Rotate credentials regularly
- Monitor access logs

---

**Status:** ✅ All critical issues from the analysis have been addressed
