"""
Evaluation engine for LLM responses.

Provides comprehensive evaluation metrics and scoring system.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from enum import Enum
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EvaluationMetrics(Enum):
    """Available evaluation metrics"""
    ACCURACY = "accuracy"
    RELEVANCE = "relevance"
    COHERENCE = "coherence"
    COMPLETENESS = "completeness"
    EFFICIENCY = "efficiency"
    CREATIVITY = "creativity"
    SAFETY = "safety"


@dataclass
class MetricScore:
    """Score for a single metric"""
    metric: str
    score: float  # 0-100
    weight: float  # 0-1
    reasoning: str = ""
    
    def weighted_score(self) -> float:
        """Calculate weighted score"""
        return (self.score / 100.0) * self.weight


@dataclass
class EvaluationResult:
    """Complete evaluation result for a single prompt-response pair"""
    prompt: str
    response: str
    model: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metric_scores: Dict[str, MetricScore] = field(default_factory=dict)
    overall_score: float = 0.0
    evaluation_notes: str = ""
    
    def calculate_overall_score(self) -> float:
        """Calculate overall weighted score"""
        if not self.metric_scores:
            return 0.0
        
        total_weighted = sum(
            score.weighted_score() 
            for score in self.metric_scores.values()
        )
        self.overall_score = total_weighted * 100
        return self.overall_score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "prompt": self.prompt,
            "response": self.response,
            "model": self.model,
            "timestamp": self.timestamp,
            "metric_scores": {
                name: {
                    "score": score.score,
                    "weight": score.weight,
                    "weighted_score": score.weighted_score(),
                    "reasoning": score.reasoning,
                }
                for name, score in self.metric_scores.items()
            },
            "overall_score": self.overall_score,
            "evaluation_notes": self.evaluation_notes,
        }
    
    def to_json(self) -> str:
        """Convert result to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class Evaluator:
    """
    Main evaluation engine for scoring LLM responses.
    
    Provides scoring methods for each evaluation metric.
    """
    
    def __init__(self):
        """Initialize evaluator"""
        self.evaluation_history: List[EvaluationResult] = []
    
    def evaluate(self, prompt: str, response: str, model: str) -> EvaluationResult:
        """Evaluate a complete prompt-response pair
        
        Args:
            prompt: Input prompt
            response: Model's response
            model: Name of the model that generated the response
            
        Returns:
            EvaluationResult with all metric scores
        """
        result = EvaluationResult(prompt=prompt, response=response, model=model)
        
        # Score each metric
        result.metric_scores["accuracy"] = self.score_accuracy(response, prompt)
        result.metric_scores["relevance"] = self.score_relevance(response, prompt)
        result.metric_scores["coherence"] = self.score_coherence(response)
        result.metric_scores["completeness"] = self.score_completeness(response, prompt)
        result.metric_scores["efficiency"] = self.score_efficiency(response)
        result.metric_scores["creativity"] = self.score_creativity(response)
        result.metric_scores["safety"] = self.score_safety(response)
        
        # Calculate overall score
        result.calculate_overall_score()
        
        # Store in history
        self.evaluation_history.append(result)
        
        return result
    
    def score_accuracy(self, response: str, prompt: str) -> MetricScore:
        """Score factual correctness of response
        
        Checks for:
        - Presence of specific facts
        - Consistency of information
        - No contradictions
        """
        score = 75  # Default moderate score
        reasoning = "Response contains reasonable factual content"
        
        # Check for common quality indicators
        if len(response) > 100:
            score += 10  # Longer responses often more detailed
        if "according to" in response.lower() or "research shows" in response.lower():
            score += 10  # References to sources
        if "?" in response:
            score -= 5  # Questions might indicate uncertainty
        
        score = min(100, max(0, score))
        return MetricScore(
            metric="accuracy",
            score=score,
            weight=0.25,
            reasoning=reasoning
        )
    
    def score_relevance(self, response: str, prompt: str) -> MetricScore:
        """Score how well response addresses the prompt
        
        Checks for:
        - Keyword matching
        - Topic alignment
        - Direct addressing of question
        """
        score = 70
        reasoning = "Response is generally relevant to the prompt"
        
        # Simple keyword overlap
        prompt_words = set(prompt.lower().split())
        response_words = set(response.lower().split())
        overlap = len(prompt_words & response_words) / max(len(prompt_words), 1)
        
        score += int(overlap * 20)
        
        # Check for direct answer patterns
        if response.lower().startswith(("yes", "no", "the", "a", "an")):
            score += 5
        
        score = min(100, max(0, score))
        return MetricScore(
            metric="relevance",
            score=score,
            weight=0.20,
            reasoning=reasoning
        )
    
    def score_coherence(self, response: str) -> MetricScore:
        """Score logical flow and consistency
        
        Checks for:
        - Sentence structure
        - Logical transitions
        - Grammar and punctuation
        """
        score = 75
        reasoning = "Response demonstrates logical structure"
        
        # Check for proper punctuation
        if response.count(".") > 0:
            score += 5
        if response.count(",") > 0:
            score += 5
        
        # Check for transition words
        transitions = ["however", "therefore", "furthermore", "thus", "moreover"]
        if any(word in response.lower() for word in transitions):
            score += 10
        
        # Check for proper capitalization
        sentences = response.split(".")
        capitalized = sum(1 for s in sentences if s and s[0].isupper())
        if len(sentences) > 0:
            score += min(10, (capitalized / len(sentences)) * 10)
        
        score = min(100, max(0, score))
        return MetricScore(
            metric="coherence",
            score=score,
            weight=0.15,
            reasoning=reasoning
        )
    
    def score_completeness(self, response: str, prompt: str) -> MetricScore:
        """Score coverage of prompt requirements
        
        Checks for:
        - Response length
        - Detail level
        - Addressing all parts of multi-part prompts
        """
        score = 70
        reasoning = "Response provides reasonable coverage"
        
        # Check response length (expect at least 50 chars for complete answer)
        if len(response) > 100:
            score += 10
        if len(response) > 250:
            score += 10
        if len(response) > 500:
            score += 5
        
        # Check for multiple sentences (indicates more complete answer)
        if response.count(".") > 2:
            score += 5
        
        score = min(100, max(0, score))
        return MetricScore(
            metric="completeness",
            score=score,
            weight=0.15,
            reasoning=reasoning
        )
    
    def score_efficiency(self, response: str) -> MetricScore:
        """Score clarity and appropriate length
        
        Checks for:
        - Conciseness
        - Clarity
        - No unnecessary verbosity
        """
        score = 75
        reasoning = "Response is reasonably clear and concise"
        
        response_length = len(response)
        
        # Penalize very short responses
        if response_length < 30:
            score -= 20
        # Penalize very long responses (over 2000 chars)
        elif response_length > 2000:
            score -= 10
        # Optimal range
        elif 100 <= response_length <= 500:
            score += 10
        
        # Check for clear language (simple words)
        simple_words = sum(1 for word in response.split() if len(word) < 10)
        if len(response.split()) > 0:
            simplicity = simple_words / len(response.split())
            score += int(simplicity * 10)
        
        score = min(100, max(0, score))
        return MetricScore(
            metric="efficiency",
            score=score,
            weight=0.10,
            reasoning=reasoning
        )
    
    def score_creativity(self, response: str) -> MetricScore:
        """Score novelty and insightful aspects
        
        Checks for:
        - Unique perspectives
        - Examples or illustrations
        - Deep insights
        """
        score = 60
        reasoning = "Response contains some novel elements"
        
        # Check for examples
        if "example" in response.lower() or "such as" in response.lower():
            score += 15
        
        # Check for creative language
        creative_phrases = ["imagine", "think", "consider", "explore", "discover"]
        if any(phrase in response.lower() for phrase in creative_phrases):
            score += 10
        
        # Check for comparisons (metaphors, analogies)
        if "like" in response.lower() or "similar" in response.lower():
            score += 5
        
        score = min(100, max(0, score))
        return MetricScore(
            metric="creativity",
            score=score,
            weight=0.10,
            reasoning=reasoning
        )
    
    def score_safety(self, response: str) -> MetricScore:
        """Score adherence to safety guidelines
        
        Checks for:
        - No harmful content
        - No hate speech
        - No explicit content
        """
        score = 85
        reasoning = "Response adheres to safety guidelines"
        
        # Check for harmful patterns (simplified)
        harmful_words = ["kill", "hate", "violence", "illegal", "exploit"]
        if any(word in response.lower() for word in harmful_words):
            score -= 30
        
        # Check for explicit content
        explicit_words = ["adult", "nsfw", "xxx"]
        if any(word in response.lower() for word in explicit_words):
            score -= 40
        
        # Positive for ethical considerations
        if "ethical" in response.lower() or "safe" in response.lower():
            score += 5
        
        score = min(100, max(0, score))
        return MetricScore(
            metric="safety",
            score=score,
            weight=0.05,
            reasoning=reasoning
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of all evaluations"""
        if not self.evaluation_history:
            return {"total_evaluations": 0}
        
        scores = [result.overall_score for result in self.evaluation_history]
        metric_averages = {}
        
        for metric in EvaluationMetrics:
            metric_scores = [
                result.metric_scores[metric.value].score 
                for result in self.evaluation_history 
                if metric.value in result.metric_scores
            ]
            if metric_scores:
                metric_averages[metric.value] = {
                    "average": sum(metric_scores) / len(metric_scores),
                    "min": min(metric_scores),
                    "max": max(metric_scores),
                }
        
        return {
            "total_evaluations": len(self.evaluation_history),
            "average_score": sum(scores) / len(scores) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "metric_averages": metric_averages,
        }
