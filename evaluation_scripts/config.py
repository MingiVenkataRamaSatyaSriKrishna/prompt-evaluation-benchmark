"""
Configuration module for LLM Evaluation Framework

Manages paths, API keys, metrics definitions, and settings.
"""

import os
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class MetricConfig:
    """Configuration for evaluation metrics"""
    name: str
    weight: float
    description: str
    enabled: bool = True


class Config:
    """
    Central configuration for the evaluation framework.
    
    Manages:
    - Directory paths
    - API credentials
    - Metric definitions
    - Model configurations
    """
    
    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    PROMPTS_DIR = BASE_DIR / "prompts"
    DATASETS_DIR = BASE_DIR / "datasets"
    RESULTS_DIR = BASE_DIR / "results"
    SCREENSHOTS_DIR = BASE_DIR / "screenshots"
    
    # Create directories if they don't exist
    @staticmethod
    def ensure_directories():
        """Create necessary directories if they don't exist"""
        for directory in [Config.PROMPTS_DIR, Config.DATASETS_DIR, 
                         Config.RESULTS_DIR, Config.SCREENSHOTS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
    
    # API Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
    HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "meta-llama/Llama-2-7b-hf")
    
    # Evaluation Configuration
    DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "60"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
    
    # Results Configuration
    SAVE_RESULTS = os.getenv("SAVE_RESULTS", "true").lower() == "true"
    RESULTS_FORMAT = os.getenv("RESULTS_FORMAT", "json")  # json, csv, html
    GENERATE_VISUALIZATIONS = os.getenv("GENERATE_VISUALIZATIONS", "true").lower() == "true"
    
    # Evaluation Metrics (with weights)
    METRICS = {
        "accuracy": MetricConfig(
            name="accuracy",
            weight=0.25,
            description="Factual correctness of the response"
        ),
        "relevance": MetricConfig(
            name="relevance",
            weight=0.20,
            description="How well the response addresses the prompt"
        ),
        "coherence": MetricConfig(
            name="coherence",
            weight=0.15,
            description="Logical flow and consistency of the response"
        ),
        "completeness": MetricConfig(
            name="completeness",
            weight=0.15,
            description="Coverage of all prompt requirements"
        ),
        "efficiency": MetricConfig(
            name="efficiency",
            weight=0.10,
            description="Response clarity and appropriate length"
        ),
        "creativity": MetricConfig(
            name="creativity",
            weight=0.10,
            description="Novel or insightful aspects of the response"
        ),
        "safety": MetricConfig(
            name="safety",
            weight=0.05,
            description="Adherence to safety guidelines"
        ),
    }
    
    # Supported Models
    SUPPORTED_MODELS = {
        "openai": {
            "gpt-4": "gpt-4",
            "gpt-3.5-turbo": "gpt-3.5-turbo",
            "gpt-4-turbo": "gpt-4-turbo-preview",
        },
        "huggingface": {
            "llama-2": "meta-llama/Llama-2-7b-hf",
            "mistral": "mistralai/Mistral-7B-v0.1",
            "falcon": "tiiuae/falcon-7b",
        },
        "mock": {
            "test": "mock-test",
            "demo": "mock-demo",
        }
    }
    
    @classmethod
    def get_metric(cls, metric_name: str) -> MetricConfig:
        """Get metric configuration by name"""
        return cls.METRICS.get(metric_name)
    
    @classmethod
    def get_all_metrics(cls) -> Dict[str, MetricConfig]:
        """Get all enabled metrics"""
        return {k: v for k, v in cls.METRICS.items() if v.enabled}
    
    @classmethod
    def get_model_path(cls, provider: str, model: str) -> str:
        """Get full model path from provider and model name"""
        if provider in cls.SUPPORTED_MODELS:
            if model in cls.SUPPORTED_MODELS[provider]:
                return cls.SUPPORTED_MODELS[provider][model]
        raise ValueError(f"Unsupported model: {provider}:{model}")


# Initialize directories on import
Config.ensure_directories()
