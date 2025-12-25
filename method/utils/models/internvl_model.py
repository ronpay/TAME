import math
import numpy as np
import torch
import torchvision.transforms as T
from PIL import Image
from torchvision.transforms.functional import InterpolationMode
from transformers import AutoModel, AutoTokenizer
from loguru import logger

from .base_model import BaseModel

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

def build_transform(input_size):
    """Build image transformation pipeline"""
    MEAN, STD = IMAGENET_MEAN, IMAGENET_STD
    transform = T.Compose([
        T.Lambda(lambda img: img.convert('RGB') if img.mode != 'RGB' else img),
        T.Resize((input_size, input_size), interpolation=InterpolationMode.BICUBIC),
        T.ToTensor(),
        T.Normalize(mean=MEAN, std=STD)
    ])
    return transform

def find_closest_aspect_ratio(aspect_ratio, target_ratios, width, height, image_size):
    """Find the closest aspect ratio from target ratios"""
    best_ratio_diff = float('inf')
    best_ratio = (1, 1)
    area = width * height
    for ratio in target_ratios:
        target_aspect_ratio = ratio[0] / ratio[1]
        ratio_diff = abs(aspect_ratio - target_aspect_ratio)
        if ratio_diff < best_ratio_diff:
            best_ratio_diff = ratio_diff
            best_ratio = ratio
        elif ratio_diff == best_ratio_diff:
            if area > 0.5 * image_size * image_size * ratio[0] * ratio[1]:
                best_ratio = ratio
    return best_ratio

def dynamic_preprocess(image, min_num=1, max_num=12, image_size=448, use_thumbnail=False):
    """Dynamically preprocess image into multiple patches"""
    orig_width, orig_height = image.size
    aspect_ratio = orig_width / orig_height

    # Calculate the existing image aspect ratio
    target_ratios = set(
        (i, j) for n in range(min_num, max_num + 1) for i in range(1, n + 1) for j in range(1, n + 1) if
        i * j <= max_num and i * j >= min_num)
    target_ratios = sorted(target_ratios, key=lambda x: x[0] * x[1])

    # Find the closest aspect ratio to the target
    target_aspect_ratio = find_closest_aspect_ratio(
        aspect_ratio, target_ratios, orig_width, orig_height, image_size)

    # Calculate the target width and height
    target_width = image_size * target_aspect_ratio[0]
    target_height = image_size * target_aspect_ratio[1]
    blocks = target_aspect_ratio[0] * target_aspect_ratio[1]

    # Resize the image
    resized_img = image.resize((target_width, target_height))
    processed_images = []
    for i in range(blocks):
        box = (
            (i % (target_width // image_size)) * image_size,
            (i // (target_width // image_size)) * image_size,
            ((i % (target_width // image_size)) + 1) * image_size,
            ((i // (target_width // image_size)) + 1) * image_size
        )
        # Split the image
        split_img = resized_img.crop(box)
        processed_images.append(split_img)
    assert len(processed_images) == blocks
    if use_thumbnail and len(processed_images) != 1:
        thumbnail_img = image.resize((image_size, image_size))
        processed_images.append(thumbnail_img)
    return processed_images

def load_image_tensor(image, input_size=448, max_num=12):
    """Load and preprocess image into tensor format"""
    if isinstance(image, str):
        image = Image.open(image).convert('RGB')
    elif isinstance(image, Image.Image):
        image = image.convert('RGB')
    
    transform = build_transform(input_size=input_size)
    images = dynamic_preprocess(image, image_size=input_size, use_thumbnail=True, max_num=max_num)
    pixel_values = [transform(img) for img in images]
    pixel_values = torch.stack(pixel_values)
    return pixel_values


class InternVLModel(BaseModel):
    """InternVL3-8B model implementation for single GPU"""
    
    def __init__(self, model_id="OpenGVLab/InternVL3-8B", params={}):
        super().__init__()
        self.model_id = model_id
        self.params = params if params else {}
        
        # For single GPU, we use device_map="auto" instead of the complex splitting
        logger.info(f"Loading InternVL model: {model_id}")
        self.model = AutoModel.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            load_in_8bit=False,  # Set to True if you need to save memory
            low_cpu_mem_usage=True,
            use_flash_attn=True,
            trust_remote_code=True,
            device_map="auto"  # Simplified for single GPU
        ).eval()
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_id, 
            trust_remote_code=True, 
            use_fast=False
        )
        
        # Default generation config
        self.generation_config = dict(
            max_new_tokens=1024, 
            do_sample=True,
            **self.params
        )
        
        logger.info("InternVL model loaded successfully")

    @staticmethod
    def model_list():
        """Return list of supported model IDs"""
        return ["OpenGVLab/InternVL3-8B"]

    def chat_text(self, prompt: str, max_tokens: int = 512) -> str:
        """Chat with text-only input"""
        try:
            # Update generation config with max_tokens
            generation_config = self.generation_config.copy()
            generation_config['max_new_tokens'] = max_tokens
            
            # Pure text conversation
            response = self.model.chat(
                self.tokenizer, 
                None,  # No image
                prompt, 
                generation_config, 
                history=None, 
                return_history=False
            )
            
            logger.debug(f"InternVL text response: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Error in InternVL chat_text: {e}")
            return f"Error: {str(e)}"

    def chat_img(self, prompt: str, image: Image.Image, max_tokens: int = 512) -> str:
        """Chat with image and text input"""
        try:
            # Update generation config with max_tokens
            generation_config = self.generation_config.copy()
            generation_config['max_new_tokens'] = max_tokens
            
            # Process image
            pixel_values = load_image_tensor(image, max_num=12).to(torch.bfloat16).cuda()
            
            # Add image token to prompt
            image_prompt = f'<image>\n{prompt}'
            
            # Single-image single-round conversation
            response = self.model.chat(
                self.tokenizer, 
                pixel_values, 
                image_prompt, 
                generation_config
            )
            
            logger.debug(f"InternVL image response: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Error in InternVL chat_img: {e}")
            return f"Error: {str(e)}"

    def chat_multi_img(self, prompt: str, images: list[Image.Image], max_tokens: int = 512) -> str:
        """Chat with multiple images (for future extension)"""
        try:
            if not images:
                return self.chat_text(prompt, max_tokens)
            elif len(images) == 1:
                return self.chat_img(prompt, images[0], max_tokens)
            else:
                # Handle multiple images by concatenating them
                generation_config = self.generation_config.copy()
                generation_config['max_new_tokens'] = max_tokens
                
                # Process all images
                pixel_values_list = []
                for image in images:
                    pixel_values = load_image_tensor(image, max_num=12).to(torch.bfloat16).cuda()
                    pixel_values_list.append(pixel_values)
                
                # Concatenate all image tensors
                pixel_values = torch.cat(pixel_values_list, dim=0)
                
                # Create prompt with multiple image tokens
                image_tokens = '<image>\n' * len(images)
                multi_image_prompt = f'{image_tokens}{prompt}'
                
                response = self.model.chat(
                    self.tokenizer,
                    pixel_values,
                    multi_image_prompt,
                    generation_config
                )
                
                logger.debug(f"InternVL multi-image response: {response}")
                return response
                
        except Exception as e:
            logger.error(f"Error in InternVL chat_multi_img: {e}")
            return f"Error: {str(e)}" 