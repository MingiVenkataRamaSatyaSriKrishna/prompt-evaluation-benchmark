"""
LLM Model interfaces and implementations

Provides abstract base class and concrete implementations for various LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import json
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LLMModel(ABC):
    """
    Abstract base class for LLM models.
    
    All specific model implementations should inherit from this class.
    """
    
    def __init__(self, model_name: str, temperature: float = 0.7, max_tokens: int = 2048):
        """Initialize the LLM model
        
        Args:
            model_name: Name of the model
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in response
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.request_count = 0
        self.total_latency = 0.0
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response for a given prompt
        
        Args:
            prompt: Input prompt text
            **kwargs: Additional model-specific parameters
            
        Returns:
            Generated response text
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get model usage statistics"""
        avg_latency = (self.total_latency / self.request_count) if self.request_count > 0 else 0
        return {
            "model": self.model_name,
            "requests": self.request_count,
            "avg_latency": avg_latency,
            "total_latency": self.total_latency,
        }


class OpenAIModel(LLMModel):
    """
    OpenAI GPT model implementation.
    
    Requires OPENAI_API_KEY environment variable to be set.
    """
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", **kwargs):
        """Initialize OpenAI model
        
        Args:
            model_name: OpenAI model ID (gpt-4, gpt-3.5-turbo, etc.)
            **kwargs: Additional parameters for LLMModel
        """
        super().__init__(model_name, **kwargs)
        try:
            import openai
            self.client = openai.OpenAI()
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using OpenAI API"""
        try:
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            latency = time.time() - start_time
            self.request_count += 1
            self.total_latency += latency
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise


class HuggingFaceModel(LLMModel):
    """
    HuggingFace model implementation.
    
    Requires HUGGINGFACE_API_KEY environment variable to be set.
    """
    
    def __init__(self, model_name: str = "meta-llama/Llama-2-7b-hf", **kwargs):
        """Initialize HuggingFace model
        
        Args:
            model_name: HuggingFace model ID
            **kwargs: Additional parameters for LLMModel
        """
        super().__init__(model_name, **kwargs)
        try:
            from huggingface_hub import InferenceClient
            import os
            api_key = os.getenv("HUGGINGFACE_API_KEY")
            if not api_key:
                raise ValueError("HUGGINGFACE_API_KEY not set")
            self.client = InferenceClient(api_key=api_key)
        except ImportError:
            raise ImportError("huggingface_hub package required. Install with: pip install huggingface-hub")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using HuggingFace API"""
        try:
            start_time = time.time()
            
            response = self.client.text_generation(
                prompt,
                model=self.model_name,
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            
            latency = time.time() - start_time
            self.request_count += 1
            self.total_latency += latency
            
            return response
            
        except Exception as e:
            logger.error(f"HuggingFace API error: {str(e)}")
            raise


class MockModel(LLMModel):
    """
    Mock model for testing and demonstrations.
    
    Returns deterministic responses without API calls.
    """
    
    def __init__(self, model_name: str = "mock-test", **kwargs):
        """Initialize mock model
        
        Args:
            model_name: Mock model identifier
            **kwargs: Additional parameters for LLMModel
        """
        super().__init__(model_name, **kwargs)
        self.responses = {
            "what is ai": "Artificial Intelligence (AI) refers to computer systems designed to perform tasks that typically require human intelligence. These include learning from experience, pattern recognition, language understanding, and decision-making. AI powers applications like chatbots, recommendation systems, and autonomous vehicles.",
            "explain machine learning": "Machine Learning is a subset of AI where systems learn from data without being explicitly programmed. It uses algorithms to identify patterns and improve performance through experience. Common types include supervised learning, unsupervised learning, and reinforcement learning.",
            "default": "This is a mock response from the test model. In production, this would be replaced with actual API calls to a real language model."
        }
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate a mock response"""
        start_time = time.time()
        time.sleep(0.1)  # Simulate latency
        
        prompt_lower = prompt.lower()
        response = self.responses.get(prompt_lower, self.responses["default"])
        
        latency = time.time() - start_time
        self.request_count += 1
        self.total_latency += latency
        
        return response


class ModelFactory:
    """
    Factory for creating LLM model instances.
    
    Provides a simple interface to instantiate different model types.
    """
    
    _models = {
        "openai": OpenAIModel,
        "huggingface": HuggingFaceModel,
        "mock": MockModel,
    }
    
    @classmethod
    def create(cls, provider: str, model_name: str, **kwargs) -> LLMModel:
        """Create a model instance
        
        Args:
            provider: Model provider (openai, huggingface, mock)
            model_name: Specific model name
            **kwargs: Additional arguments for the model
            
        Returns:
            LLMModel instance
            
        Raises:
            ValueError: If provider is not supported
        """
        if provider not in cls._models:
            raise ValueError(f"Unknown provider: {provider}. Supported: {list(cls._models.keys())}")
        
        model_class = cls._models[provider]
        return model_class(model_name, **kwargs)
    
    @classmethod
    def register_model(cls, provider: str, model_class: type):
        """Register a custom model provider
        
        Args:
            provider: Provider name
            model_class: Model class inheriting from LLMModel
        """
        if not issubclass(model_class, LLMModel):
            raise TypeError("Model class must inherit from LLMModel")
        cls._models[provider] = model_class
    
    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """Get list of supported providers"""
        return list(cls._models.keys())
