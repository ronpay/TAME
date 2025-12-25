from pathlib import Path

import yaml
from gen_image_utils import ImageGenerator
from loguru import logger
from PIL import Image


class PromptImageGenerator:
    def __init__(self, concept_id: str, concept_type: str = "pet"):
        self.concept_id = concept_id
        self.concept_type = concept_type
        self.concept_dir = Path(f"dataset_maker/{concept_type}") / concept_id
        self.img_dir = self.concept_dir / "img"
        self.img_dir.mkdir(parents=True, exist_ok=True)

        # Load base image
        # Try to find base image with different extensions
        base_extensions = [".png", ".jpg", ".jpeg"]
        self.base_img_path = None
        for ext in base_extensions:
            potential_path = self.img_dir / f"base{ext}"
            if potential_path.exists():
                self.base_img_path = potential_path
                break

        if self.base_img_path is None:
            # If no base image found, default to base.png for error message
            self.base_img_path = self.img_dir / "base.png"
        if not self.base_img_path.exists():
            raise FileNotFoundError(f"Base image not found: {self.base_img_path}")

        self.base_img = Image.open(self.base_img_path).convert("RGB")

        # Initialize image generator
        self.image_generator = ImageGenerator("gpt-image-1")

    def load_yaml_file(self, filename: str):
        """Load YAML file and return its content"""
        file_path = self.concept_dir / filename
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def extract_image_prompts_from_history(self, history_data):
        """Extract image prompts from history.yaml"""
        prompts = []
        if not history_data:
            return prompts

        for entry in history_data:
            if "image_prompt" in entry and entry["image_prompt"] is not None:
                prompts.append(
                    {"image_id": entry.get("image_id"), "prompt": entry["image_prompt"], "source": "history"}
                )
        return prompts

    def extract_image_prompts_from_profile(self, profile_data):
        """Extract image prompts from profile.yaml - only if it has image_prompt field"""
        prompts = []
        # Profile.yaml doesn't have image_prompt fields, so return empty
        return prompts

    def extract_image_prompts_from_questions(self, questions_data):
        """Extract image prompts from question.yaml"""
        prompts = []
        if not questions_data:
            return prompts

        for question in questions_data:
            if "image_prompt" in question and question["image_prompt"] is not None:
                prompts.append(
                    {
                        "image_id": question.get("image_id"),
                        "prompt": question["image_prompt"],
                        "source": "questions",
                    }
                )
        return prompts

    def generate_image_for_prompt(self, prompt_data, force=False):
        """Generate image for a single prompt"""
        image_id = prompt_data["image_id"]
        prompt = prompt_data["prompt"]
        source = prompt_data["source"]

        if not image_id:
            logger.warning(f"Skipping prompt without image_id: {prompt}")
            return

        # Check if image already exists
        output_path = self.img_dir / f"{image_id}.png"
        if output_path.exists() and not force:
            logger.info(f"Image already exists, skipping: {output_path}")
            return

        logger.info(f"Generating image for {image_id} from {source}: {prompt}")

        try:
            # Use simple attributes based on concept
            attributes = f"A {self.concept_id} {self.concept_type} as shown in the reference image"

            generated_image = self.image_generator.generate_image(self.base_img, attributes, prompt, [])

            # Save the generated image
            generated_image.save(output_path, "PNG")

            logger.info(f"Successfully generated and saved: {output_path}")

        except Exception as e:
            logger.error(f"Failed to generate image for {image_id}: {str(e)}")

    def generate_all_images(self, force=False):
        """Generate images for all prompts in all YAML files

        Args:
            force (bool): If True, regenerate images even if they already exist
        """
        logger.info(f"Starting image generation for concept: {self.concept_id}")

        # Load all YAML files
        history_data = self.load_yaml_file("history.yaml")
        profile_data = self.load_yaml_file("profile.yaml")
        easy_questions_data = self.load_yaml_file("easy_question.yaml")
        hard_questions_data = self.load_yaml_file("hard_question.yaml")

        # Extract prompts from all sources
        all_prompts = []

        if history_data:
            history_prompts = self.extract_image_prompts_from_history(history_data)
            all_prompts.extend(history_prompts)
            logger.info(f"Found {len(history_prompts)} prompts in history.yaml")

        if profile_data:
            profile_prompts = self.extract_image_prompts_from_profile(profile_data)
            all_prompts.extend(profile_prompts)
            logger.info(f"Found {len(profile_prompts)} prompts in profile.yaml")

        if easy_questions_data:
            easy_question_prompts = self.extract_image_prompts_from_questions(easy_questions_data)
            all_prompts.extend(easy_question_prompts)
            logger.info(f"Found {len(easy_question_prompts)} prompts in easy_question.yaml")

        if hard_questions_data:
            hard_question_prompts = self.extract_image_prompts_from_questions(hard_questions_data)
            all_prompts.extend(hard_question_prompts)
            logger.info(f"Found {len(hard_question_prompts)} prompts in hard_question.yaml")

        logger.info(f"Total prompts to process: {len(all_prompts)}")

        # Count existing images
        existing_count = 0
        for prompt_data in all_prompts:
            if prompt_data["image_id"]:
                output_path = self.img_dir / f"{prompt_data['image_id']}.png"
                if output_path.exists():
                    existing_count += 1

        if existing_count > 0:
            if force:
                logger.info(f"Found {existing_count} existing images, will regenerate due to force=True")
            else:
                logger.info(f"Found {existing_count} existing images, will skip them")

        # Generate images for all prompts
        generated_count = 0
        skipped_count = 0

        for i, prompt_data in enumerate(all_prompts, 1):
            logger.info(f"Processing prompt {i}/{len(all_prompts)}")

            # Check if would be skipped
            image_id = prompt_data["image_id"]
            if image_id:
                output_path = self.img_dir / f"{image_id}.png"
                if output_path.exists() and not force:
                    skipped_count += 1
                else:
                    generated_count += 1

            self.generate_image_for_prompt(prompt_data, force)

        logger.info(f"Image generation completed! Generated: {generated_count}, Skipped: {skipped_count}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate images for concept prompts")
    parser.add_argument("--concept_id", default="dog_1", help="Concept ID to generate images for")
    parser.add_argument(
        "--concept_type",
        default="pet",
        choices=["pet", "person", "object"],
        help="Type of concept: pet, person, or object",
    )
    parser.add_argument("--force", action="store_true", help="Regenerate images even if they already exist")
    args = parser.parse_args()

    try:
        generator = PromptImageGenerator(args.concept_id, args.concept_type)
        generator.generate_all_images(force=args.force)

    except Exception as e:
        logger.error(f"Error during image generation: {str(e)}")
        raise e
