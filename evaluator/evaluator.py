import argparse
import json
import multiprocessing as mp
import random
import signal
import ssl
import sys
import threading
import time
from collections import defaultdict
from datetime import datetime
from multiprocessing import Lock, Manager, Queue
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import yaml
from loguru import logger
from torchvision import os
from tqdm import tqdm

from method.utils.mllm_factory import MLLMFactory


def load_single_concept_data(concept_id: str) -> Dict[str, Any]:
    """Static function to load concept data for multiprocessing."""
    concept_path = Path("data/concept") / concept_id
    data = {"easy": {}, "hard": {}}

    # Load easy questions
    easy_path = concept_path / "easy_question.yaml"
    if easy_path.exists():
        try:
            with open(easy_path, "r", encoding="utf-8") as f:
                easy_questions = yaml.safe_load(f) or []
            for q in easy_questions:
                data["easy"][q["id"]] = q
        except Exception as e:
            print(f"Error loading easy questions for {concept_id}: {e}")

    # Load hard questions
    hard_path = concept_path / "hard_question.yaml"
    if hard_path.exists():
        try:
            with open(hard_path, "r", encoding="utf-8") as f:
                hard_questions = yaml.safe_load(f) or []
            for q in hard_questions:
                data["hard"][q["id"]] = q
        except Exception as e:
            print(f"Error loading hard questions for {concept_id}: {e}")

    return data


def load_all_concepts() -> Dict[str, Any]:
    """Static function to load all concept data for multiprocessing."""
    concepts_path = Path("data/concept")
    concept_data = {}

    if not concepts_path.exists():
        print(f"Concepts directory not found: {concepts_path}")
        return concept_data

    for concept_dir in concepts_path.iterdir():
        if concept_dir.is_dir():
            concept_id = concept_dir.name
            concept_data[concept_id] = load_single_concept_data(concept_id)

    return concept_data


def evaluate_single_result_with_retry(evaluator, result, ground_truth, max_retries=3):
    """Helper function to evaluate with retry logic for network errors."""

    for attempt in range(max_retries):
        try:
            if result["difficulty"] == "easy":
                return evaluate_easy_question_static(result, ground_truth, evaluator)
            elif result["difficulty"] == "hard":
                return evaluate_hard_question_static(result, ground_truth, evaluator)
            else:
                raise ValueError(f"Unknown difficulty: {result['difficulty']}")

        except (requests.exceptions.RequestException, ssl.SSLError, ConnectionError) as e:
            if attempt < max_retries - 1:
                wait_time = (2**attempt) * 5  # 5s, 10s, 20s
                logger.warning(f"Network error on attempt {attempt + 1}, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
                continue
            else:
                raise e
        except Exception as e:
            # Don't retry for non-network errors
            raise e


def evaluate_single_result(args_tuple):
    """Worker function to evaluate a single result in multiprocessing."""
    result, concept_data, model_id = args_tuple

    try:
        # Create evaluator instance for this process
        evaluator = MLLMFactory(model_id)

        concept_id = result["concept_id"]
        question_id = result["question_id"]
        difficulty = result["difficulty"]

        # Get ground truth
        if concept_id not in concept_data:
            return None, f"Concept {concept_id} not found"

        if difficulty not in concept_data[concept_id]:
            return None, f"Difficulty {difficulty} not found for concept {concept_id}"

        if question_id not in concept_data[concept_id][difficulty]:
            return None, f"Question {question_id} not found for {concept_id}/{difficulty}"

        ground_truth = concept_data[concept_id][difficulty][question_id]

        # Evaluate with retry logic for network errors
        evaluation = evaluate_single_result_with_retry(evaluator, result, ground_truth)

        return evaluation, None

    except Exception as e:
        return (
            None,
            f"Error evaluating {result.get('concept_id', 'unknown')}/{result.get('question_id', 'unknown')}: {str(e)}",
        )


def evaluate_choice_accuracy_static(predicted_choice: str, ground_truth: Dict[str, Any]) -> int:
    """Static function for choice accuracy evaluation."""
    if "options" not in ground_truth or "answer" not in ground_truth:
        return 0

    # Map the correct answer to A/B/C/D
    correct_answer = ground_truth["answer"]
    options = ground_truth["options"]

    # Find which option (A/B/C/D) matches the correct answer
    correct_choice = None
    for i, option in enumerate(options):
        if option == correct_answer:
            correct_choice = chr(ord("A") + i)  # Convert 0->A, 1->B, etc.
            break

    if correct_choice is None:
        return 0
    if predicted_choice is None:
        # random one
        predicted_choice = random.choice(["A", "B", "C", "D"])

    return 1 if predicted_choice.upper() == correct_choice else 0


def evaluate_freetext_accuracy_static(predicted_answer: str, ground_truth: Dict[str, Any], evaluator) -> int:
    """Static function for freetext accuracy evaluation."""
    if "evaluation_criteria" not in ground_truth:
        return 0

    ideal_answer = ground_truth["evaluation_criteria"].get("ideal_answer", "")
    if not ideal_answer:
        return 0

    prompt = f"""Please evaluate whether the following predicted answer is an acceptable substitute for the ideal answer.

Ideal Answer: {ideal_answer}

Predicted Answer: {predicted_answer}

Consider:
- Does the predicted answer support the same general conclusion?
- Is the predicted answer factually compatible with the ideal answer (i.e., not contradictory)?
- You may overlook missing nuances or slightly less precise phrasing if the main intent is still preserved.

Respond with only "YES" if the predicted answer is acceptable, or "NO" if it is not."""

    try:
        response = evaluator.chat_text(prompt)
        return 1 if "YES" in response.strip().upper() else 0
    except Exception as e:
        return 0


def evaluate_scoring_point_static(predicted_answer: str, key_point: str, evaluator) -> int:
    """Static function for scoring point evaluation."""
    prompt = f"""Please evaluate whether the following answer addresses the given key point.

Key Point: {key_point}

Answer: {predicted_answer}

Respond with only "YES" if the answer clearly addresses this key point, or "NO" if it doesn't."""

    try:
        response = evaluator.chat_text(prompt)
        return 1 if "YES" in response.strip().upper() else 0
    except Exception as e:
        return 0


def evaluate_easy_question_static(
    result: Dict[str, Any], ground_truth: Dict[str, Any], evaluator
) -> Dict[str, Any]:
    """Static function to evaluate an easy question result."""
    evaluation = {
        "concept_id": result["concept_id"],
        "question_id": result["question_id"],
        "difficulty": result["difficulty"],
    }

    # Choice accuracy
    predicted_choice = result.get("choice", "")
    evaluation["choice_acc"] = evaluate_choice_accuracy_static(predicted_choice, ground_truth)

    # Freetext accuracy
    predicted_answer = result.get("answer", "")
    evaluation["freetext_acc"] = evaluate_freetext_accuracy_static(predicted_answer, ground_truth, evaluator)

    # Scoring point - for easy questions, there should be one key point
    key_points = ground_truth.get("evaluation_criteria", {}).get("key_points", [])
    if key_points:
        # For easy questions, evaluate if the answer addresses the key point(s)
        scoring_point = 0
        for key_point in key_points:
            if evaluate_scoring_point_static(predicted_answer, key_point, evaluator):
                scoring_point = 1
                break  # If any key point is satisfied, mark as 1
        evaluation["scoring_point"] = scoring_point
    else:
        evaluation["scoring_point"] = 0

    return evaluation


def evaluate_hard_question_static(
    result: Dict[str, Any], ground_truth: Dict[str, Any], evaluator
) -> Dict[str, Any]:
    """Static function to evaluate a hard question result."""
    evaluation = {
        "concept_id": result["concept_id"],
        "question_id": result["question_id"],
        "difficulty": result["difficulty"],
    }

    # Choice accuracy
    predicted_choice = result.get("choice", "")
    evaluation["choice_acc"] = evaluate_choice_accuracy_static(predicted_choice, ground_truth)

    # Freetext accuracy
    predicted_answer = result.get("answer", "")
    evaluation["freetext_acc"] = evaluate_freetext_accuracy_static(predicted_answer, ground_truth, evaluator)

    # Scoring points - for hard questions, there should be two key points
    key_points = ground_truth.get("evaluation_criteria", {}).get("key_points", [])
    if len(key_points) >= 2:
        # First key point (long-term information)
        evaluation["scoring_point_long"] = evaluate_scoring_point_static(
            predicted_answer, key_points[0], evaluator
        )
        # Second key point (short-term information)
        evaluation["scoring_point_short"] = evaluate_scoring_point_static(
            predicted_answer, key_points[1], evaluator
        )
    else:
        evaluation["scoring_point_long"] = 0
        evaluation["scoring_point_short"] = 0

    return evaluation


class ConceptEvaluator:
    def __init__(self, model_id: str = "Qwen/Qwen2.5-72B-Instruct"):
        """Initialize the evaluator with an LLM for freetext evaluation."""
        self.model_id = model_id
        self.evaluator = MLLMFactory(model_id)
        self.concept_data = {}
        self.load_all_concepts()

    def load_all_concepts(self):
        """Load all concept data from data/concept directory."""
        self.concept_data = load_all_concepts()

    def get_ground_truth(
        self, concept_id: str, question_id: int, difficulty: str
    ) -> Optional[Dict[str, Any]]:
        """Get ground truth data for a specific question."""
        if concept_id not in self.concept_data:
            logger.warning(f"Concept {concept_id} not found")
            return None

        if difficulty not in self.concept_data[concept_id]:
            logger.warning(f"Difficulty {difficulty} not found for concept {concept_id}")
            return None

        if question_id not in self.concept_data[concept_id][difficulty]:
            logger.warning(f"Question {question_id} not found for {concept_id}/{difficulty}")
            return None

        return self.concept_data[concept_id][difficulty][question_id]

    def evaluate_choice_accuracy(self, predicted_choice: str, ground_truth: Dict[str, Any]) -> int:
        """Evaluate choice accuracy by comparing predicted choice with ground truth answer."""
        return evaluate_choice_accuracy_static(predicted_choice, ground_truth)

    def evaluate_freetext_accuracy(self, predicted_answer: str, ground_truth: Dict[str, Any]) -> int:
        """Evaluate freetext accuracy using LLM comparison with ideal answer."""
        return evaluate_freetext_accuracy_static(predicted_answer, ground_truth, self.evaluator)

    def evaluate_scoring_point(self, predicted_answer: str, key_point: str) -> int:
        """Evaluate if the predicted answer addresses a specific key point."""
        return evaluate_scoring_point_static(predicted_answer, key_point, self.evaluator)

    def evaluate_easy_question(self, result: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate an easy question result."""
        return evaluate_easy_question_static(result, ground_truth, self.evaluator)

    def evaluate_hard_question(self, result: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a hard question result."""
        return evaluate_hard_question_static(result, ground_truth, self.evaluator)

    def filter_latest_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter results to keep only the latest for each (concept_id, question_id, difficulty) combination."""
        # Group results by (concept_id, question_id, difficulty)
        grouped = defaultdict(list)
        for result in results:
            key = (result["concept_id"], result["question_id"], result["difficulty"])
            grouped[key].append(result)

        # Keep only the last result for each group (assuming they are in chronological order)
        filtered_results = []
        for key, group in grouped.items():
            filtered_results.append(group[-1])  # Take the last (most recent) result

        return filtered_results

    def load_existing_evaluations(self, output_file: str) -> Dict[Tuple[str, int, str], Dict[str, Any]]:
        """Load existing evaluation results from output file if it exists."""
        existing_evaluations = {}

        if not Path(output_file).exists():
            logger.info("No existing evaluation file found, starting fresh")
            return existing_evaluations

        try:
            with open(output_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        evaluation = json.loads(line)
                        key = (evaluation["concept_id"], evaluation["question_id"], evaluation["difficulty"])
                        existing_evaluations[key] = evaluation

            logger.info(f"Loaded {len(existing_evaluations)} existing evaluations from {output_file}")
        except Exception as e:
            logger.error(f"Error loading existing evaluations from {output_file}: {e}")

        return existing_evaluations

    def save_evaluation_incrementally(self, evaluation: Dict[str, Any], output_file: str, file_lock: Lock):
        """Save a single evaluation result incrementally with thread safety."""
        try:
            # Ensure directory exists
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Thread-safe file writing
            with file_lock:
                with open(output_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(evaluation, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Error saving evaluation incrementally: {e}")

    def evaluate_results(self, input_file: str, output_file: str):
        """Main evaluation function with multiprocessing support."""
        logger.info(f"Loading results from {input_file}")

        # Load all results from JSONL file
        results = []
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        results.append(json.loads(line))
        except Exception as e:
            logger.error(f"Error loading input file {input_file}: {e}")
            return

        logger.info(f"Loaded {len(results)} results")

        # Filter to keep only latest results
        filtered_results = self.filter_latest_results(results)
        logger.info(f"After filtering, have {len(filtered_results)} unique results")

        # Load existing evaluations to support resume
        existing_evaluations = self.load_existing_evaluations(output_file)

        # Filter out already evaluated results
        remaining_results = []
        for result in filtered_results:
            key = (result["concept_id"], result["question_id"], result["difficulty"])
            if key not in existing_evaluations:
                remaining_results.append(result)

        logger.info(f"Found {len(existing_evaluations)} existing evaluations")
        logger.info(f"Remaining to evaluate: {len(remaining_results)} results")

        if not remaining_results:
            logger.info("All results have already been evaluated!")
            # Still calculate and display statistics from existing evaluations
            all_evaluations = list(existing_evaluations.values())
            self.calculate_final_statistics(all_evaluations)
            return

        # Initialize shared statistics
        manager = Manager()
        easy_stats = manager.dict(
            {"choice_acc": manager.list(), "freetext_acc": manager.list(), "scoring_point": manager.list()}
        )
        hard_stats = manager.dict(
            {
                "choice_acc": manager.list(),
                "freetext_acc": manager.list(),
                "scoring_point_long": manager.list(),
                "scoring_point_short": manager.list(),
            }
        )
        file_lock = manager.Lock()

        # Initialize stats from existing evaluations
        for evaluation in existing_evaluations.values():
            if evaluation["difficulty"] == "easy":
                easy_stats["choice_acc"].append(evaluation["choice_acc"])
                easy_stats["freetext_acc"].append(evaluation["freetext_acc"])
                easy_stats["scoring_point"].append(evaluation["scoring_point"])
            elif evaluation["difficulty"] == "hard":
                hard_stats["choice_acc"].append(evaluation["choice_acc"])
                hard_stats["freetext_acc"].append(evaluation["freetext_acc"])
                hard_stats["scoring_point_long"].append(evaluation["scoring_point_long"])
                hard_stats["scoring_point_short"].append(evaluation["scoring_point_short"])

        # Prepare arguments for multiprocessing
        args_list = [(result, self.concept_data, self.model_id) for result in remaining_results]

        # Use multiprocessing with 5 workers
        logger.info("Starting multiprocessing evaluation with 5 workers...")

        # Create progress tracking using mp.Value with explicit lock
        completed_count = mp.Value("i", 0)
        completed_lock = mp.Lock()
        total_count = len(remaining_results)

        def update_progress_and_save(result_tuple):
            """Callback function to handle completed evaluations."""
            evaluation, error = result_tuple

            if error:
                logger.warning(f"Evaluation error: {error}")
                return

            if evaluation is None:
                return

            # Update statistics
            if evaluation["difficulty"] == "easy":
                easy_stats["choice_acc"].append(evaluation["choice_acc"])
                easy_stats["freetext_acc"].append(evaluation["freetext_acc"])
                easy_stats["scoring_point"].append(evaluation["scoring_point"])
            elif evaluation["difficulty"] == "hard":
                hard_stats["choice_acc"].append(evaluation["choice_acc"])
                hard_stats["freetext_acc"].append(evaluation["freetext_acc"])
                hard_stats["scoring_point_long"].append(evaluation["scoring_point_long"])
                hard_stats["scoring_point_short"].append(evaluation["scoring_point_short"])

            # Save evaluation incrementally
            self.save_evaluation_incrementally(evaluation, output_file, file_lock)

            # Update progress
            with completed_lock:
                completed_count.value += 1
                current = completed_count.value

                # Print progress every 10 completions or at the end
                if current % 10 == 0 or current == total_count:
                    progress_pct = (current / total_count) * 100

                    # Calculate current stats
                    stats_msg = f"Progress: {current}/{total_count} ({progress_pct:.1f}%)"

                    if len(easy_stats["choice_acc"]) > 0:
                        s_ca = sum(easy_stats["choice_acc"]) / len(easy_stats["choice_acc"])
                        s_fa = sum(easy_stats["freetext_acc"]) / len(easy_stats["freetext_acc"])
                        s_sp = sum(easy_stats["scoring_point"]) / len(easy_stats["scoring_point"])
                        stats_msg += f" | Easy({len(easy_stats['choice_acc'])}): CA={s_ca:.3f} FA={s_fa:.3f} SP={s_sp:.3f}"

                    if len(hard_stats["choice_acc"]) > 0:
                        h_ca = sum(hard_stats["choice_acc"]) / len(hard_stats["choice_acc"])
                        h_fa = sum(hard_stats["freetext_acc"]) / len(hard_stats["freetext_acc"])
                        h_spl = sum(hard_stats["scoring_point_long"]) / len(hard_stats["scoring_point_long"])
                        h_sps = sum(hard_stats["scoring_point_short"]) / len(
                            hard_stats["scoring_point_short"]
                        )
                        stats_msg += f" | Hard({len(hard_stats['choice_acc'])}): CA={h_ca:.3f} FA={h_fa:.3f} SPL={h_spl:.3f} SPS={h_sps:.3f}"

                    logger.info(stats_msg)

        # Execute multiprocessing with better error handling
        def signal_handler(signum, frame):
            logger.info("Received interrupt signal, shutting down gracefully...")

        # Set up signal handler for graceful shutdown
        original_handler = signal.signal(signal.SIGINT, signal_handler)

        try:
            with mp.Pool(processes=2) as pool:
                # Submit all tasks
                results_async = [
                    pool.apply_async(evaluate_single_result, (args,), callback=update_progress_and_save)
                    for args in args_list
                ]

                # Wait for all tasks to complete with timeout to allow interruption
                for i, result_async in enumerate(results_async):
                    try:
                        result_async.get(timeout=300)  # 5 minute timeout per task
                    except mp.TimeoutError:
                        logger.warning(f"Task {i + 1} timed out after 5 minutes")
                    except KeyboardInterrupt:
                        logger.info("Keyboard interrupt received, terminating pool...")
                        pool.terminate()
                        pool.join()
                        raise
                    except Exception as e:
                        logger.warning(f"Task {i + 1} failed with error: {e}")

        except KeyboardInterrupt:
            logger.info("Evaluation interrupted by user")
            return
        except Exception as e:
            logger.error(f"Multiprocessing error: {e}")
            return
        finally:
            # Restore original signal handler
            signal.signal(signal.SIGINT, original_handler)

        logger.info(f"Evaluation completed! Results saved to {output_file}")

        # Calculate and display final statistics
        final_easy_stats = {
            "choice_acc": list(easy_stats["choice_acc"]),
            "freetext_acc": list(easy_stats["freetext_acc"]),
            "scoring_point": list(easy_stats["scoring_point"]),
        }
        final_hard_stats = {
            "choice_acc": list(hard_stats["choice_acc"]),
            "freetext_acc": list(hard_stats["freetext_acc"]),
            "scoring_point_long": list(hard_stats["scoring_point_long"]),
            "scoring_point_short": list(hard_stats["scoring_point_short"]),
        }

        self.calculate_statistics(final_easy_stats, final_hard_stats)

    def calculate_final_statistics(self, evaluations: List[Dict[str, Any]]):
        """Calculate final statistics from all evaluations."""
        easy_stats = {"choice_acc": [], "freetext_acc": [], "scoring_point": []}
        hard_stats = {
            "choice_acc": [],
            "freetext_acc": [],
            "scoring_point_long": [],
            "scoring_point_short": [],
        }

        for evaluation in evaluations:
            if evaluation["difficulty"] == "easy":
                easy_stats["choice_acc"].append(evaluation["choice_acc"])
                easy_stats["freetext_acc"].append(evaluation["freetext_acc"])
                easy_stats["scoring_point"].append(evaluation["scoring_point"])
            elif evaluation["difficulty"] == "hard":
                hard_stats["choice_acc"].append(evaluation["choice_acc"])
                hard_stats["freetext_acc"].append(evaluation["freetext_acc"])
                hard_stats["scoring_point_long"].append(evaluation["scoring_point_long"])
                hard_stats["scoring_point_short"].append(evaluation["scoring_point_short"])

        self.calculate_statistics(easy_stats, hard_stats)

    def calculate_statistics(self, easy_stats: Dict[str, List[int]], hard_stats: Dict[str, List[int]]):
        """Calculate and display aggregated statistics."""

        # Calculate averages
        logger.info("=== EVALUATION STATISTICS ===")

        if easy_stats["choice_acc"]:
            easy_choice_avg = sum(easy_stats["choice_acc"]) / len(easy_stats["choice_acc"])
            easy_freetext_avg = sum(easy_stats["freetext_acc"]) / len(easy_stats["freetext_acc"])
            easy_scoring_avg = sum(easy_stats["scoring_point"]) / len(easy_stats["scoring_point"])

            logger.info(
                f"Easy (n={len(easy_stats['choice_acc'])}): CA={easy_choice_avg:.3f} FA={easy_freetext_avg:.3f} SP={easy_scoring_avg:.3f}"
            )
        else:
            logger.info("Easy: No data")

        if hard_stats["choice_acc"]:
            hard_choice_avg = sum(hard_stats["choice_acc"]) / len(hard_stats["choice_acc"])
            hard_freetext_avg = sum(hard_stats["freetext_acc"]) / len(hard_stats["freetext_acc"])
            hard_scoring_long_avg = sum(hard_stats["scoring_point_long"]) / len(
                hard_stats["scoring_point_long"]
            )
            hard_scoring_short_avg = sum(hard_stats["scoring_point_short"]) / len(
                hard_stats["scoring_point_short"]
            )

            logger.info(
                f"Hard (n={len(hard_stats['choice_acc'])}): CA={hard_choice_avg:.3f} FA={hard_freetext_avg:.3f} SPL={hard_scoring_long_avg:.3f} SPS={hard_scoring_short_avg:.3f}"
            )
        else:
            logger.info("Hard: No data")

        if easy_stats["choice_acc"] and hard_stats["choice_acc"]:
            logger.info(
                f"{easy_choice_avg * 100:.2f} & {easy_freetext_avg * 100:.2f} & {easy_scoring_avg * 100:.2f} & {hard_choice_avg * 100:.2f} & {hard_freetext_avg * 100:.2f} & {hard_scoring_long_avg * 100:.2f} & {hard_scoring_short_avg * 100:.2f}"
            )


def main():
    parser = argparse.ArgumentParser(description="Evaluate concept-based Q&A results")
    parser.add_argument("input_file", help="Input JSONL file with results")
    parser.add_argument("output_file", help="Output JSONL file for evaluations")
    parser.add_argument("--model", default="Qwen/Qwen2.5-72B-Instruct", help="Model ID for LLM evaluation")

    args = parser.parse_args()

    # Setup logger
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    )
    # save log to log/{timestamp}.log
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.add(f"log/{timestamp}.log")

    # Create evaluator and run evaluation
    evaluator = ConceptEvaluator(model_id=args.model)
    evaluator.evaluate_results(args.input_file, args.output_file)


if __name__ == "__main__":
    main()
