import os
import sys
import yaml
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from src.exceptions import ExceptionError
from src.loggers import logging


def get_api_key(api_key_name):
    return os.environ[api_key_name]


def load_llm_config(provider_name: str, config_path=".\src\config\llm_configs.yml"):
    """
    Load configuration for a specific LLM provider.

    Args:
        provider_name (str): e.g., "gemini", "groq", "openai".
        config_path (str): Path to YAML config file.

    Returns:
        dict: Configuration dictionary for the provider, or None if an error occurs.
    """
    try:
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r") as f:
            configs = yaml.safe_load(f)
            logging.info("Read the llm releted config file")

        if not isinstance(configs, dict):
            raise ValueError(f"Invalid YAML structure in {config_path}. Expected a dictionary at root level.")

        if provider_name not in configs:
            raise ValueError(f"Provider '{provider_name}' not found in config file.")

        return configs[provider_name]
    except Exception as e:
        raise ExceptionError(e, sys)
