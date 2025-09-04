# 🤖 RFT (Reinforcement Fine-tuning) Integration

This document describes the RFT integration for the OF-MCP web scraper, which enables automatic training data collection and reinforcement learning workflows.

## 🧠 Overview

The RFT integration connects the web scraping pipeline with a reinforcement fine-tuning system, following this workflow:

```
🕷️ Web Scraping → 📤 Image Upload → 🤖 Response Generation → 🎯 Human Feedback → 💾 Model Training
```

### Architecture Components

1. **Supabase Edge Functions** - Handle uploads, responses, rewards, and checkpoints
2. **Python RFT Client** - Integrates with the MCP scraper
3. **Database Schema** - Stores training data, feedback, and model checkpoints
4. **MCP Tools** - Provides RFT functionality through the MCP interface

## 📋 Database Schema

### Core Tables

- **`images`** - Stores uploaded image metadata
- **`responses`** - Model responses for training data
- **`rewards`** - Human feedback scores (-1 to 1)
- **`checkpoints`** - Model versions and deployment status

### Relationships

```
images ← responses ← rewards
checkpoints (independent)
```

## 🚀 Setup Instructions

### 1. Database Setup

Run the migration to create all necessary tables:

```sql
-- Apply the migration file
\i supabase/migrations/20240904000001_rft_integration_setup.sql
```

### 2. Edge Functions Deployment

Deploy all edge functions using the provided script:

```bash
chmod +x scripts/deploy-edge-functions.sh
./scripts/deploy-edge-functions.sh
```

Or deploy individually:

```bash
supabase functions deploy upload
supabase functions deploy rft-responses
supabase functions deploy rft-rewards
supabase functions deploy rft-checkpoints
```

### 3. Configuration

Update your `config/mcp_config.json`:

```json
{
  "supabase": {
    "url": "https://your-project.supabase.co",
    "anon_key": "your-anon-key",
    "service_role_key": "your-service-role-key",
    "storage_bucket": "scraped-images",
    "rft_integration": {
      "enabled": true,
      "auto_process_scraped_images": true,
      "default_user_id": "mcp-scraper",
      "generate_training_prompts": true
    }
  }
}
```

### 4. Install Dependencies

Ensure you have the required Python packages:

```bash
pip install aiohttp
```

## 🔧 Usage

### MCP Tools

The integration adds 4 new MCP tools:

#### `rft_process_images`

Process scraped images for RFT training:

```json
{
  "tool": "rft_process_images",
  "arguments": {
    "image_paths": ["/path/to/image1.jpg", "/path/to/image2.jpg"],
    "context": {
      "url": "https://source-website.com",
      "category": "fashion",
      "quality_score": 0.85
    },
    "user_id": "scraper-session-1"
  }
}
```

#### `rft_create_reward`

Create reward feedback for responses:

```json
{
  "tool": "rft_create_reward",
  "arguments": {
    "response_id": "uuid-of-response",
    "feedback": {
      "type": "like",
      "quality": 4,
      "comments": "Great description"
    }
  }
}
```

#### `rft_get_statistics`

Get comprehensive training statistics:

```json
{
  "tool": "rft_get_statistics",
  "arguments": {}
}
```

#### `rft_manage_checkpoints`

Manage model checkpoints:

```json
{
  "tool": "rft_manage_checkpoints",
  "arguments": {
    "action": "create",
    "checkpoint_data": {
      "version": "v1.2.0",
      "storage_key": "models/checkpoint-v1.2.0.safetensors",
      "epoch": 50,
      "avg_reward": 0.82,
      "is_active": true
    }
  }
}
```

### Automatic Integration

When you use the `scrape_website` tool, images are automatically processed for RFT if the integration is enabled:

```json
{
  "tool": "scrape_website",
  "arguments": {
    "url": "https://example.com",
    "max_images": 20,
    "category": "fashion"
  }
}
```

This will:

1. Scrape images from the website
2. Upload them to Supabase storage
3. Generate training prompts
4. Create response records
5. Prepare data for reinforcement learning

## 🐍 Python API

### Direct Usage

```python
from src.rft_integration import RFTSupabaseClient, RFTTrainingManager

# Initialize client
client = RFTSupabaseClient("https://your-project.supabase.co", "your-anon-key")

# Process scraping results
manager = RFTTrainingManager(client, config)
result = await manager.integrate_scraping_session(scraping_result)

# Create rewards
feedback = {"type": "like", "quality": 4, "comments": "Excellent"}
reward = await manager.create_reward_feedback(response_id, feedback)

# Get statistics
stats = await manager.get_training_statistics()
```

### Integration with Scraper

```python
from src.rft_integration import integrate_with_mcp_scraper

# Integrate scraping results with RFT
scraper_result = {
    "url": "https://example.com",
    "images": [{"local_path": "/path/to/img.jpg"}],
    "category": "fashion"
}

supabase_config = {
    "url": "https://your-project.supabase.co",
    "anon_key": "your-anon-key"
}

result = await integrate_with_mcp_scraper(scraper_result, supabase_config)
```

## 📊 Edge Functions API

### Upload Function

**POST** `/functions/v1/upload`

Upload images with metadata:

```javascript
const formData = new FormData();
formData.append("file", fileBlob);
formData.append("user_id", "user-123");
formData.append("category", "fashion");
formData.append("metadata", JSON.stringify({ additional: "data" }));

const response = await fetch("/functions/v1/upload", {
  method: "POST",
  body: formData,
});
```

### RFT Responses Function

**POST** `/functions/v1/rft-responses`

Create training responses:

```javascript
const response = await fetch("/functions/v1/rft-responses", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    user_id: "user-123",
    prompt: "Describe this image",
    response_text: "This image shows...",
    model_id: "gpt-4-vision",
    metadata: { image_id: "img-123" },
  }),
});
```

**GET** `/functions/v1/rft-responses`

Retrieve responses with filtering:

```javascript
const url = "/functions/v1/rft-responses?user_id=user-123&limit=50&offset=0";
const response = await fetch(url);
```

### RFT Rewards Function

**POST** `/functions/v1/rft-rewards`

Create reward feedback:

```javascript
const response = await fetch("/functions/v1/rft-rewards", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    response_id: "response-uuid",
    score: 0.8,
    detail: "High quality response",
  }),
});
```

**GET** `/functions/v1/rft-rewards`

Get rewards with statistics:

```javascript
const url = "/functions/v1/rft-rewards?min_score=0.5&limit=100";
const response = await fetch(url);
```

### RFT Checkpoints Function

**POST** `/functions/v1/rft-checkpoints`

Create model checkpoints:

```javascript
const response = await fetch("/functions/v1/rft-checkpoints", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    version: "v1.0.0",
    storage_key: "models/checkpoint.safetensors",
    epoch: 10,
    avg_reward: 0.75,
    is_active: true,
  }),
});
```

**GET** `/functions/v1/rft-checkpoints`

List checkpoints:

```javascript
const url = "/functions/v1/rft-checkpoints?active_only=true";
const response = await fetch(url);
```

## 🎯 Training Workflow

### 1. Data Collection Phase

```python
# Scrape images
scraping_result = await scraper.scrape_url("https://example.com")

# Process for RFT
rft_result = await rft_manager.integrate_scraping_session(scraping_result)
```

### 2. Response Generation Phase

```python
# Generate training prompts and responses
training_data = await processor.create_rft_training_data(processed_images)
```

### 3. Human Feedback Phase

```python
# Collect human feedback
feedback = {"type": "like", "quality": 4, "comments": "Good description"}
reward = await manager.create_reward_feedback(response_id, feedback)
```

### 4. Model Training Phase

```python
# Create checkpoint after training
checkpoint = await client.create_checkpoint(
    version="v1.1.0",
    storage_key="models/improved-model.safetensors",
    epoch=20,
    avg_reward=0.85,
    is_active=True
)
```

## 📈 Monitoring & Statistics

### Real-time Statistics

```python
stats = await manager.get_training_statistics()

print(f"Responses: {stats['responses']['total']}")
print(f"Average Reward: {stats['rewards']['avg_score']}")
print(f"Training Status: {stats['training_readiness']['status']}")
```

### Database Views

Use the pre-built views for analytics:

```sql
-- Get training data with rewards
SELECT * FROM public.training_data_view
WHERE reward_score > 0.5
ORDER BY response_created_at DESC;

-- Get overall statistics
SELECT * FROM public.rft_statistics_view;
```

## 🔒 Security Considerations

1. **Row Level Security (RLS)** - Enabled on all tables
2. **API Key Management** - Use environment variables
3. **File Validation** - Edge functions validate file types and sizes
4. **User Authentication** - Supabase Auth integration
5. **Storage Policies** - Controlled access to uploaded files

## 🐛 Troubleshooting

### Common Issues

1. **Edge Functions Not Responding**

   ```bash
   supabase functions list
   supabase logs --type=functions
   ```

2. **Database Connection Issues**

   ```sql
   SELECT 1; -- Test basic connectivity
   \dt public.*; -- List tables
   ```

3. **Upload Failures**

   - Check file size limits
   - Verify storage bucket exists
   - Confirm API keys are correct

4. **RFT Integration Not Available**
   ```bash
   pip install aiohttp  # Ensure dependencies are installed
   ```

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger("rft-integration").setLevel(logging.DEBUG)
```

## 🚀 Production Deployment

1. **Environment Variables**

   ```bash
   export SUPABASE_URL="https://your-project.supabase.co"
   export SUPABASE_ANON_KEY="your-anon-key"
   export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
   ```

2. **Scaling Considerations**

   - Use connection pooling for high throughput
   - Monitor storage usage
   - Set up database backups
   - Configure edge function timeouts

3. **Monitoring**
   - Set up Supabase monitoring alerts
   - Monitor API usage and quotas
   - Track training progress metrics

## 📚 Examples

See `examples/rft_workflow_demo.py` for a complete demonstration of the RFT integration workflow.

## 🤝 Contributing

When contributing to the RFT integration:

1. Follow the existing database schema
2. Maintain backward compatibility
3. Add comprehensive tests
4. Update documentation
5. Consider security implications

## 📄 License

This RFT integration follows the same license as the main OF-MCP project.
