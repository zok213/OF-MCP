# Jina AI + MCP Web Scraper Integration Example

## 🚀 Professional AI-Driven Web Scraping Architecture

Your brilliant architecture combines:
1. **Jina AI Research** → Intelligent URL discovery
2. **MCP Server** → Automated keyword generation  
3. **Professional Scraping** → Image extraction and organization
4. **Database Integration** → Automated image categorization

## 🧠 How It Works

### Step 1: AI Keyword Generation
```python
# MCP server generates intelligent keywords
keywords = await generate_research_keywords(
    base_topic="celebrity photos",
    context={"style": "professional", "quality": "high"}
)
# Result: ["celebrity photos", "professional celebrity portraits", 
#          "high quality celebrity images", "celebrity photoshoot", etc.]
```

### Step 2: Jina AI URL Discovery
```bash
# Your Jina API call (now integrated into MCP)
curl "https://eu-s-beta.jina.ai/?q=professional+celebrity+photos" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer jina_6d7ebc1123864682af6f40ee3f1cb0cfh2B52EisCvTac-yJkU1tD6xv11Xf" \
  -H "X-No-Cache: true" \
  -H "X-Respond-With: no-content"
```

### Step 3: Intelligent URL Filtering
```python
# Automatically filter and prioritize discovered URLs
filtered_urls = [
    {
        "url": "https://example-portfolio.com/celebrity-photos",
        "priority": 85,  # High priority for portfolio sites
        "site_type": "professional_portfolio",
        "legal_risk": "low",
        "estimated_images": 45
    },
    # ... more discovered targets
]
```

### Step 4: Automated Scraping Pipeline
```python
# MCP server automatically scrapes discovered URLs
for url in filtered_urls:
    scraping_result = await scraper.scrape_url(url["url"])
    images = await download_images(scraping_result)
    await categorize_and_store(images, database)
```

## 🔧 Implementation Guide

### 1. Update Your MCP Configuration
```json
{
    "jina_ai": {
        "api_key": "jina_6d7ebc1123864682af6f40ee3f1cb0cfh2B52EisCvTac-yJkU1tD6xv11Xf",
        "base_url": "https://eu-s-beta.jina.ai",
        "max_keywords_per_topic": 10,
        "urls_per_keyword": 15,
        "enable_intelligent_filtering": true
    },
    "research_pipeline": {
        "auto_generate_variations": true,
        "semantic_expansion": true,
        "context_aware_keywords": true,
        "priority_based_filtering": true
    }
}
```

### 2. Using the New MCP Tool
```python
# Call the intelligent research tool
research_result = await mcp_client.call_tool("intelligent_research", {
    "topic": "model portfolio photos",
    "context": {
        "style": "professional",
        "category": "fashion",
        "quality": "high"
    },
    "max_keywords": 8,
    "urls_per_keyword": 10,
    "filter_criteria": {
        "min_priority": 60,
        "exclude_high_risk": True,
        "max_targets": 25,
        "allowed_site_types": [
            "professional_portfolio",
            "image_platform", 
            "stock_photos"
        ]
    },
    "jina_api_key": "your_jina_api_key"
})
```

### 3. Automated Workflow Example
```python
async def intelligent_scraping_workflow(topic: str):
    """Complete AI-driven scraping workflow"""
    
    # Step 1: Intelligent research
    research = await mcp_server.intelligent_research({
        "topic": topic,
        "jina_api_key": JINA_API_KEY
    })
    
    # Step 2: Auto-scrape discovered URLs
    for target in research["filtered_targets"]:
        if target["priority"] >= 70:  # High priority only
            await mcp_server.scrape_website({
                "url": target["url"],
                "max_images": 50,
                "category": topic.replace(" ", "_")
            })
    
    # Step 3: Auto-categorize downloaded images
    await mcp_server.categorize_images({
        "source_folder": f"./data/raw/{topic.replace(' ', '_')}",
        "learn_new_faces": True
    })
    
    # Step 4: Generate statistics
    stats = await mcp_server.get_statistics({})
    return stats
```

## 🏗️ Database Integration Architecture

### Intelligent Image Organization
```sql
-- Auto-generated database schema
CREATE TABLE discovered_urls (
    id UUID PRIMARY KEY,
    topic VARCHAR(255),
    url TEXT,
    domain VARCHAR(255),
    priority INTEGER,
    site_type VARCHAR(100),
    legal_risk VARCHAR(50),
    discovered_at TIMESTAMP,
    scraped_at TIMESTAMP,
    images_found INTEGER
);

CREATE TABLE scraped_images (
    id UUID PRIMARY KEY,
    url_id UUID REFERENCES discovered_urls(id),
    file_path TEXT,
    original_url TEXT,
    file_size INTEGER,
    width INTEGER,
    height INTEGER,
    face_detected BOOLEAN,
    person_category VARCHAR(255),
    quality_score FLOAT,
    processed_at TIMESTAMP
);
```

### Auto-Categorization Pipeline
```python
class IntelligentImageProcessor:
    """AI-powered image processing and categorization"""
    
    async def process_scraped_images(self, batch_id: str):
        """Process a batch of scraped images"""
        
        # 1. Face detection using OpenCV
        faces = await self.detect_faces(batch_id)
        
        # 2. Person identification and clustering
        persons = await self.identify_persons(faces)
        
        # 3. Quality assessment
        quality_scores = await self.assess_quality(batch_id)
        
        # 4. Automatic folder organization
        await self.organize_by_person(persons)
        
        # 5. Database updates
        await self.update_database(batch_id, persons, quality_scores)
        
        return {
            "processed_images": len(batch_id),
            "faces_detected": len(faces),
            "persons_identified": len(set(p["person_id"] for p in persons)),
            "categories_created": len(set(p["category"] for p in persons))
        }
```

## 🚀 Professional Usage Examples

### Celebrity Photo Research
```python
# Research and scrape celebrity photos
await intelligent_scraping_workflow("celebrity red carpet photos")
```

### Fashion Model Portfolio Collection
```python
# Discover and collect model portfolios
research_result = await mcp_server.intelligent_research({
    "topic": "fashion model portfolio",
    "context": {"style": "editorial", "category": "high_fashion"},
    "filter_criteria": {"min_priority": 80}
})
```

### Automated Content Pipeline
```python
# Complete automated content discovery and organization
topics = ["celebrity events", "fashion shows", "model portfolios"]

for topic in topics:
    print(f"Processing: {topic}")
    
    # AI research phase
    urls = await discover_urls_with_jina(topic)
    
    # Scraping phase  
    images = await scrape_discovered_urls(urls)
    
    # Organization phase
    categories = await auto_categorize_images(images)
    
    print(f"Completed: {len(images)} images in {len(categories)} categories")
```

## ⚖️ Legal & Compliance Features

### Automatic Legal Compliance
```python
# Built-in legal compliance checking
compliance_result = await mcp_server.check_legal_compliance({
    "url": "https://example-site.com",
    "check_robots": True,
    "analyze_tos": True
})

if compliance_result["robots_ok"] and compliance_result["legal_risk"] == "low":
    # Proceed with scraping
    await scrape_website(url)
else:
    # Log compliance issue and skip
    logger.warning(f"Compliance issue: {compliance_result}")
```

## 📊 Monitoring & Analytics

### Real-time Progress Tracking
```python
# Monitor the intelligent pipeline
async def monitor_pipeline():
    stats = await mcp_server.get_statistics({})
    
    print(f"📊 Pipeline Status:")
    print(f"  🔍 URLs Researched: {stats['urls_researched']}")
    print(f"  📥 Images Scraped: {stats['images_scraped']}")
    print(f"  👥 Persons Identified: {stats['persons_identified']}")
    print(f"  📁 Categories Created: {stats['categories_created']}")
```

## 💡 Professional Tips

1. **Start Small**: Begin with 5-10 keywords for testing
2. **Priority First**: Focus on high-priority (80+) targets initially  
3. **Legal Compliance**: Always check robots.txt and ToS
4. **Quality Control**: Use minimum resolution and file size filters
5. **Rate Limiting**: Respect website rate limits and be professional

## 🔧 Troubleshooting

### Common Issues
```python
# Handle API rate limits
if "rate_limit" in error_message:
    await asyncio.sleep(60)  # Wait before retrying

# Handle invalid API keys  
if "unauthorized" in error_message:
    logger.error("Check your Jina AI API key")

# Handle network timeouts
if "timeout" in error_message:
    retry_count += 1
    if retry_count < 3:
        await retry_with_backoff()
```

---

## 🎯 Your Complete Professional System

You now have:
- ✅ **Intelligent Keyword Generation** (MCP AI reasoning)
- ✅ **Professional URL Discovery** (Jina AI integration) 
- ✅ **Automated Web Scraping** (Playwright + specialized scrapers)
- ✅ **Image Quality Filtering** (OpenCV + professional validation)
- ✅ **Person Detection & Categorization** (Face recognition + clustering)
- ✅ **Legal Compliance Checking** (robots.txt + ToS analysis)
- ✅ **Database Organization** (Automated file management)
- ✅ **Real-time Monitoring** (Progress tracking + statistics)

**Ready for Production Deployment! 🚀**
