import base64
from io import BytesIO, text_encoding

import einops
import requests
import torch
from icecream import ic
from loguru import logger
from PIL import Image
from qwen_vl_utils import process_vision_info
from transformers import (
    AutoModel,
    AutoModelForCausalLM,
    AutoProcessor,
    AutoTokenizer,
    Qwen2_5_VLForConditionalGeneration,
)

from .base_model import BaseModel


def resize_image(image: Image.Image, max_size=640):
    """
    Resize an image while maintaining its aspect ratio, ensuring the longest side is max_size pixels.

    Args:
        image (PIL.Image.Image): The image to resize
        max_size (int): Maximum length of the longest dimension

    Returns:
        PIL.Image.Image: Resized image
    """
    # Get current dimensions
    width, height = image.size

    # Calculate the scaling factor
    if width >= height:
        # Width is the longest dimension
        scaling_factor = max_size / width
    else:
        # Height is the longest dimension
        scaling_factor = max_size / height

    # Calculate new dimensions
    new_width = int(width * scaling_factor)
    new_height = int(height * scaling_factor)

    # Resize the image
    return image.resize((new_width, new_height), Image.LANCZOS)


def pil_image_to_base64(image, image_format="PNG"):
    """
    Convert a PIL.Image.Image object to a Base64 string.

    Args:
        image (PIL.Image.Image): The image to be converted.
        image_format (str): Format to save the image, e.g., "PNG", "JPEG".

    Returns:
        str: The Base64-encoded string of the image.
    """
    # resize image
    image = resize_image(image)
    # Create a BytesIO object
    buffer = BytesIO()

    # Save the image to the buffer in the specified format
    image.save(buffer, format=image_format)

    # Ensure the pointer is at the beginning of the buffer
    buffer.seek(0)

    # Get the binary content of the image and encode it as Base64
    image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # Close the buffer
    buffer.close()

    return image_base64


class QwenVLModel(BaseModel):
    def __init__(self, model_id="Qwen/Qwen2.5-VL-7B-Instruct", params={}):
        super().__init__()
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            model_id,
            torch_dtype="auto",
            # torch_dtype=torch.float16,
            device_map="cuda",
            attn_implementation="flash_attention_2",
            low_cpu_mem_usage=True,
        )
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.params = params if params else {}

        self.one_id = self.tokenizer.convert_tokens_to_ids("1")
        self.zero_id = self.tokenizer.convert_tokens_to_ids("0")

        self.harmful_id = self.tokenizer.convert_tokens_to_ids("Ġharmful")
        self.harmless_id = self.tokenizer.convert_tokens_to_ids("Ġharmless")

    @staticmethod
    def model_list():
        return ["Qwen/Qwen2.5-VL-7B-Instruct"]

    def chat_text(self, prompt: str, max_tokens: int = 512) -> str:
        conversation = [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ]
        text_prompt = self.processor.apply_chat_template(conversation, add_generation_prompt=True)
        inputs = self.processor(text=[text_prompt], padding=True, return_tensors="pt").to(self.model.device)
        output_ids = self.model.generate(**inputs, max_new_tokens=max_tokens, **self.params)
        generated_ids = [output_ids[len(inputs.input_ids[i]) :] for i in range(len(output_ids))]
        output_text = self.processor.batch_decode(
            generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True
        )
        logger.debug(output_text)
        return output_text[0]

    def chat_img(self, prompt: str, image: Image.Image, max_tokens: int = 512) -> str:
        image = resize_image(image)
        conversation = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": prompt},
                ],
            }
        ]

        text_prompt = self.processor.apply_chat_template(conversation, add_generation_prompt=True)

        inputs = self.processor(text=[text_prompt], images=[image], padding=True, return_tensors="pt").to(
            self.model.device
        )

        output_ids = self.model.generate(**inputs, max_new_tokens=max_tokens, **self.params)

        generated_ids = [
            output_ids[len(input_ids) :]
            for input_ids, output_ids in zip(inputs.input_ids.repeat(output_ids.shape[0], 1), output_ids)
        ]
        output_text = self.processor.batch_decode(
            generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True
        )
        logger.debug(output_text)

        return output_text[0]

    def chat_img_batch(
        self, prompts: list[str], images: list[Image.Image], max_tokens: int = 256
    ) -> list[str]:
        conversations = [
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "image"},
                        {"type": "text", "text": prompt},
                    ],
                }
            ]
            for prompt in prompts
        ]

        text_prompts = [
            self.processor.apply_chat_template(conversation, add_generation_prompt=True)
            for conversation in conversations
        ]

        inputs = self.processor(text=text_prompts, images=images, padding=True, return_tensors="pt").to(
            self.model.device
        )

        output_ids = self.model.generate(**inputs, max_new_tokens=max_tokens, **self.params)

        generated_ids = [output_ids[i][len(inputs.input_ids[i]) :] for i in range(len(output_ids))]
        output_text = self.processor.batch_decode(
            generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True
        )
        logger.debug(output_text)

        return output_text

    def chat_multi_img(self, prompt: str, images: list[Image.Image]) -> str:
        conversation = [
            {
                "role": "user",
                "content": [],
            }
        ]
        for i in range(len(images)):
            conversation[0]["content"].append(
                {"type": "image", "image": f"data:image;base64,{pil_image_to_base64(images[i])}"}
            )
        conversation[0]["content"].append({"type": "text", "text": prompt})
        text_prompt = self.processor.apply_chat_template(
            conversation, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs = process_vision_info(conversation)
        inputs = self.processor(
            text=[text_prompt], images=image_inputs, videos=video_inputs, padding=True, return_tensors="pt"
        ).to(self.model.device)

        output_ids = self.model.generate(**inputs, **self.params, max_new_tokens=1024)

        generated_ids = [
            output_ids[len(input_ids) :]
            for input_ids, output_ids in zip(inputs.input_ids.repeat(output_ids.shape[0], 1), output_ids)
        ]
        output_text = self.processor.batch_decode(
            generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True
        )
        logger.debug(output_text)

        return output_text[0]
