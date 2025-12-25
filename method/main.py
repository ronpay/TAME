import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List

import colorama
import icecream
from colorama import Fore, Style
from loguru import logger

from method.qa import QASystem
from method.TAME import TAME, get_model_id, get_model_short_name


def setup_logger():
    colorama.init(autoreset=True)
    # Create logs directory if it doesn't exist
    os.makedirs("log", exist_ok=True)
    # Remove default handler
    logger.remove()
    # Add console handler for INFO level and above
    logger.add(
        sys.stdout,
        level="INFO",
    )

    # Add file handler for DEBUG level and above
    current_time = datetime.now().strftime("%m%d_%H%M%S")
    logger.add(
        f"log/{current_time}.log",
        level="DEBUG",
        encoding="utf-8",
    )

    logger.info("Logger setup completed")


def match_options_answer_to_choice(options_answer: str, options: List[str]) -> str:
    """
    Match the options_answer string to the corresponding choice letter (A, B, C, D).

    Args:
        options_answer: The correct answer as a string
        options: List of 4 options

    Returns:
        str: The corresponding choice letter (A, B, C, or D)
    """
    if not options_answer or not options or len(options) != 4:
        return "Unknown"

    # Try to find exact match first
    for i, option in enumerate(options):
        if option.strip() == options_answer.strip():
            return chr(65 + i)  # Convert to A, B, C, D

    # Try to find partial match (case insensitive)
    options_answer_lower = options_answer.lower().strip()
    for i, option in enumerate(options):
        if options_answer_lower in option.lower().strip() or option.lower().strip() in options_answer_lower:
            return chr(65 + i)  # Convert to A, B, C, D

    logger.warning(f"Could not match options_answer '{options_answer}' to any option in {options}")
    return "Unknown"


def load_existing_question_ids(results_file: Path) -> set:
    """
    Load existing question composite keys from the results file to avoid duplicate processing.
    Uses a combination of concept_id, question_id, and difficulty for accurate matching.

    Args:
        results_file: Path to the JSONL results file

    Returns:
        set: Set of composite keys (concept_id, question_id, difficulty) that have already been processed
    """
    existing_keys = set()

    if not results_file.exists():
        logger.info(f"Results file {results_file} does not exist, starting fresh")
        return existing_keys

    try:
        with open(results_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                    concept_id = entry.get("concept_id", "unknown")
                    question_id = entry.get("question_id")
                    difficulty = entry.get("difficulty", "unknown")

                    if question_id:
                        # Create composite key for more accurate matching
                        composite_key = (concept_id, question_id, difficulty)
                        existing_keys.add(composite_key)
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON on line {line_num} in {results_file}: {e}")
                    continue

        logger.info(f"Loaded {len(existing_keys)} existing question composite keys from {results_file}")

    except Exception as e:
        logger.error(f"Error reading existing results file {results_file}: {e}")

    return existing_keys


def build_memory(model_arg: str):
    """Build memory by reading history for all concepts"""
    setup_logger()

    model_id = get_model_id(model_arg)
    model_short_name = get_model_short_name(model_id)

    logger.info(f"Building memory using model: {model_id} ({model_short_name})")

    assistant = TAME(model_id=model_id)

    logger.info("Reading history for all concepts...")
    assistant.read_history_all()

    logger.info(f"Memory building completed for model: {model_short_name}")


def run_qa(model_arg: str):
    """Run QA system to answer questions"""
    setup_logger()

    model_id = get_model_id(model_arg)
    model_short_name = get_model_short_name(model_id)

    logger.info(f"Starting QA system with model: {model_id} ({model_short_name})")

    assistant = TAME(model_id=model_id)

    logger.info("Starting QA System")
    qa_system = QASystem(model_id=model_id)

    # Create results directory if it doesn't exist
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    results_file = results_dir / f"all_results_{model_short_name}.jsonl"

    # Load existing question IDs to avoid duplicates
    existing_question_ids = load_existing_question_ids(results_file)
    skipped_count = 0
    processed_count = 0

    for q in qa_system:
        # Get question info first to create composite key
        question_id = q["qid"]
        difficulty = q.get("difficulty", "unknown")

        # Get the original concept_id from the question data (from file path)
        original_concept_id = q.get("concept_id", "unknown")

        # Get options and options_answer if they exist in the question data
        options = q.get("options", None)
        options_answer = q.get("options_answer", None)

        # Create composite key for duplicate checking using original concept_id
        composite_key = (original_concept_id, question_id, difficulty)

        # Check if this question has already been processed
        if composite_key in existing_question_ids:
            skipped_count += 1
            logger.info(
                f"{Fore.YELLOW}Skipping{Style.RESET_ALL}: {question_id} (concept: {original_concept_id}, difficulty: {difficulty}) - already processed"
            )
            continue

        processed_count += 1

        # Log the question
        logger.info(f"{Fore.BLUE}Question{Style.RESET_ALL}: {q['qid']} {q['question']}")

        # Run the complete workflow - this will identify concept_id for answering but we won't use it for storage
        identified_concept_id, answer, choice_answer = assistant.complete_qa_workflow(
            q["img_path"], q["question"], options, options_answer, original_concept_id
        )

        # Log both concept IDs for comparison
        if identified_concept_id != original_concept_id:
            logger.info(
                f"{Fore.CYAN}Concept Mismatch{Style.RESET_ALL}: Original={original_concept_id}, Identified={identified_concept_id}"
            )

        logger.info(f"{Fore.BLUE}Answer{Style.RESET_ALL}: {answer}")
        if choice_answer:
            logger.info(f"{Fore.BLUE}Choice Answer{Style.RESET_ALL}: {choice_answer}")

        # Prepare result entry using ORIGINAL concept_id for storage
        result_entry = {
            "concept_id": original_concept_id,  # Use original concept_id from file path
            "question_id": q["qid"],
            "difficulty": difficulty,
            "question": q["question"],
            "answer": answer,
            "choice": choice_answer if choice_answer else None,
        }

        # Append to JSONL file
        with open(results_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(result_entry, ensure_ascii=False) + "\n")

        logger.info(f"{Fore.MAGENTA}Result saved to {results_file}{Style.RESET_ALL}")

    # Final statistics
    logger.info(f"\n{Fore.CYAN}=== PROCESSING SUMMARY ==={Style.RESET_ALL}")
    logger.info(f"{Fore.CYAN}Questions Processed: {processed_count}{Style.RESET_ALL}")
    logger.info(f"{Fore.CYAN}Questions Skipped: {skipped_count}{Style.RESET_ALL}")
    logger.info(f"{Fore.CYAN}Total Questions: {processed_count + skipped_count}{Style.RESET_ALL}")

    logger.info(f"\n{Fore.GREEN}All results saved to: {results_file}{Style.RESET_ALL}")


def main():
    parser = argparse.ArgumentParser(description="TAME: Double Memory Personalized MLLM System")
    parser.add_argument(
        "mode", choices=["build", "qa"], help="Mode: 'build' for memory building, 'qa' for question answering"
    )
    parser.add_argument(
        "--model", "-m", default="qwenvl", help="Model to use: 'qwenvl' or 'internvl' (default: qwenvl)"
    )

    args = parser.parse_args()

    if args.mode == "build":
        build_memory(args.model)
    elif args.mode == "qa":
        run_qa(args.model)


if __name__ == "__main__":
    icecream.install()
    main()
