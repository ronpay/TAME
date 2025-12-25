from typing import Dict, Optional, Union

from .models.api_model import APIModel
from .models.qwenvl_model import QwenVLModel
from .models.internvl_model import InternVLModel


def MLLMFactory(model_id: str, params: Optional[Dict] = None):
    # Check each model class directly
    model_classes = [
        QwenVLModel,
        APIModel,
        InternVLModel,
    ]
    for model_class in model_classes:
        if model_id in model_class.model_list():
            return model_class(model_id, params)
    raise ValueError(f"Model {model_id} not supported")
