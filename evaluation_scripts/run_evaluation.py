#!/usr/bin/env python3
"""
Main evaluation runner script.

Provides three modes:
1. Single - Evaluate one prompt with one model
2. Batch - Evaluate multiple prompts with one model
3. Compare - Evaluate multiple models on same prompts
"""

import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from config import Config
from models import ModelFactory
from evaluator import Evaluator
from dataset_loader import DatasetLoader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EvaluationRunner:
    """Main evaluation orchestrator"""
    
    def __init__(self):
        """Initialize the runner"""
        self.evaluator = Evaluator()
        self.results = []
    
    def evaluate_single(self, model_spec: str, prompt: str, verbose: bool = False) -> Dict[str, Any]:
        """Evaluate a single prompt with one model
        
        Args:
            model_spec: Model specification (provider:model_name)
            prompt: The prompt to evaluate
            verbose: Print detailed output
            
        Returns:
            Evaluation result
        """
        # Parse model spec
        provider, model_name = self._parse_model_spec(model_spec)
        
        if verbose:
            logger.info(f"Creating model: {provider}:{model_name}")
        
        # Create model
        model = ModelFactory.create(provider, model_name)
        
        if verbose:
            logger.info(f"Generating response for prompt: {prompt[:100]}...")
        
        # Generate response
        response = model.generate(prompt)
        
        if verbose:
            logger.info(f"Response: {response[:100]}...")
        
        # Evaluate
        result = self.evaluator.evaluate(prompt, response, model_spec)
        self.results.append(result)
        
        if verbose:
            print(f"\nEvaluation Result:")
            print(f"Model: {model_spec}")
            print(f"Overall Score: {result.overall_score:.2f}/100")
            print(f"\nMetric Scores:")
            for metric, score in result.metric_scores.items():
                print(f"  {metric.upper()}: {score.score:.2f}/100")
        
        return result.to_dict()
    
    def evaluate_batch(self, model_spec: str, prompts: List[str], verbose: bool = False) -> List[Dict[str, Any]]:
        """Evaluate multiple prompts with one model
        
        Args:
            model_spec: Model specification
            prompts: List of prompts
            verbose: Print detailed output
            
        Returns:
            List of evaluation results
        """
        results = []
        provider, model_name = self._parse_model_spec(model_spec)
        model = ModelFactory.create(provider, model_name)
        
        logger.info(f"Evaluating {len(prompts)} prompts with {model_spec}")
        
        for i, prompt in enumerate(prompts, 1):
            if verbose:
                logger.info(f"[{i}/{len(prompts)}] Processing prompt: {prompt[:50]}...")
            
            response = model.generate(prompt)
            result = self.evaluator.evaluate(prompt, response, model_spec)
            results.append(result.to_dict())
            self.results.append(result)
        
        logger.info(f"Completed batch evaluation of {len(prompts)} prompts")
        return results
    
    def evaluate_compare(self, model_specs: List[str], prompts: List[str], verbose: bool = False) -> Dict[str, Any]:
        """Compare multiple models on same prompts
        
        Args:
            model_specs: List of model specifications
            prompts: List of prompts
            verbose: Print detailed output
            
        Returns:
            Comparison results
        """
        comparison_results = {}
        
        logger.info(f"Comparing {len(model_specs)} models on {len(prompts)} prompts")
        
        for model_spec in model_specs:
            if verbose:
                logger.info(f"Evaluating with model: {model_spec}")
            
            model_results = self.evaluate_batch(model_spec, prompts, verbose=False)
            
            # Calculate statistics
            scores = [r["overall_score"] for r in model_results]
            comparison_results[model_spec] = {
                "results": model_results,
                "average_score": sum(scores) / len(scores),
                "min_score": min(scores),
                "max_score": max(scores),
                "total_evaluations": len(model_results),
            }
        
        logger.info("Model comparison completed")
        return comparison_results
    
    def save_results(self, output_file: str = None, format: str = "json") -> str:
        """Save results to file
        
        Args:
            output_file: Output file path (auto-generated if not provided)
            format: Output format (json, csv)
            
        Returns:
            Path to output file
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = str(Config.RESULTS_DIR / f"evaluation_{timestamp}.{format}")
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            data = [r.to_dict() if hasattr(r, 'to_dict') else r for r in self.results]
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
        
        elif format == "csv":
            import pandas as pd
            data = [r.to_dict() if hasattr(r, 'to_dict') else r for r in self.results]
            df = pd.json_normalize(data)
            df.to_csv(output_path, index=False)
        
        logger.info(f"Results saved to {output_path}")
        return str(output_path)
    
    @staticmethod
    def _parse_model_spec(model_spec: str) -> tuple:
        """Parse model specification string
        
        Args:
            model_spec: Format: provider:model_name
            
        Returns:
            (provider, model_name) tuple
        """
        if ":" not in model_spec:
            raise ValueError(f"Invalid model spec format. Expected 'provider:model', got '{model_spec}'")
        
        parts = model_spec.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid model spec format: {model_spec}")
        
        return parts[0].strip(), parts[1].strip()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="LLM Prompt Evaluation Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single evaluation
  python run_evaluation.py single --model mock:test --prompt "What is AI?"
  
  # Batch evaluation
  python run_evaluation.py batch --model openai:gpt-4 --prompts-file ../prompts/test.txt
  
  # Model comparison
  python run_evaluation.py compare --models openai:gpt-4 openai:gpt-3.5-turbo --prompts-file ../prompts/benchmark.json
        """
    )
    
    subparsers = parser.add_subparsers(dest="mode", help="Evaluation mode")
    
    # Single evaluation
    single_parser = subparsers.add_parser("single", help="Evaluate single prompt")
    single_parser.add_argument("--model", required=True, help="Model spec (provider:model_name)")
    single_parser.add_argument("--prompt", required=True, help="Prompt to evaluate")
    single_parser.add_argument("--output", help="Output file path")
    single_parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format")
    single_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    # Batch evaluation
    batch_parser = subparsers.add_parser("batch", help="Evaluate multiple prompts")
    batch_parser.add_argument("--model", required=True, help="Model spec")
    batch_parser.add_argument("--prompts-file", required=True, help="File with prompts")
    batch_parser.add_argument("--column", help="Column name for CSV/Excel")
    batch_parser.add_argument("--output", help="Output file path")
    batch_parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format")
    batch_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    # Comparison
    compare_parser = subparsers.add_parser("compare", help="Compare models")
    compare_parser.add_argument("--models", nargs="+", required=True, help="Models to compare")
    compare_parser.add_argument("--prompts-file", required=True, help="File with prompts")
    compare_parser.add_argument("--column", help="Column name")
    compare_parser.add_argument("--output", help="Output file path")
    compare_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if not args.mode:
        parser.print_help()
        return
    
    runner = EvaluationRunner()
    
    try:
        if args.mode == "single":
            runner.evaluate_single(args.model, args.prompt, args.verbose)
            runner.save_results(args.output, args.format)
        
        elif args.mode == "batch":
            prompts = DatasetLoader.load(args.prompts_file, args.column)
            runner.evaluate_batch(args.model, prompts, args.verbose)
            runner.save_results(args.output, args.format)
        
        elif args.mode == "compare":
            prompts = DatasetLoader.load(args.prompts_file, args.column)
            results = runner.evaluate_compare(args.models, prompts, args.verbose)
            output_file = args.output or str(Config.RESULTS_DIR / f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Comparison results saved to {output_file}")
    
    except Exception as e:
        logger.error(f"Error during evaluation: {str(e)}")
        raise


if __name__ == "__main__":
    main()
