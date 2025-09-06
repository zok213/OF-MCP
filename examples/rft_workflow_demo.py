#!/usr/bin/env python3
"""
Complete RFT Integration Example for Adult Content
Demonstrates the full workflow from adult content scraping to RFT training
"""

import asyncio
import json
import logging
from pathlib import Path
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from rft_integration import (
    RFTSupabaseClient,
    RFTTrainingManager,
    integrate_with_mcp_scraper,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("rft-example")


async def demonstrate_rft_workflow():
    """Demonstrate complete RFT integration workflow for adult content"""

    print("🚀 Adult Content RFT Integration Workflow Demonstration")
    print("=" * 55)

    # Configuration
    supabase_config = {
        "url": "https://xewniavplpocctogfgnc.supabase.co",
        "anon_key": "your-anon-key-here",  # Replace with actual key
    }

    try:
        # Initialize RFT client
        print("\n📡 1. Initializing RFT client...")
        client = RFTSupabaseClient(supabase_config["url"], supabase_config["anon_key"])

        # Initialize training manager
        manager = RFTTrainingManager(client, supabase_config)

        print("✅ RFT client initialized successfully")

        # Simulate adult content scraping results (in real scenario, this comes from MCP scraper)
        print("\n🕷️ 2. Simulating adult content scraping results...")

        # Create some sample adult content files (for demo purposes)
        sample_images_dir = Path("./sample_images")
        sample_images_dir.mkdir(exist_ok=True)

        sample_images = []
        for i in range(3):
            img_path = sample_images_dir / f"sample_adult_image_{i+1}.jpg"
            if not img_path.exists():
                # Create a dummy file for demo
                img_path.write_bytes(b"fake_adult_image_data_for_demo")
            sample_images.append(str(img_path))

        scraper_result = {
            "url": "https://example-adult-site.com/gallery",
            "images": [{"local_path": path} for path in sample_images],
            "category": "hentai_gallery",
            "timestamp": "2024-09-04T10:00:00Z",
            "user_id": "demo-user",
            "avg_quality_score": 0.85,
            "content_type": "nsfw",
            "adult_rating": "18+",
        }

        print(f"📊 Simulated adult content scraping of {len(sample_images)} images")

        # Integrate with RFT pipeline
        print("\n🤖 3. Integrating with RFT pipeline...")

        integration_result = await integrate_with_mcp_scraper(
            scraper_result, supabase_config
        )

        if integration_result.get("success"):
            summary = integration_result.get("summary", {})
            print("✅ RFT integration completed!")
            print(f"📊 Session ID: {integration_result.get('session_id')}")
            print(f"📥 Images processed: {summary.get('processed_images', 0)}")
            print(f"❌ Images failed: {summary.get('failed_images', 0)}")
            print(
                f"📝 Training responses created: {summary.get('responses_created', 0)}"
            )
            print(
                f"🚀 Ready for training: {'Yes' if summary.get('ready_for_training') else 'No'}"
            )
        else:
            print(f"❌ RFT integration failed: {integration_result.get('error')}")
            return

        # Demonstrate response and reward management
        print("\n🎯 4. Demonstrating reward feedback...")

        # Get recent responses
        responses_result = await client.get_responses(limit=5)

        if responses_result.get("success") and responses_result.get("data"):
            recent_responses = responses_result["data"]
            print(f"📝 Found {len(recent_responses)} recent responses")

            # Create sample rewards for demonstration
            for i, response in enumerate(recent_responses[:2]):
                response_id = response["id"]

                # Simulate different types of adult content feedback
                feedback_examples = [
                    {
                        "type": "like",
                        "quality": 4,
                        "comments": "Good adult content categorization",
                    },
                    {
                        "type": "dislike",
                        "quality": 2,
                        "comments": "NSFW content not properly tagged",
                    },
                ]

                feedback = feedback_examples[i % len(feedback_examples)]

                reward_result = await manager.create_reward_feedback(
                    response_id, feedback
                )

                if reward_result.get("success"):
                    reward_data = reward_result["data"]
                    print(f"✅ Created reward for response {response_id[:8]}...")
                    print(f"   Score: {reward_data.get('score')}")
                    print(
                        f"   Feedback: {feedback['type']} (quality: {feedback['quality']})"
                    )
                else:
                    print(f"❌ Failed to create reward: {reward_result.get('error')}")

        # Demonstrate checkpoint management
        print("\n💾 5. Demonstrating checkpoint management...")

        # Create a sample adult content model checkpoint
        checkpoint_data = {
            "version": "v1.0.0-adult-content-demo",
            "storage_key": "models/adult-content-demo-checkpoint-v1.0.0.safetensors",
            "epoch": 10,
            "avg_reward": 0.75,
            "is_active": True,
            "model_type": "adult_content_classifier",
        }

        checkpoint_result = await client.create_checkpoint(**checkpoint_data)

        if checkpoint_result.get("success"):
            checkpoint = checkpoint_result["data"]
            print(f"✅ Created checkpoint: {checkpoint['version']}")
            print(f"   ID: {checkpoint['id']}")
            print(f"   Storage Key: {checkpoint['storage_key']}")
            print(f"   Average Reward: {checkpoint['avg_reward']}")
            print(f"   Active: {checkpoint['is_active']}")
        else:
            print(f"❌ Failed to create checkpoint: {checkpoint_result.get('error')}")

        # Get comprehensive statistics
        print("\n📊 6. Getting training statistics...")

        stats = await manager.get_training_statistics()

        print("📈 Training Statistics:")
        print(f"  Responses: {stats['responses']['total']}")
        print(f"  Rewards: {stats['rewards']['total']}")
        print(f"  Average Score: {stats['rewards']['avg_score']:.3f}")
        print(f"  Checkpoints: {stats['checkpoints']['total']}")
        print(f"  Training Status: {stats['training_readiness']['status']}")

        if stats["training_readiness"]["recommendations"]:
            print(f"  Recommendations:")
            for rec in stats["training_readiness"]["recommendations"]:
                print(f"    - {rec}")

        # Demonstrate different checkpoint operations
        print("\n🔄 7. Demonstrating checkpoint operations...")

        # List all checkpoints
        checkpoints_result = await client.get_checkpoints()

        if checkpoints_result.get("success"):
            checkpoints = checkpoints_result["data"]
            print(f"📋 Found {len(checkpoints)} checkpoints:")

            for checkpoint in checkpoints:
                status = "🟢 Active" if checkpoint.get("is_active") else "⚪ Inactive"
                print(f"  • {checkpoint['version']} - {status}")
                print(
                    f"    Epoch: {checkpoint.get('epoch', 0)}, Reward: {checkpoint.get('avg_reward', 0):.3f}"
                )

        # Get active checkpoint
        active_result = await client.get_active_checkpoint()

        if active_result.get("success"):
            active_checkpoint = active_result["data"]
            print(f"\n🟢 Active Checkpoint: {active_checkpoint['version']}")
        else:
            print(f"\n❌ No active checkpoint found")

        print("\n🎉 Adult Content RFT Integration Workflow Completed Successfully!")
        print("\n💡 Next Steps:")
        print("  1. Set up actual Supabase credentials")
        print("  2. Deploy edge functions using deploy-edge-functions.sh")
        print("  3. Run database migration: 20240904000001_rft_integration_setup.sql")
        print("  4. Configure MCP server with Supabase settings for adult content")
        print("  5. Start adult content scraping and training!")
        print(
            "  6. Ensure compliance with adult content regulations and age verification"
        )

    except Exception as e:
        logger.error(f"RFT workflow demonstration failed: {e}")
        print(f"\n❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("  • Check Supabase URL and API key")
        print("  • Ensure edge functions are deployed")
        print("  • Verify database tables are created")
        print("  • Check network connectivity")


async def test_individual_components():
    """Test individual RFT components"""

    print("\n🧪 Testing Individual RFT Components")
    print("=" * 40)

    supabase_config = {
        "url": "https://xewniavplpocctogfgnc.supabase.co",
        "anon_key": "your-anon-key-here",  # Replace with actual key
    }

    client = RFTSupabaseClient(supabase_config["url"], supabase_config["anon_key"])

    # Test response creation
    print("\n📝 Testing response creation...")
    response_result = await client.create_response(
        user_id="test-user",
        prompt="Describe this fashion image",
        response_text="This image shows a model wearing a stylish dress...",
        model_id="test-model",
        metadata={"test": True},
    )
    print(
        f"Response creation: {'✅ Success' if response_result.get('success') else '❌ Failed'}"
    )

    # Test reward creation
    if response_result.get("success"):
        response_id = response_result["data"]["id"]
        print(f"\n🎯 Testing reward creation...")

        reward_result = await client.create_reward(
            response_id, 0.8, "Good quality response"
        )
        print(
            f"Reward creation: {'✅ Success' if reward_result.get('success') else '❌ Failed'}"
        )

    # Test checkpoint creation
    print(f"\n💾 Testing checkpoint creation...")
    checkpoint_result = await client.create_checkpoint(
        version="test-v1.0.0",
        storage_key="test/checkpoint.safetensors",
        epoch=5,
        avg_reward=0.6,
        is_active=False,
    )
    print(
        f"Checkpoint creation: {'✅ Success' if checkpoint_result.get('success') else '❌ Failed'}"
    )

    print("\n✅ Component testing completed!")


if __name__ == "__main__":
    print("🤖 RFT Integration Demo")
    print("Choose an option:")
    print("1. Full workflow demonstration")
    print("2. Test individual components")
    print("3. Both")

    choice = input("\nEnter choice (1-3): ").strip()

    if choice == "1":
        asyncio.run(demonstrate_rft_workflow())
    elif choice == "2":
        asyncio.run(test_individual_components())
    elif choice == "3":
        asyncio.run(demonstrate_rft_workflow())
        asyncio.run(test_individual_components())
    else:
        print("Invalid choice. Running full demonstration...")
        asyncio.run(demonstrate_rft_workflow())
