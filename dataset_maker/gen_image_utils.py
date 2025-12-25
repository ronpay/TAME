import base64
import io
import random
import re
from pathlib import Path
from typing import List

import requests
import yaml
from loguru import logger
from openai import OpenAI
from PIL import Image
from pydantic import BaseModel


class ImageGenerator:
    def __init__(self, model_name: str):
        self.client = OpenAI()
        self.model_name = model_name
        self.prompt = """
Generate an image of this person/pet/object using the quality and style of mobile phone photography that
matches the attributes from the person/pet/object in the reference image.

The content of the image should be:
{content_requirement}

Ensure the background is diverse and varied—reflecting the content requirements with multiple complementary settings (e.g., indoor, outdoor, playful, serene)—while keeping the object as the focal point.

Guidelines:
+ Use vivid, concrete details.
+ Keep composition balanced and focused on the object.
+ Incorporate a variety of backgrounds that align with the specified content requirements.
+ Do not repeat any phrase from the "previous captions" list.
"""

    def generate_image(
        self, base_img: Image.Image, attributes: str, content_requirement: str, previous_captions: List[str]
    ):
        prompt = self.prompt.format(
            content_requirement=content_requirement,
        )

        # Convert PIL Image to bytes for API
        img_byte_arr = io.BytesIO()
        base_img.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)

        result = self.client.images.edit(
            model=self.model_name,
            image=img_byte_arr,
            prompt=prompt,
            n=1,
            size="1024x1024",
        )

        # Decode the base64 image data
        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        # Convert to PIL Image
        logger.debug("Converting base64 image data to PIL Image")
        try:
            image_data_io = io.BytesIO(image_bytes)
            image = Image.open(image_data_io).convert("RGB")
        except Exception as e:
            logger.error(f"Failed to process image data: {str(e)}")
            raise e

        return image
