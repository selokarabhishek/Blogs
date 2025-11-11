"""
Utility functions for the Government Scheme Discovery AI
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file

    Args:
        config_path: Path to config file. Defaults to config/config.yaml

    Returns:
        Dictionary containing configuration
    """
    if config_path is None:
        config_path = PROJECT_ROOT / "config" / "config.yaml"

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    return config


def get_env_variable(var_name: str, default: Any = None) -> Any:
    """
    Get environment variable with optional default

    Args:
        var_name: Name of environment variable
        default: Default value if variable not found

    Returns:
        Environment variable value or default
    """
    return os.getenv(var_name, default)


def setup_logging(log_file: str = None):
    """
    Setup logging configuration

    Args:
        log_file: Path to log file. Defaults to logs/app.log
    """
    if log_file is None:
        log_file = PROJECT_ROOT / "logs" / "app.log"

    # Create logs directory if it doesn't exist
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure logger
    logger.add(
        log_file,
        rotation="10 MB",
        retention="30 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    )


def format_currency(amount: float) -> str:
    """
    Format amount in Indian currency format

    Args:
        amount: Amount to format

    Returns:
        Formatted currency string
    """
    if amount >= 10000000:  # 1 crore
        return f"₹{amount/10000000:.2f}Cr"
    elif amount >= 100000:  # 1 lakh
        return f"₹{amount/100000:.2f}L"
    elif amount >= 1000:  # 1 thousand
        return f"₹{amount/1000:.2f}K"
    else:
        return f"₹{amount:.2f}"


def validate_user_profile(profile: Dict[str, Any]) -> bool:
    """
    Validate user profile data

    Args:
        profile: User profile dictionary

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["age", "gender", "category", "annual_income", "state", "occupation"]

    for field in required_fields:
        if field not in profile or profile[field] is None:
            logger.error(f"Missing required field: {field}")
            return False

    # Validate age
    if not (0 <= profile["age"] <= 120):
        logger.error(f"Invalid age: {profile['age']}")
        return False

    # Validate income
    if profile["annual_income"] < 0:
        logger.error(f"Invalid income: {profile['annual_income']}")
        return False

    return True
