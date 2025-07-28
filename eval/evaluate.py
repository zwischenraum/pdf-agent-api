import json
from datetime import datetime
from pathlib import Path
from typing import Any

from openai import OpenAI

from src.settings import settings
from src.visual_qa import VisualQATool, encode_image

JUDGE_SYSTEM_PROMPT = """You are an expert evaluator for question-answering systems.

Your task is to compare a predicted answer with the expected answer and determine if they are semantically equivalent.

Consider these factors:
- Exact matches are always correct
- Different formatting of the same information should be considered correct (e.g., "978,35 EUR" vs "978.35 EUR")
- Minor variations in date formats should be considered correct (e.g., "04.10.2018" vs "4.10.2018")
- Semantic equivalence matters more than exact string matching
- Partial answers that contain the key information should be considered correct
- If the predicted answer contains "No answer in page" or similar, it should be considered incorrect unless the expected answer also indicates no answer

Respond with exactly one word: either "correct" or "incorrect"."""


class EvaluationResults:
    """Class to manage evaluation results and reporting."""

    def __init__(self):
        self.results: list[dict[str, Any]] = []
        self.total_questions = 0
        self.correct_answers = 0

    def add_result(self, question: str, expected: str, predicted: str, grade: str):
        """Add a single evaluation result."""
        is_correct = grade.lower().strip() == "correct"
        result = {
            "question": question,
            "expected_answer": expected,
            "predicted_answer": predicted,
            "grade": grade,
            "is_correct": is_correct,
        }
        self.results.append(result)
        self.total_questions += 1
        if is_correct:
            self.correct_answers += 1

    def get_accuracy(self) -> float:
        """Calculate accuracy percentage."""
        if self.total_questions == 0:
            return 0.0
        return (self.correct_answers / self.total_questions) * 100

    def save_detailed_results(self, filename: str):
        """Save detailed results to JSON file."""
        output = {
            "evaluation_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_questions": self.total_questions,
                "correct_answers": self.correct_answers,
                "accuracy": self.get_accuracy(),
            },
            "results": self.results,
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

    def print_summary(self):
        """Print evaluation summary to console."""
        print("\n" + "=" * 60)
        print("EVALUATION SUMMARY")
        print("=" * 60)
        print(f"Total Questions: {self.total_questions}")
        print(f"Correct Answers: {self.correct_answers}")
        print(f"Incorrect Answers: {self.total_questions - self.correct_answers}")
        print(f"Accuracy: {self.get_accuracy():.1f}%")
        print("=" * 60)

        print("\nDETAILED RESULTS:")
        print("-" * 60)
        for i, result in enumerate(self.results, 1):
            status = "✓" if result["is_correct"] else "✗"
            print(f"{i:2d}. {status} Question: {result['question']}")
            print(f"    Expected: {result['expected_answer']}")
            print(f"    Predicted: {result['predicted_answer']}")
            print(f"    Grade: {result['grade']}")
            print()


class LLMJudge:
    """LLM-based judge for grading QA answers."""

    def __init__(self, model_id: str, api_base: str, api_key: str):
        self.client = OpenAI(api_key=api_key, base_url=api_base)
        self.model_id = model_id

    def grade_answer(self, question: str, expected_answer: str, predicted_answer: str) -> str:
        """Grade a single answer using the LLM judge."""
        user_prompt = f"""Question: {question}

Expected Answer: {expected_answer}

Predicted Answer: {predicted_answer}

Are these answers semantically equivalent?"""

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,  # Make grading deterministic
                max_tokens=10,  # We only need "correct" or "incorrect"
            )

            grade = response.choices[0].message.content.strip().lower()
            # Ensure we get a valid response
            if grade not in ["correct", "incorrect"]:
                print(f"Warning: Unexpected judge response '{grade}', defaulting to 'incorrect'")
                return "incorrect"
            return grade

        except Exception as e:
            print(f"Error in LLM judge: {e}")
            return "incorrect"  # Conservative default


def load_eval_set(filepath: str) -> list[dict[str, str]]:
    """Load evaluation questions and answers from JSONL file."""
    eval_data = []
    try:
        with open(filepath, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    eval_data.append(json.loads(line))
        print(f"Loaded {len(eval_data)} questions from {filepath}")
        return eval_data
    except FileNotFoundError:
        print(f"Error: Evaluation file '{filepath}' not found.")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON in {filepath}: {e}")
        return []


def run_evaluation(
    eval_set_path: str = "eval/eval_set.jsonl",
    image_path: str = "tests/test.png",
    output_file: str = None,
):
    """Run the complete evaluation pipeline."""

    # Set default output filename if not provided
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"evaluation_results_{timestamp}.json"

    print("Starting Visual QA Evaluation Pipeline")
    print("=" * 50)

    # Verify image file exists
    if not Path(image_path).exists():
        print(f"Error: Image file '{image_path}' not found.")
        return

    # Load evaluation set
    eval_data = load_eval_set(eval_set_path)
    if not eval_data:
        return

    # Initialize tools
    print(f"Initializing Visual QA tool with model: {settings.model_id}")
    visual_qa_tool = VisualQATool(
        model_id=settings.model_id, api_base=settings.api_base, api_key=settings.api_key
    )

    print(f"Initializing LLM Judge with model: {settings.model_id}")
    judge = LLMJudge(
        model_id=settings.model_id, api_base=settings.api_base, api_key=settings.api_key
    )

    # Encode image once
    print(f"Encoding image: {image_path}")
    try:
        base64_image = encode_image(image_path)
    except Exception as e:
        print(f"Error encoding image: {e}")
        return

    # Initialize results tracker
    results = EvaluationResults()

    # Process each question
    print(f"\nProcessing {len(eval_data)} questions...")
    print("-" * 50)

    for i, item in enumerate(eval_data, 1):
        question = item.get("question", "")
        expected_answer = item.get("answer", "")

        print(f"[{i}/{len(eval_data)}] Processing: {question}")

        # Get prediction from visual QA tool
        try:
            predicted_answer = visual_qa_tool(base64_image, question)
            print(f"  Predicted: {predicted_answer}")
        except Exception as e:
            print(f"  Error in visual QA: {e}")
            predicted_answer = f"Error: {str(e)}"

        # Grade the answer using LLM judge
        try:
            grade = judge.grade_answer(question, expected_answer, predicted_answer)
            print(f"  Grade: {grade}")
        except Exception as e:
            print(f"  Error in grading: {e}")
            grade = "incorrect"

        # Add to results
        results.add_result(question, expected_answer, predicted_answer, grade)
        print()

    # Save and display results
    print(f"Saving detailed results to: {output_file}")
    results.save_detailed_results(output_file)

    # Print summary
    results.print_summary()

    return results


if __name__ == "__main__":
    """Run evaluation when script is executed directly."""
    # Check if required environment variables are set
    if not settings.api_key or not settings.api_base:
        print(
            "Warning: API key or base URL not configured. Please check your .env file or environment variables."
        )
        print("Required settings:")
        print(f"  API_BASE: {settings.api_base}")
        print(f"  API_KEY: {'*' * 10 if settings.api_key else 'Not set'}")
        print(f"  MODEL_ID: {settings.model_id}")
        print()

    # Run the evaluation
    results = run_evaluation()

    if results:
        print(f"\nEvaluation completed! Final accuracy: {results.get_accuracy():.1f}%")
    else:
        print("Evaluation failed to complete.")
