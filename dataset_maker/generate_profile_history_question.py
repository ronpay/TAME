#!/usr/bin/env python3
"""
Workflow script to generate profile, history, and questions for a given concept_id.
Usage: python generate_profile_history_question.py <concept_id>
Example: python generate_profile_history_question.py hamster_1
"""

import argparse
import os
import re
import sys
from collections import OrderedDict
from pathlib import Path

import yaml
from PIL import Image

from dataset_maker.utils.llm_utils import APIModel

# Use OrderedDict for preserving YAML order
yaml.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    lambda loader, node: OrderedDict(loader.construct_pairs(node)),
)


class DatasetWorkflow:
    def __init__(self, concept_id: str, model_id: str = "gemini-2.5-pro", concept_type: str = "pet"):
        self.concept_id = concept_id
        self.model_id = model_id
        self.concept_type = concept_type
        self.concept_dir = Path(f"dataset_maker/concept_{concept_type}/{concept_id}")
        self.prompt_dir = Path(f"dataset_maker/prompt/{concept_type}")

        # Initialize the model
        self.model = APIModel(model_id)

        # Ensure concept directory exists
        self.concept_dir.mkdir(parents=True, exist_ok=True)

    def load_base_image(self) -> Image.Image:
        """Load the base image for the concept"""
        # Try both .png and .jpg extensions
        for ext in [".png", ".jpg", ".jpeg"]:
            image_path = self.concept_dir / "img" / f"base{ext}"
            if image_path.exists():
                return Image.open(image_path)

        raise FileNotFoundError(f"No base image found for concept {self.concept_id}")

    def load_prompt(self, prompt_name: str) -> str:
        """Load a prompt file"""
        prompt_path = self.prompt_dir / f"{prompt_name}.md"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def extract_yaml_from_response(self, response: str) -> str:
        """Extract YAML content from the model response"""
        # Look for YAML code blocks
        yaml_pattern = r"```ya?ml\s*\n(.*?)\n```"
        match = re.search(yaml_pattern, response, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1)

        # If no code block found, try to find YAML-like content
        lines = response.split("\n")
        yaml_lines = []
        in_yaml = False

        for line in lines:
            if (
                line.strip().startswith("concept_id:")
                or line.strip().startswith("- turn:")
                or line.strip().startswith("- id:")
            ):
                in_yaml = True

            if in_yaml:
                yaml_lines.append(line)

        if yaml_lines:
            return "\n".join(yaml_lines)

        return response

    def load_existing_profile(self) -> str:
        """Load existing profile.yaml as raw string"""
        profile_path = self.concept_dir / "profile.yaml"
        if profile_path.exists():
            with open(profile_path, "r", encoding="utf-8") as f:
                return f.read()
        return None

    def load_existing_yaml_file(self, filename: str) -> OrderedDict:
        """Load existing YAML file with preserved order"""
        file_path = self.concept_dir / filename
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return None

    def step1_generate_profile(self) -> str:
        """Step 1: Generate profile using base image"""
        profile_path = self.concept_dir / "profile.yaml"

        # Check if profile already exists
        existing_profile = self.load_existing_profile()
        if existing_profile:
            print(f"Profile already exists at {profile_path}, loading existing file...")
            return existing_profile

        print(f"Step 1: Generating profile for {self.concept_id}...")

        # Load the base image
        base_image = self.load_base_image()

        # Load the profile generation prompt
        prompt = self.load_prompt("profile_generation")

        # Format the prompt - it doesn't need any substitutions, just use as is
        formatted_prompt = prompt

        # Generate the profile
        response = self.model.chat_img(formatted_prompt, base_image, max_tokens=4096)

        # Extract and parse YAML
        yaml_content = self.extract_yaml_from_response(response)

        try:
            profile = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML: {e}")
            print(f"Raw response: {response}")
            raise

        # Save the raw YAML content directly to profile.yaml
        with open(profile_path, "w", encoding="utf-8") as f:
            f.write(yaml_content)
        # Comment: The raw YAML content is saved directly without parsing or formatting

        print(f"Profile saved to {profile_path}")
        return yaml_content

    def step2_generate_history(self, profile: str) -> OrderedDict:
        """Step 2: Generate history using profile (no image)"""
        history_path = self.concept_dir / "history.yaml"

        # Check if history already exists
        existing_history = self.load_existing_yaml_file("history.yaml")
        if existing_history:
            print(f"History already exists at {history_path}, loading existing file...")
            return existing_history

        print(f"Step 2: Generating history for {self.concept_id}...")

        # Load the history prompt
        prompt_template = self.load_prompt("history_prompt")

        # Format the prompt with profile
        formatted_prompt = prompt_template.replace("{profile}", profile)

        # Generate the history
        response = self.model.chat_text(formatted_prompt, max_tokens=4096)

        # Extract and parse YAML
        yaml_content = self.extract_yaml_from_response(response)

        try:
            history = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML: {e}")
            print(f"Raw response: {response}")
            raise

        # Save history with preserved order
        with open(history_path, "w", encoding="utf-8") as f:
            yaml.dump(history, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        print(f"History saved to {history_path}")
        return history

    def step3_generate_easy_questions(self, profile: str, history: OrderedDict) -> OrderedDict:
        """Step 3: Generate easy questions using profile and history"""
        easy_questions_path = self.concept_dir / "easy_question.yaml"

        # Check if easy questions already exist
        existing_easy_questions = self.load_existing_yaml_file("easy_question.yaml")
        if existing_easy_questions:
            print(f"Easy questions already exist at {easy_questions_path}, loading existing file...")
            return existing_easy_questions

        print(f"Step 3: Generating easy questions for {self.concept_id}...")

        # Load the easy questions prompt
        prompt_template = self.load_prompt("easy_question_generation")

        # Format the prompt with profile and history
        profile_yaml = profile
        history_yaml = yaml.dump(history, default_flow_style=False, allow_unicode=True, sort_keys=False)

        formatted_prompt = prompt_template.replace("{profile}", profile_yaml).replace(
            "{history}", history_yaml
        )

        # Generate the easy questions
        response = self.model.chat_text(formatted_prompt, max_tokens=4096)

        # Extract and parse YAML
        yaml_content = self.extract_yaml_from_response(response)

        try:
            easy_questions = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML: {e}")
            print(f"Raw response: {response}")
            raise

        # Save easy questions with preserved order
        with open(easy_questions_path, "w", encoding="utf-8") as f:
            yaml.dump(easy_questions, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        print(f"Easy questions saved to {easy_questions_path}")
        return easy_questions

    def step4_generate_hard_questions(self, profile: str, history: OrderedDict) -> OrderedDict:
        """Step 4: Generate hard questions using profile and history"""
        hard_questions_path = self.concept_dir / "hard_question.yaml"

        # Check if hard questions already exist
        existing_hard_questions = self.load_existing_yaml_file("hard_question.yaml")
        if existing_hard_questions:
            print(
                f"Hard questions already exist at {hard_questions_path}, loading existing file..."
            )
            return existing_hard_questions

        print(f"Step 4: Generating hard questions for {self.concept_id}...")

        # Load the hard questions prompt
        prompt_template = self.load_prompt("hard_question_generation")

        # Format the prompt with profile and history
        profile_yaml = profile
        history_yaml = yaml.dump(history, default_flow_style=False, allow_unicode=True, sort_keys=False)

        formatted_prompt = prompt_template.replace("{profile}", profile_yaml).replace(
            "{history}", history_yaml
        )

        # Generate the hard questions
        response = self.model.chat_text(formatted_prompt, max_tokens=4096)

        # Extract and parse YAML
        yaml_content = self.extract_yaml_from_response(response)

        try:
            hard_questions = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML: {e}")
            print(f"Raw response: {response}")
            raise

        # Save hard questions with preserved order
        with open(hard_questions_path, "w", encoding="utf-8") as f:
            yaml.dump(hard_questions, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        print(f"Hard questions saved to {hard_questions_path}")
        return hard_questions

    def run_workflow(self):
        """Run the complete workflow"""
        print(f"Starting workflow for concept: {self.concept_id}")
        print(f"Using model: {self.model_id}")

        try:
            # Step 1: Generate profile (or load existing)
            profile = self.step1_generate_profile()

            # Step 2: Generate history (or load existing)
            history = self.step2_generate_history(profile)

            # Step 3: Generate easy questions (or load existing)
            easy_questions = self.step3_generate_easy_questions(profile, history)

            # Step 4: Generate hard questions (or load existing)
            hard_questions = self.step4_generate_hard_questions(profile, history)

            print(f"\nWorkflow completed successfully!")
            print(f"All files saved to: {self.concept_dir}")

        except Exception as e:
            print(f"Error in workflow: {e}")
            raise


def main():
    parser = argparse.ArgumentParser(description="Generate profile, history, and questions for a concept")
    parser.add_argument("concept_id", help="Concept ID (e.g., hamster_1)")
    parser.add_argument(
        "--model",
        default="gemini-2.5-pro",
        help="Model ID to use (default: gemini-2.5-pro)",
    )
    parser.add_argument(
        "--type",
        dest="concept_type",
        default="pet",
        choices=["pet", "object", "person"],
        help="Concept type (default: pet). Available types: pet, object, person",
    )

    args = parser.parse_args()

    # Create and run the workflow
    workflow = DatasetWorkflow(args.concept_id, args.model, args.concept_type)
    workflow.run_workflow()


if __name__ == "__main__":
    main()
