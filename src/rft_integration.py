#!/usr/bin/env python3
"""
RFT (Reinforcement Fine-tuning) Integration for MCP Web Scraper
Connects the web scraping pipeline with the RFT training system
"""

import asyncio
import aiohttp
import json
import logging
import os
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import uuid
from datetime import datetime

# Import environment utilities if available
try:
    from utils.env_loader import get_optional_env

    ENV_UTILS_AVAILABLE = True
except ImportError:
    ENV_UTILS_AVAILABLE = False

    def get_optional_env(key: str, default: str = "") -> str:
        return os.getenv(key, default)


logger = logging.getLogger("rft-integration")


class RFTSupabaseClient:
    """Client for interacting with RFT Supabase edge functions"""

    def __init__(self, supabase_url: str, anon_key: str = None):
        self.base_url = f"{supabase_url}/functions/v1"
        self.headers = {
            "Content-Type": "application/json",
            "apikey": anon_key or "",
        }
        if anon_key:
            self.headers["Authorization"] = f"Bearer {anon_key}"

    async def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request to Supabase edge function"""
        url = f"{self.base_url}/{endpoint}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(
                    method, url, headers=self.headers, **kwargs
                ) as response:
                    if response.content_type == "application/json":
                        data = await response.json()
                    else:
                        text = await response.text()
                        data = {"raw_response": text}

                    if response.status >= 400:
                        logger.error(
                            f"HTTP {response.status} for {method} {endpoint}: {data}"
                        )
                        return {
                            "success": False,
                            "error": data.get("error", f"HTTP {response.status}"),
                            "status": response.status,
                        }

                    return data
            except Exception as e:
                logger.error(f"Request failed for {method} {endpoint}: {e}")
                return {"success": False, "error": str(e)}

    # Upload Functions
    async def upload_image(
        self,
        file_path: str,
        user_id: str = "anonymous",
        category: str = "scraped",
        metadata: Dict = None,
    ) -> Dict[str, Any]:
        """Upload image to Supabase storage with metadata"""
        if not Path(file_path).exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        data = aiohttp.FormData()
        data.add_field("file", open(file_path, "rb"), filename=Path(file_path).name)
        data.add_field("user_id", user_id)
        data.add_field("category", category)

        if metadata:
            data.add_field("metadata", json.dumps(metadata))

        # Override headers for multipart
        headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_url}/upload", data=data, headers=headers
                ) as response:
                    result = await response.json()
                    if response.status >= 400:
                        logger.error(f"Upload failed: {result}")
                    return result
            except Exception as e:
                logger.error(f"Upload request failed: {e}")
                return {"success": False, "error": str(e)}

    # RFT Response Functions
    async def create_response(
        self,
        user_id: str,
        prompt: str,
        response_text: str,
        model_id: str = "default",
        metadata: Dict = None,
    ) -> Dict[str, Any]:
        """Create a new RFT response record"""
        payload = {
            "user_id": user_id,
            "prompt": prompt,
            "response_text": response_text,
            "model_id": model_id,
            "metadata": metadata or {},
        }
        return await self._make_request("POST", "rft-responses", json=payload)

    async def get_responses(
        self,
        user_id: str = None,
        model_id: str = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get RFT responses with optional filtering"""
        params = {"limit": limit, "offset": offset}
        if user_id:
            params["user_id"] = user_id
        if model_id:
            params["model_id"] = model_id

        return await self._make_request("GET", "rft-responses", params=params)

    async def update_response(self, response_id: str, updates: Dict) -> Dict[str, Any]:
        """Update an RFT response"""
        return await self._make_request(
            "PUT", f"rft-responses?id={response_id}", json=updates
        )

    # RFT Reward Functions
    async def create_reward(
        self, response_id: str, score: float, detail: str = None
    ) -> Dict[str, Any]:
        """Create a reward for a response"""
        if not -1 <= score <= 1:
            return {"success": False, "error": "Score must be between -1 and 1"}

        payload = {"response_id": response_id, "score": score, "detail": detail}
        return await self._make_request("POST", "rft-rewards", json=payload)

    async def get_rewards(
        self,
        response_id: str = None,
        min_score: float = None,
        max_score: float = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get rewards with optional filtering"""
        params = {"limit": limit, "offset": offset}
        if response_id:
            params["response_id"] = response_id
        if min_score is not None:
            params["min_score"] = min_score
        if max_score is not None:
            params["max_score"] = max_score

        return await self._make_request("GET", "rft-rewards", params=params)

    async def update_reward(
        self, reward_id: str, score: float = None, detail: str = None
    ) -> Dict[str, Any]:
        """Update a reward score"""
        updates = {}
        if score is not None:
            if not -1 <= score <= 1:
                return {"success": False, "error": "Score must be between -1 and 1"}
            updates["score"] = score
        if detail is not None:
            updates["detail"] = detail

        return await self._make_request(
            "PUT", f"rft-rewards?id={reward_id}", json=updates
        )

    # RFT Checkpoint Functions
    async def create_checkpoint(
        self,
        version: str,
        storage_key: str,
        url: str = None,
        epoch: int = 0,
        avg_reward: float = 0,
        is_active: bool = False,
    ) -> Dict[str, Any]:
        """Create a new model checkpoint"""
        payload = {
            "version": version,
            "storage_key": storage_key,
            "url": url,
            "epoch": epoch,
            "avg_reward": avg_reward,
            "is_active": is_active,
        }
        return await self._make_request("POST", "rft-checkpoints", json=payload)

    async def get_checkpoints(
        self,
        version: str = None,
        active_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get model checkpoints"""
        params = {"limit": limit, "offset": offset}
        if version:
            params["version"] = version
        if active_only:
            params["active_only"] = "true"

        return await self._make_request("GET", "rft-checkpoints", params=params)

    async def activate_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """Activate a specific checkpoint (deactivates others)"""
        return await self._make_request(
            "PUT", f"rft-checkpoints?id={checkpoint_id}", json={"is_active": True}
        )

    async def get_active_checkpoint(self) -> Dict[str, Any]:
        """Get the currently active checkpoint"""
        result = await self.get_checkpoints(active_only=True, limit=1)
        if result.get("success") and result.get("data"):
            return {"success": True, "data": result["data"][0]}
        return {"success": False, "error": "No active checkpoint found"}


class RFTImageProcessor:
    """Processes scraped images for RFT training pipeline"""

    def __init__(self, supabase_client: RFTSupabaseClient, config: Dict):
        self.client = supabase_client
        self.config = config
        self.session_id = str(uuid.uuid4())

    async def process_scraped_images(
        self, image_paths: List[str], scraping_context: Dict
    ) -> Dict[str, Any]:
        """Process a batch of scraped images for RFT training"""
        results = {
            "session_id": self.session_id,
            "processed": [],
            "failed": [],
            "total_images": len(image_paths),
            "scraping_context": scraping_context,
            "timestamp": datetime.now().isoformat(),
        }

        for image_path in image_paths:
            try:
                # Upload image with RFT metadata
                metadata = {
                    "session_id": self.session_id,
                    "source_url": scraping_context.get("url"),
                    "scraping_timestamp": scraping_context.get("timestamp"),
                    "category": scraping_context.get("category", "general"),
                    "quality_score": scraping_context.get("quality_score"),
                    "rft_stage": "data_collection",
                }

                upload_result = await self.client.upload_image(
                    image_path,
                    user_id=scraping_context.get("user_id", "scraper"),
                    category="rft-training-data",
                    metadata=metadata,
                )

                if upload_result.get("success"):
                    results["processed"].append(
                        {
                            "image_path": image_path,
                            "image_id": upload_result.get("imageId"),
                            "url": upload_result.get("url"),
                            "metadata": metadata,
                        }
                    )
                else:
                    results["failed"].append(
                        {"image_path": image_path, "error": upload_result.get("error")}
                    )

            except Exception as e:
                logger.error(f"Error processing image {image_path}: {e}")
                results["failed"].append({"image_path": image_path, "error": str(e)})

        return results

    async def create_training_prompt(self, image_url: str, context: Dict) -> str:
        """Generate training prompt for image"""
        # This would typically use the context to create appropriate prompts
        category = context.get("category", "general")
        quality = context.get("quality_score", "medium")

        prompt_templates = {
            "fashion": f"Generate a detailed description of this {quality} quality fashion image",
            "portrait": f"Describe the person and styling in this {quality} quality portrait",
            "general": f"Provide a comprehensive description of this {quality} quality image",
        }

        return prompt_templates.get(category, prompt_templates["general"])

    async def simulate_model_response(self, prompt: str, image_url: str) -> str:
        """Simulate model response (placeholder for actual model inference)"""
        # This is a placeholder - in real implementation, this would call your model
        return f"This image shows [SIMULATED RESPONSE FOR: {prompt}]"

    async def create_rft_training_data(
        self, processed_images: List[Dict]
    ) -> Dict[str, Any]:
        """Create RFT training data from processed images"""
        training_data = {
            "responses_created": [],
            "failed": [],
            "timestamp": datetime.now().isoformat(),
        }

        for image_data in processed_images:
            try:
                # Create prompt
                prompt = await self.create_training_prompt(
                    image_data["url"], image_data["metadata"]
                )

                # Simulate model response (replace with actual model inference)
                response_text = await self.simulate_model_response(
                    prompt, image_data["url"]
                )

                # Create response record
                response_result = await self.client.create_response(
                    user_id=image_data["metadata"].get("session_id", "unknown"),
                    prompt=prompt,
                    response_text=response_text,
                    model_id="scraper-base-model",
                    metadata={
                        "image_id": image_data["image_id"],
                        "image_url": image_data["url"],
                        "source_context": image_data["metadata"],
                    },
                )

                if response_result.get("success"):
                    training_data["responses_created"].append(
                        {
                            "response_id": response_result["data"]["id"],
                            "image_id": image_data["image_id"],
                            "prompt": prompt,
                            "response": response_text,
                        }
                    )
                else:
                    training_data["failed"].append(
                        {
                            "image_id": image_data["image_id"],
                            "error": response_result.get("error"),
                        }
                    )

            except Exception as e:
                logger.error(
                    f"Error creating training data for image {image_data.get('image_id')}: {e}"
                )
                training_data["failed"].append(
                    {"image_id": image_data.get("image_id"), "error": str(e)}
                )

        return training_data


class RFTTrainingManager:
    """Manages the RFT training pipeline integration"""

    def __init__(self, supabase_client: RFTSupabaseClient, config: Dict):
        self.client = supabase_client
        self.config = config
        self.processor = RFTImageProcessor(supabase_client, config)

    async def integrate_scraping_session(self, scraping_result: Dict) -> Dict[str, Any]:
        """Integrate a complete scraping session into RFT pipeline"""
        logger.info(f"Integrating scraping session into RFT pipeline")

        # Extract image paths from scraping result
        images = scraping_result.get("images", [])
        image_paths = [img.get("local_path") for img in images if img.get("local_path")]

        if not image_paths:
            return {
                "success": False,
                "error": "No valid image paths found in scraping result",
            }

        # Process images for RFT
        processing_result = await self.processor.process_scraped_images(
            image_paths,
            {
                "url": scraping_result.get("url"),
                "timestamp": scraping_result.get("timestamp"),
                "category": scraping_result.get("category"),
                "user_id": "mcp-scraper",
                "quality_score": scraping_result.get("avg_quality_score"),
            },
        )

        # Create training data
        if processing_result["processed"]:
            training_result = await self.processor.create_rft_training_data(
                processing_result["processed"]
            )
            processing_result["training_data"] = training_result

        return {
            "success": True,
            "session_id": self.processor.session_id,
            "processing_result": processing_result,
            "summary": {
                "total_images": len(image_paths),
                "processed_images": len(processing_result["processed"]),
                "failed_images": len(processing_result["failed"]),
                "responses_created": len(
                    processing_result.get("training_data", {}).get(
                        "responses_created", []
                    )
                ),
                "ready_for_training": len(processing_result["processed"]) > 0,
            },
        }

    async def create_reward_feedback(
        self, response_id: str, human_feedback: Dict
    ) -> Dict[str, Any]:
        """Create reward based on human feedback"""
        # Convert human feedback to reward score
        feedback_type = human_feedback.get("type")  # "like", "dislike", "neutral"
        quality_rating = human_feedback.get("quality", 0)  # 1-5 scale

        # Convert to -1 to 1 scale
        if feedback_type == "like":
            base_score = 0.5
        elif feedback_type == "dislike":
            base_score = -0.5
        else:
            base_score = 0

        # Adjust based on quality rating
        quality_adjustment = (quality_rating - 3) * 0.2  # -0.4 to 0.4
        final_score = max(-1, min(1, base_score + quality_adjustment))

        detail = json.dumps(
            {
                "feedback_type": feedback_type,
                "quality_rating": quality_rating,
                "comments": human_feedback.get("comments"),
                "timestamp": datetime.now().isoformat(),
            }
        )

        return await self.client.create_reward(response_id, final_score, detail)

    async def get_training_statistics(self) -> Dict[str, Any]:
        """Get comprehensive training statistics"""
        # Get responses
        responses_result = await self.client.get_responses(limit=1000)

        # Get rewards
        rewards_result = await self.client.get_rewards(limit=1000)

        # Get checkpoints
        checkpoints_result = await self.client.get_checkpoints(limit=100)

        stats = {
            "responses": {"total": 0, "by_model": {}, "recent_24h": 0},
            "rewards": {
                "total": 0,
                "avg_score": 0,
                "distribution": {"positive": 0, "negative": 0, "neutral": 0},
            },
            "checkpoints": {"total": 0, "active": None, "best_performance": 0},
            "training_readiness": {"status": "unknown", "recommendations": []},
        }

        # Process responses
        if responses_result.get("success"):
            responses = responses_result.get("data", [])
            stats["responses"]["total"] = len(responses)

            # Count by model
            for response in responses:
                model_id = response.get("model_id", "unknown")
                stats["responses"]["by_model"][model_id] = (
                    stats["responses"]["by_model"].get(model_id, 0) + 1
                )

        # Process rewards
        if rewards_result.get("success"):
            rewards_data = rewards_result.get("stats", {})
            stats["rewards"] = {**stats["rewards"], **rewards_data}

        # Process checkpoints
        if checkpoints_result.get("success"):
            checkpoints_data = checkpoints_result.get("stats", {})
            stats["checkpoints"] = {**stats["checkpoints"], **checkpoints_data}

        # Determine training readiness
        total_responses = stats["responses"]["total"]
        total_rewards = stats["rewards"]["total"]

        if total_responses > 100 and total_rewards > 50:
            stats["training_readiness"]["status"] = "ready"
        elif total_responses > 50:
            stats["training_readiness"]["status"] = "partial"
            stats["training_readiness"]["recommendations"].append(
                "Need more reward feedback"
            )
        else:
            stats["training_readiness"]["status"] = "insufficient_data"
            stats["training_readiness"]["recommendations"].append(
                "Need more training responses"
            )

        return stats


# Integration with MCP Server
async def integrate_with_mcp_scraper(
    scraper_result: Dict, supabase_config: Dict
) -> Dict[str, Any]:
    """Main integration function for MCP scraper"""
    try:
        # Initialize RFT client
        client = RFTSupabaseClient(
            supabase_config["url"], supabase_config.get("anon_key")
        )

        # Initialize training manager
        manager = RFTTrainingManager(client, supabase_config)

        # Integrate scraping result
        integration_result = await manager.integrate_scraping_session(scraper_result)

        logger.info(f"RFT integration completed: {integration_result.get('summary')}")
        return integration_result

    except Exception as e:
        logger.error(f"RFT integration failed: {e}")
        return {"success": False, "error": str(e)}


# Example usage
async def example_rft_workflow():
    """Example of complete RFT workflow"""
    # Configuration
    supabase_config = {
        "url": "https://xewniavplpocctogfgnc.supabase.co",
        "anon_key": "your-anon-key-here",
    }

    # Initialize client
    client = RFTSupabaseClient(supabase_config["url"], supabase_config["anon_key"])

    # Simulate scraping result
    scraper_result = {
        "url": "https://example.com",
        "images": [
            {"local_path": "/path/to/image1.jpg"},
            {"local_path": "/path/to/image2.jpg"},
        ],
        "category": "fashion",
        "timestamp": datetime.now().isoformat(),
    }

    # Integrate with RFT
    result = await integrate_with_mcp_scraper(scraper_result, supabase_config)
    print(f"Integration result: {result}")

    # Get training statistics
    manager = RFTTrainingManager(client, supabase_config)
    stats = await manager.get_training_statistics()
    print(f"Training statistics: {stats}")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_rft_workflow())
