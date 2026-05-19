"""
LLM Evaluation Framework - Package initialization

Exports main classes and utilities for the evaluation system.
"""

from .config import Config
from .models import ModelFactory, LLMModel
from .evaluator import Evaluator, EvaluationMetrics
from .dataset_loader import DatasetLoader

__version__ = "1.0.0"
__author__ = "Prompt Evaluation Team"

__all__ = [
    "Config",
    "ModelFactory",
    "LLMModel",
    "Evaluator",
    "EvaluationMetrics",
    "DatasetLoader",
]
