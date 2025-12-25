import base64
import json
import os
import random
import re
import time
from io import BytesIO
from typing import Optional

import dotenv
import requests
from icecream import ic
from loguru import logger
from PIL import Image

# from .base_model import BaseModel


class APIModel:
    def __init__(self, model_id: str, params={}):
        """
        Initialize APIModel with model_id and API key.

        Args:
            model_id: Model identifier
        """
        super().__init__()
        dotenv.load_dotenv()
        self.model_id = model_id
        self.api_key = os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("API_KEY environment variable is not set")

        self.api_base = os.getenv("API_URL")
        self.params = params

    def get_headers(self):
        # split self.api_key by ',', and convert to list
        api_keys = self.api_key.split(",")
        # convert to list of dict
        # random one for api_key
        api_key = random.choice(api_keys)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        return headers

    @staticmethod
    def model_list():
        return ["gemini-2.5-pro"]

    def _encode_image(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string."""
        image = image.convert("RGB")
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def chat_img(self, prompt: str, image: Image.Image, max_tokens: int = 2048) -> str:
        return self.chat_multi_img(prompt, [image], max_tokens)

    def chat_text(self, prompt: str, max_tokens: int = 2048) -> str:
        return self.chat_multi_img(prompt, [], max_tokens)

    def chat_multi_img(
        self, prompt: str, images: list[Image.Image], max_tokens: int = 2048, stream: bool = True
    ) -> str:
        """
        Generate text response for the given prompt and multiple images using OpenAI API.

        Args:
            prompt: Text prompt to process
            images: List of images to analyze (list of PIL Image objects)
            max_tokens: Maximum number of tokens to generate
            stream: Whether to use streaming mode (default: True)

        Returns:
            str: Generated text response
        """
        content = [{"type": "text", "text": prompt}]

        # Add each image to the content list
        for image in images:
            base64_image = self._encode_image(image)
            image_content = {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
            }
            content.append(image_content)

        payload = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": content}],
            "stream": stream,
        }
        # merge payload with params
        payload.update(self.params)

        # Try up to 3 times with 30 second sleep on 429 errors
        max_retries = 8
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.api_base}/chat/completions",
                    headers=self.get_headers(),
                    json=payload,
                    stream=stream,
                )

                # If we get a 429 Too Many Requests error and have attempts left, sleep and retry
                if response.status_code == 429 and attempt < max_retries - 1:
                    retry_delay = 30 * (2**attempt)  # 30s, 60s, 120ss
                    logger.warning(
                        f"Rate limit (429) hit. Retrying after {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(retry_delay)
                    continue

                response.raise_for_status()

                if stream:
                    # Handle streaming response
                    full_response = ""
                    for line in response.iter_lines():
                        if line:
                            line = line.decode("utf-8")
                            if line.startswith("data: "):
                                data = line[6:]  # Remove 'data: ' prefix
                                if data == "[DONE]":
                                    break
                                try:
                                    chunk = json.loads(data)
                                    if "choices" in chunk and len(chunk["choices"]) > 0:
                                        delta = chunk["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            full_response += delta["content"]
                                except json.JSONDecodeError:
                                    continue

                    logger.debug(
                        f"API request {payload['messages'][0]['content'][0]}\n Response: {full_response}"
                    )
                    return full_response.strip()
                else:
                    # Handle non-streaming response
                    result = response.json()
                    logger.debug(f"API request {payload['messages'][0]['content'][0]}\n Response: {result}")
                    return result["choices"][0]["message"]["content"].strip()

            except requests.exceptions.RequestException as e:
                # If this is our last attempt, raise the exception
                logger.warning(f"API request failed: {str(e)}")
                time.sleep(30)
                if attempt == max_retries - 1:
                    raise Exception(f"API request failed after {max_retries} attempts: {str(e)}")
