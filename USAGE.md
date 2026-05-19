# LLM Evaluation Framework - Usage Guide

Comprehensive guide for using the prompt-evaluation-benchmark framework.

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Basic Usage](#basic-usage)
4. [Advanced Usage](#advanced-usage)
5. [Examples](#examples)
6. [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- API keys for LLM providers (optional, depending on which models you use)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/MingiVenkataRamaSatyaSriKrishna/prompt-evaluation-benchmark.git
   cd prompt-evaluation-benchmark
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp evaluation_scripts/.env.example evaluation_scripts/.env
   # Edit .env with your API keys
   ```

---

## Configuration

### Environment Variables

Edit `.env` file in `evaluation_scripts/` directory:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4

# HuggingFace Configuration
HUGGINGFACE_API_KEY=your_key_here
HUGGINGFACE_MODEL=meta-llama/Llama-2-7b-hf

# Evaluation Settings
DEFAULT_TIMEOUT=60
MAX_RETRIES=3
BATCH_SIZE=10

# Results
SAVE_RESULTS=true
RESULTS_FORMAT=json
GENERATE_VISUALIZATIONS=true
```

### Configuration File

The `config.py` file contains:

- **Directory paths** - Locations for prompts, datasets, results
- **API credentials** - Loaded from environment variables
- **Metrics definitions** - 7 evaluation metrics with weights
- **Supported models** - Registry of available models

---

## Basic Usage

### 1. Single Prompt Evaluation

Evaluate one prompt with one model:

```bash
cd evaluation_scripts
python run_evaluation.py single \
    --model mock:test \
    --prompt "What is artificial intelligence?"
```

**Options:**
- `--model`: Model specification (provider:model_name)
- `--prompt`: Text prompt to evaluate
- `--output`: Output file path (optional)
- `--format`: Output format: json or csv (default: json)
- `-v, --verbose`: Print detailed output

### 2. Batch Evaluation

Evaluate multiple prompts with one model:

```bash
cd evaluation_scripts
python run_evaluation.py batch \
    --model openai:gpt-4 \
    --prompts-file ../prompts/questions.txt
```

**Supported file formats:**
- `.txt` - One prompt per line
- `.csv` - Use `--column` to specify which column
- `.json` - Array or array of objects
- `.xlsx` - Use `--column` for specific column

### 3. Model Comparison

Compare multiple models on the same prompts:

```bash
cd evaluation_scripts
python run_evaluation.py compare \
    --models openai:gpt-4 openai:gpt-3.5-turbo mock:test \
    --prompts-file ../prompts/benchmark.csv
```

### 4. Generate Reports

Create visual reports from evaluation results:

```bash
cd evaluation_scripts
python generate_report.py \
    --results-file ../results/evaluation_*.json \
    --format html
```

**Report formats:**
- `html` - Interactive HTML report with statistics
- `csv` - Spreadsheet-compatible format
- `all` - Generate both formats

---

## Advanced Usage

### Custom Models

Register custom model providers:

```python
from models import ModelFactory, LLMModel

class CustomModel(LLMModel):
    def generate(self, prompt: str, **kwargs) -> str:
        # Your implementation
        return "response"

# Register the model
ModelFactory.register_model("custom", CustomModel)

# Use it
model = ModelFactory.create("custom", "my-model")
```

### Custom Metrics

Extend the evaluator with custom metrics:

```python
from evaluator import Evaluator, MetricScore

class CustomEvaluator(Evaluator):
    def score_custom_metric(self, response: str, prompt: str) -> MetricScore:
        # Your scoring logic
        score = 75.0
        return MetricScore(
            metric="custom",
            score=score,
            weight=0.1,
            reasoning="Custom evaluation"
        )
```

### Programmatic API

Use the framework in your own scripts:

```python
from evaluation_scripts.config import Config
from evaluation_scripts.models import ModelFactory
from evaluation_scripts.evaluator import Evaluator
from evaluation_scripts.dataset_loader import DatasetLoader

# Load prompts
prompts = DatasetLoader.load("prompts/test.csv", column="question")

# Create model and evaluator
model = ModelFactory.create("mock", "test")
evaluator = Evaluator()

# Evaluate
for prompt in prompts:
    response = model.generate(prompt)
    result = evaluator.evaluate(prompt, response, "mock:test")
    print(f"Score: {result.overall_score:.2f}")

# Get summary
summary = evaluator.get_summary()
print(f"Average: {summary['average_score']:.2f}")
```

---

## Examples

### Example 1: Quick Test with Mock Model

```bash
# Single evaluation
python run_evaluation.py single \
    --model mock:test \
    --prompt "Explain machine learning" \
    -v

# Output:
# Evaluation Result:
# Model: mock:test
# Overall Score: 75.23/100
# 
# Metric Scores:
#   ACCURACY: 80.00/100
#   RELEVANCE: 75.00/100
#   COHERENCE: 78.00/100
#   ...
```

### Example 2: Compare Real Models

```bash
# Create test prompts
cat > prompts/ai_questions.txt << EOF
What is artificial intelligence?
Explain machine learning
What is deep learning?
EOF

# Compare models (requires API keys)
python run_evaluation.py compare \
    --models openai:gpt-4 openai:gpt-3.5-turbo \
    --prompts-file ../prompts/ai_questions.txt \
    --output ../results/comparison.json

# Generate report
python generate_report.py \
    --results-file ../results/comparison.json \
    --format html \
    --output ../results/comparison_report.html
```

### Example 3: Batch Evaluation from CSV

```bash
# Create CSV with prompts
cat > datasets/test_data.csv << EOF
question,category
What is AI?,basics
How does ML work?,advanced
EOF

# Run batch evaluation
python run_evaluation.py batch \
    --model mock:test \
    --prompts-file ../datasets/test_data.csv \
    --column question \
    --output ../results/batch_results.json \
    --format json
```

### Example 4: Programmatic Usage

```python
# script.py
from evaluation_scripts.models import ModelFactory
from evaluation_scripts.evaluator import Evaluator

# Create components
model = ModelFactory.create("mock", "test")
evaluator = Evaluator()

# Evaluate multiple prompts
prompts = [
    "What is AI?",
    "Explain machine learning",
    "What is deep learning?"
]

for prompt in prompts:
    response = model.generate(prompt)
    result = evaluator.evaluate(prompt, response, "mock:test")
    print(f"Prompt: {prompt}")
    print(f"Score: {result.overall_score:.2f}\n")

# Print summary
summary = evaluator.get_summary()
print(f"Average Score: {summary['average_score']:.2f}")
```

---

## Troubleshooting

### Issue: "API Key not found"

**Solution:**
1. Ensure `.env` file exists in `evaluation_scripts/`
2. Set the appropriate API key: `OPENAI_API_KEY` or `HUGGINGFACE_API_KEY`
3. Reload the environment: `source venv/bin/activate`

### Issue: "Module not found"

**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
python -c "import pandas; import openai; print('OK')"
```

### Issue: "Timeout during evaluation"

**Solution:**
1. Increase `DEFAULT_TIMEOUT` in `.env`
2. Check network connection
3. Verify API key has proper permissions

### Issue: "File not found" for prompts

**Solution:**
```bash
# Verify file path
ls ../prompts/

# Use absolute path if needed
python run_evaluation.py batch \
    --model mock:test \
    --prompts-file /absolute/path/to/prompts.txt
```

### Issue: Results not saving

**Solution:**
1. Check `SAVE_RESULTS=true` in `.env`
2. Verify write permissions in `results/` directory
3. Use explicit `--output` path:
   ```bash
   python run_evaluation.py single \
       --model mock:test \
       --prompt "test" \
       --output ./my_results.json
   ```

---

## Best Practices

1. **Use Mock Model for Testing** - Start with `mock:test` to verify setup
2. **Start Small** - Evaluate a few prompts before large batches
3. **Save Results** - Always save results for reproducibility
4. **Use Specific Models** - Specify exact model names (e.g., `gpt-4`, not just `openai`)
5. **Monitor Costs** - API calls may incur charges; check rate limits
6. **Batch Evaluation** - Use batch mode for efficiency with multiple prompts
7. **Regular Backups** - Back up results directory periodically

---

## Support

For issues or questions:
1. Check this guide's Troubleshooting section
2. Review example scripts
3. Open an issue on GitHub
4. Check API provider documentation

---

**Last Updated:** 2026-05-19
