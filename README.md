# PDF Agent API

A sophisticated PDF Visual Question Answering system powered by AI agents that can navigate through PDF documents and answer questions about their content.

## Features

- 🤖 **AI-Powered Navigation**: Uses smolagents to intelligently navigate through PDF pages
- 📄 **Visual Question Answering**: Analyzes PDF content visually to answer questions
- 🚀 **FastAPI Integration**: RESTful API for easy integration
- 📊 **Comprehensive Evaluation**: Built-in evaluation system with LLM-based judging
- 🎯 **Page Navigation**: Smart navigation tools (next_page, previous_page, go_to_page)

## Project Structure

```
pdf-agent-api/
├── src/                          # Source code
│   ├── main.py                   # FastAPI application
│   ├── settings.py               # Configuration management
│   ├── prompts.py                # AI agent prompts
│   └── visual_qa.py              # Visual QA tool implementation
├── eval/                         # Evaluation framework
│   ├── evaluate.py               # Evaluation logic
│   ├── run_eval.py               # CLI evaluation runner
│   ├── eval_set.jsonl            # Evaluation dataset
│   └── results/                  # Evaluation results
├── tests/                        # Test files
├── .pre-commit-config.yaml       # Pre-commit hooks
├── pyproject.toml                # Project configuration
└── README.md                     # This file
```

## Installation

### Prerequisites

- Python 3.12+
- `uv` package manager

### Setup

1. Clone the repository:
```bash
git clone git@github.com:zwischenraum/pdf-agent-api.git
cd pdf-agent-api
```

2. Install dependencies using uv:
```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

Or using pip:
```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

3. Set up pre-commit hooks:
```bash
pre-commit install
```

4. Configure environment variables:
```bash
cp env.example .env
# Edit .env with your API configuration
```

### Environment Variables

Create a `.env` file with the following variables:

```env
API_BASE=http://localhost:11434
API_KEY=your_api_key_here
MODEL_ID=google/gemma-3-27b-it
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

## Usage

### Starting the API Server

1. Run the FastAPI server:
```bash
python src/main.py
# Or using the console script:
pdf-agent-api
```

2. The API will be available at `http://localhost:8000`

### API Endpoints

#### POST /ask_pdf

Ask questions about a PDF document.

**Request:**
- `file`: PDF file (multipart/form-data)
- `question`: Question string (form data)

**Response:**
```json
{
  "answer": "The answer to your question",
  "page": 3
}
```

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/ask_pdf" \
  -F "file=@path/to/document.pdf" \
  -F "question=What is the total revenue mentioned in the report?"
```

### Running Evaluations

The project includes a comprehensive evaluation framework:

```bash
# Run evaluation with default settings
python eval/run_eval.py

# Or using the console script
run-eval

# Custom evaluation
python eval/run_eval.py \
  --eval-set eval/eval_set.jsonl \
  --image tests/test.png \
  --output my_results.json
```

### Development

#### Code Quality

The project uses ruff for linting and formatting:

```bash
# Check code quality
ruff check .
ruff format --check .

# Auto-fix issues
ruff check --fix .
ruff format .
```

## How It Works

### Agent Architecture

The system uses a sophisticated AI agent architecture:

1. **PDF State Management**: Tracks current page and navigation state
2. **Tool-based Navigation**: Provides `next_page()`, `previous_page()`, and `go_to_page()` tools
3. **Visual Analysis**: Uses vision-language models to analyze PDF page images
4. **Smart Memory Management**: Optimizes memory by managing image history
5. **Step-by-step Reasoning**: Follows a thought-code-observation pattern

### Evaluation System

The evaluation framework includes:

- **LLM Judge**: Uses the same model to grade answer quality
- **Semantic Matching**: Compares predicted vs expected answers semantically
- **Detailed Reporting**: Provides comprehensive evaluation metrics
- **Result Tracking**: Saves detailed results for analysis

## Configuration

### Model Configuration

The system supports various vision-language models through LiteLLM:

- **Hosted Models**: Configure via `API_BASE` and `MODEL_ID`
- **Local Models**: Use with Ollama or similar local serving
- **Cloud APIs**: OpenAI, Anthropic, Google, etc.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [SmolagAgents](https://github.com/huggingface/smolagents) for the agent framework
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [Ruff](https://github.com/astral-sh/ruff) for code quality
