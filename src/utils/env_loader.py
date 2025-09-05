#!/usr/bin/env python3
"""
Environment variable loading utilities
Provides secure environment variable loading with validation
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class EnvironmentError(Exception):
    """Custom exception for environment variable issues"""

    pass


def load_env_file(env_path: Optional[str] = None) -> None:
    """
    Load environment variables from .env file

    Args:
        env_path: Path to .env file. If None, looks for .env in project root
    """
    if env_path is None:
        # Look for .env in project root
        project_root = Path(__file__).parent.parent.parent
        env_path = project_root / ".env"

    env_path = Path(env_path)

    if not env_path.exists():
        logger.warning(f"Environment file not found: {env_path}")
        return

    try:
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")

                    # Only set if not already in environment
                    if key not in os.environ:
                        os.environ[key] = value

        logger.info(f"Loaded environment variables from: {env_path}")
    except Exception as e:
        logger.error(f"Failed to load environment file {env_path}: {e}")


def get_required_env(key: str) -> str:
    """
    Get required environment variable, raise error if missing

    Args:
        key: Environment variable name

    Returns:
        Environment variable value

    Raises:
        EnvironmentError: If variable is missing or empty
    """
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{key}' is missing or empty"
        )
    return value


def get_optional_env(key: str, default: str = "") -> str:
    """
    Get optional environment variable with default

    Args:
        key: Environment variable name
        default: Default value if not found

    Returns:
        Environment variable value or default
    """
    return os.getenv(key, default)


def validate_api_key(key: str, service_name: str) -> str:
    """
    Validate API key format and return it

    Args:
        key: API key to validate
        service_name: Name of service for error messages

    Returns:
        Validated API key

    Raises:
        EnvironmentError: If key format is invalid
    """
    if not key:
        raise EnvironmentError(f"{service_name} API key is empty")

    if len(key) < 10:
        raise EnvironmentError(f"{service_name} API key appears to be too short")

    # Basic format validation
    if service_name.lower() == "jina" and not key.startswith(("jina_", "sk-")):
        logger.warning(f"Jina API key may have unexpected format: {key[:10]}...")

    if service_name.lower() == "supabase" and not key.startswith("eyJ"):
        logger.warning(f"Supabase key may have unexpected format: {key[:10]}...")

    return key


def get_secure_config() -> Dict[str, Any]:
    """
    Get secure configuration from environment variables

    Returns:
        Dictionary with validated configuration

    Raises:
        EnvironmentError: If required variables are missing
    """
    # Load .env file if it exists
    load_env_file()

    config = {}

    # Jina AI configuration (optional)
    jina_key = get_optional_env("JINA_API_KEY")
    if jina_key:
        config["jina"] = {
            "api_key": validate_api_key(jina_key, "Jina"),
            "base_url": get_optional_env("JINA_BASE_URL", "https://eu-s-beta.jina.ai"),
        }

    # Supabase configuration (required for RFT)
    supabase_anon_key = get_optional_env("SUPABASE_ANON_KEY")
    supabase_service_key = get_optional_env("SUPABASE_SERVICE_ROLE_KEY")

    if supabase_anon_key or supabase_service_key:
        config["supabase"] = {}

        if supabase_anon_key:
            config["supabase"]["anon_key"] = validate_api_key(
                supabase_anon_key, "Supabase"
            )

        if supabase_service_key:
            config["supabase"]["service_role_key"] = validate_api_key(
                supabase_service_key, "Supabase"
            )

    # Other optional configurations
    config["server"] = {
        "host": get_optional_env("MCP_SERVER_HOST", "localhost"),
        "port": int(get_optional_env("MCP_SERVER_PORT", "8000")),
        "debug": get_optional_env("MCP_SERVER_DEBUG", "false").lower() == "true",
    }

    return config


def check_environment_health() -> Dict[str, Any]:
    """
    Check the health of environment configuration

    Returns:
        Dictionary with health status
    """
    health = {
        "status": "healthy",
        "issues": [],
        "warnings": [],
        "available_services": [],
    }

    try:
        # Check Jina API
        jina_key = get_optional_env("JINA_API_KEY")
        if jina_key:
            try:
                validate_api_key(jina_key, "Jina")
                health["available_services"].append("jina_ai")
            except EnvironmentError as e:
                health["issues"].append(f"Jina AI: {e}")
                health["status"] = "degraded"
        else:
            health["warnings"].append(
                "Jina AI key not configured - intelligent research unavailable"
            )

        # Check Supabase
        supabase_anon = get_optional_env("SUPABASE_ANON_KEY")
        supabase_service = get_optional_env("SUPABASE_SERVICE_ROLE_KEY")

        if supabase_anon or supabase_service:
            try:
                if supabase_anon:
                    validate_api_key(supabase_anon, "Supabase")
                if supabase_service:
                    validate_api_key(supabase_service, "Supabase")
                health["available_services"].append("supabase")
            except EnvironmentError as e:
                health["issues"].append(f"Supabase: {e}")
                health["status"] = "degraded"
        else:
            health["warnings"].append(
                "Supabase keys not configured - RFT integration unavailable"
            )

        # Determine overall status
        if health["issues"]:
            health["status"] = "unhealthy" if len(health["issues"]) > 2 else "degraded"

    except Exception as e:
        health["status"] = "error"
        health["issues"].append(f"Environment check failed: {e}")

    return health


if __name__ == "__main__":
    # Test environment configuration
    try:
        config = get_secure_config()
        health = check_environment_health()

        print("🔧 Environment Configuration Test")
        print("=" * 40)
        print(f"Status: {health['status']}")
        print(f"Available Services: {', '.join(health['available_services'])}")

        if health["warnings"]:
            print("\n⚠️ Warnings:")
            for warning in health["warnings"]:
                print(f"  • {warning}")

        if health["issues"]:
            print("\n❌ Issues:")
            for issue in health["issues"]:
                print(f"  • {issue}")

        print("\n✅ Environment check completed")

    except Exception as e:
        print(f"❌ Environment check failed: {e}")
