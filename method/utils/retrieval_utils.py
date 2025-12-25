import torch
from PIL import Image
from sentence_transformers import SentenceTransformer
from torch import Tensor
from torchvision import ops
from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor


class Detector:
    def __init__(self, model_id: str = "IDEA-Research/grounding-dino-base"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = AutoModelForZeroShotObjectDetection.from_pretrained(model_id).to(self.device)
        self.processor = AutoProcessor.from_pretrained(model_id)

    def detect_and_crop(self, image: Image.Image, text_labels: list[str]) -> list[Image.Image]:
        # 1. IMPROVEMENT: Format text as a single dot-separated string
        # This allows the model to detect all classes in one pass and understand them together.
        text_prompt = " . ".join(text_labels) + " ."

        inputs = self.processor(images=image, text=text_prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)

        results = self.processor.post_process_grounded_object_detection(
            outputs,
            inputs.input_ids,
            # box_threshold=0.30,
            text_threshold=0.25,  # Slightly higher text threshold reduces "gibberish" matches
            target_sizes=[image.size[::-1]],
        )[0]

        # Extract tensors for NMS and Fallback logic
        boxes = results["boxes"]
        scores = results["scores"]
        labels = results["labels"]  # These are text labels (str)

        if len(boxes) == 0:
            return []

        # 2. IMPROVEMENT: Fallback/Priority Logic
        # We want to filter out generic labels if a specific label exists for the same spot.
        # Define hierarchy: Specific items > "pet" > "person" > "object"
        # We create a simple priority map (lower number = higher priority)
        priority_map = {label: 1 for label in labels}  # Default priority
        if "object" in priority_map:
            priority_map["object"] = 3
        if "pet" in priority_map:
            priority_map["pet"] = 2
        if "person" in priority_map:
            priority_map["person"] = 2

        # Assign numeric priority to each detection
        priorities = torch.tensor([priority_map.get(l, 1) for l in labels], device=self.device)

        # 3. IMPROVEMENT: Class-Agnostic NMS with Priority
        # We process boxes. If boxes overlap significantly (IoU > 0.5), we keep the one with higher priority (lower score).
        # Since standard NMS sorts by confidence score, we can trick it or do a manual check.
        # Here we use standard NMS for pure deduplication first.
        keep_indices = ops.nms(boxes, scores, iou_threshold=0.5)

        # Now, handle the "Fallback":
        # If we have two remaining boxes that overlap significantly but have different labels,
        # we manually remove the "generic" one.
        final_boxes = []
        final_indices = []

        # Sort kept indices by priority (low to high) then score (high to low)
        # This ensures we process specific high-confidence items first
        sorted_indices = sorted(keep_indices.tolist(), key=lambda i: (priorities[i], -scores[i]))

        accepted_boxes = []  # Store [x1, y1, x2, y2]

        for idx in sorted_indices:
            current_box = boxes[idx]
            is_redundant = False

            # Check overlap with already accepted boxes
            if len(accepted_boxes) > 0:
                # Calculate IoU with all accepted boxes
                accepted_tensor = torch.stack(accepted_boxes)
                iou = ops.box_iou(current_box.unsqueeze(0), accepted_tensor)[0]

                # If overlap > 0.6 with an EXISTING (higher priority) box, discard this one
                if (iou > 0.6).any():
                    is_redundant = True

            if not is_redundant:
                accepted_boxes.append(current_box)
                final_indices.append(idx)

        # Crop final images
        cropped_images = []
        for idx in final_indices:
            box = boxes[idx].tolist()
            # Ensure box is within image bounds
            box = [max(0, box[0]), max(0, box[1]), min(image.width, box[2]), min(image.height, box[3])]
            cropped_image = image.crop(box)
            cropped_images.append(cropped_image)

        return cropped_images


class Retriever:
    def __init__(self, model_id: str = "jinaai/jina-embeddings-v4"):
        self.device = "cuda"
        self.model = SentenceTransformer(model_id, trust_remote_code=True, device=self.device)

    def encode_query_images(self, images: list[Image.Image], batch_size: int = 1):
        image_embeddings = self.model.encode(
            sentences=images,
            task="retrieval",
            batch_size=batch_size,
        )
        return image_embeddings

    def encode_passage_text(self, texts: list[str], batch_size: int = 1):
        text_embeddings = self.model.encode(
            sentences=texts,
            task="retrieval",
            batch_size=batch_size,
        )
        return text_embeddings

    def encode_passage_images(self, images: list[Image.Image], batch_size: int = 1):
        image_embeddings = self.model.encode(
            sentences=images,
            task="retrieval",
            batch_size=batch_size,
        )
        return image_embeddings

    def retrieve_concept(
        self, query_images: list[Image.Image], target_concepts: list[tuple[Image.Image, str]], batch_size: int = 1
    ) -> int:
        # Encode all query images
        query_embeddings = self.encode_query_images(query_images, batch_size=batch_size)

        # Extract and encode all concept images and texts
        concept_images = [concept[0] for concept in target_concepts]
        concept_texts = [concept[1] for concept in target_concepts]

        concept_image_embeddings = self.encode_passage_images(concept_images, batch_size=batch_size)
        concept_text_embeddings = self.encode_passage_text(concept_texts, batch_size=batch_size)

        # Convert to tensors
        query_tensor = torch.tensor(query_embeddings)
        concept_image_tensor = torch.tensor(concept_image_embeddings)
        concept_text_tensor = torch.tensor(concept_text_embeddings)

        # Calculate similarity matrix for images and texts
        image_similarities = torch.mm(query_tensor, concept_image_tensor.T)
        text_similarities = torch.mm(query_tensor, concept_text_tensor.T)

        # Weighted similarity (0.7 for image, 0.3 for text)
        weighted_similarities = 0.7 * image_similarities + 0.3 * text_similarities

        # Find the best query-concept pair
        max_similarity, best_idx = torch.max(weighted_similarities.flatten(), dim=0)

        # Convert flattened index back to concept index
        best_concept_idx = best_idx % len(target_concepts)

        return best_concept_idx.item()
        # get the most similar passage to all query embeddings

    def retrieve(self, query: Tensor, passage: Tensor, top_k: int = 10):
        # get the most similar passage to all query embeddings
        # return the top 1 passages index
        # use cosine similarity
        similarity = torch.nn.functional.cosine_similarity(query, passage, dim=1)
        top_k_indices = torch.topk(similarity, top_k).indices
        return top_k_indices
