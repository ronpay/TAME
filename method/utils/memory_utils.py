import re
from pathlib import Path
from typing import Optional

import yaml
from loguru import logger
from PIL import Image


class MemoryManager:
    def __init__(self, concept_id: str, model_name: str = "default"):
        self.concept_id = concept_id
        self.model_name = model_name
        base_path = Path("memory") / model_name / concept_id
        self.static_memory_path = base_path / "static.yaml"
        self.dynamic_memory_path = base_path / "dynamic.yaml"
        self.portrait_path = base_path / "portrait.png"
        self.static_memory_path.parent.mkdir(parents=True, exist_ok=True)
        self.dynamic_memory_path.parent.mkdir(parents=True, exist_ok=True)
        self.portrait_path.parent.mkdir(parents=True, exist_ok=True)
        self.static_memory = self.read_static_memory()  # FIX: Remove redundant parameter
        self.dynamic_memory = self.read_dynamic_memory()  # FIX: Remove redundant parameter

    def read_static_memory(self) -> list:  # Remove unused concept_id parameter
        if not self.static_memory_path.exists():
            return []
        with open(self.static_memory_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or []

    def read_dynamic_memory(self) -> list:  # Remove unused concept_id parameter
        if not self.dynamic_memory_path.exists():
            return []
        with open(self.dynamic_memory_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or []

    def read_portrait(self) -> Optional[Image.Image]:  # Remove unused concept_id parameter
        if not self.portrait_path.exists():
            return None
        return Image.open(self.portrait_path)

    def update_static_memory(
        self, memory: str, op: str, target_id: int = 0
    ):  # FIX: Remove unused concept_id parameter and memory_type parameter
        if not memory and op == "add":  # FIX: Validate memory content
            logger.warning("Cannot add empty memory")
            return

        static_memory = self.static_memory.copy()  # FIX: Work with copy to avoid side effects
        to_added = []

        if op == "add":
            # Replace newlines with periods before storing
            cleaned_memory = memory.replace('\n', ' ') if memory else memory
            to_added.append(cleaned_memory)
            logger.debug(f"Adding to static memory: '{cleaned_memory}'")
        elif op == "remove":
            if 0 <= target_id < len(static_memory):
                item_to_remove = static_memory[target_id]
                static_memory[target_id] = "DELETE"
                logger.info(f"Removing from static memory at position {target_id + 1} (1-indexed): '{item_to_remove}'")
            else:
                logger.error(
                    f"Cannot remove from static memory: index {target_id + 1} (1-indexed) out of range. "
                    f"Valid range: [1, {len(static_memory)}]. Current static memory has {len(static_memory)} items."
                )
                return
        elif op == "modify":
            if 0 <= target_id < len(static_memory):
                old_value = static_memory[target_id]
                # Replace newlines with periods before storing
                cleaned_memory = memory.replace('\n', ' ') if memory else memory
                static_memory[target_id] = cleaned_memory
                logger.info(f"Modifying static memory at position {target_id + 1} (1-indexed): '{old_value}' -> '{cleaned_memory}'")
            else:
                logger.error(
                    f"Cannot modify static memory: index {target_id + 1} (1-indexed) out of range. "
                    f"Valid range: [1, {len(static_memory)}]. Current static memory has {len(static_memory)} items."
                )
                return

        static_memory = [m for m in static_memory if m != "DELETE"]
        static_memory.extend(to_added)

        # remove duplicated information while preserving order
        seen = set()
        static_memory = [x for x in static_memory if not (x in seen or seen.add(x))]

        with open(self.static_memory_path, "w", encoding="utf-8") as f:
            yaml.dump(static_memory, f, allow_unicode=True)
        self.static_memory = static_memory

    def update_dynamic_memory(
        self, memory: str, op: str, target_id: int = 0
    ):  # FIX: Remove unused concept_id parameter
        if not memory and op == "add":  # FIX: Validate memory content
            logger.warning("Cannot add empty memory")
            return

        dynamic_memory = self.dynamic_memory.copy()  # FIX: Work with copy to avoid side effects
        to_added = []

        if op == "add":
            # Replace newlines with periods before storing
            cleaned_memory = memory.replace('\n', ' ') if memory else memory
            to_added.append(cleaned_memory)
            logger.debug(f"Adding to dynamic memory: '{cleaned_memory}'")
        elif op == "remove":
            if 0 <= target_id < len(dynamic_memory):
                item_to_remove = dynamic_memory[target_id]
                dynamic_memory[target_id] = "DELETE"
                logger.info(f"Removing from dynamic memory at position {target_id + 1} (1-indexed): '{item_to_remove}'")
            else:
                logger.error(
                    f"Cannot remove from dynamic memory: index {target_id + 1} (1-indexed) out of range. "
                    f"Valid range: [1, {len(dynamic_memory)}]. Current dynamic memory has {len(dynamic_memory)} items."
                )
                return
        elif op == "modify":
            if 0 <= target_id < len(dynamic_memory):
                old_value = dynamic_memory[target_id]
                # Replace newlines with periods before storing
                cleaned_memory = memory.replace('\n', ' ') if memory else memory
                dynamic_memory[target_id] = cleaned_memory
                logger.info(f"Modifying dynamic memory at position {target_id + 1} (1-indexed): '{old_value}' -> '{cleaned_memory}'")
            else:
                logger.error(
                    f"Cannot modify dynamic memory: index {target_id + 1} (1-indexed) out of range. "
                    f"Valid range: [1, {len(dynamic_memory)}]. Current dynamic memory has {len(dynamic_memory)} items."
                )
                return

        dynamic_memory = [m for m in dynamic_memory if m != "DELETE"]
        dynamic_memory.extend(to_added)

        # remove duplicated information while preserving order
        seen = set()
        dynamic_memory = [x for x in dynamic_memory if not (x in seen or seen.add(x))]

        with open(self.dynamic_memory_path, "w", encoding="utf-8") as f:
            yaml.dump(dynamic_memory, f, allow_unicode=True)
        self.dynamic_memory = dynamic_memory

    def clean_dynamic_memory(self):  # Remove concept_id parameter and fix path
        if self.dynamic_memory_path.exists():
            self.dynamic_memory_path.unlink()
            self.dynamic_memory = []

    def save_portrait(self, portrait: Image.Image):  # Remove concept_id parameter and add validation
        if portrait is None:  # Add None check
            logger.warning("Cannot save None portrait")
            return

        self.portrait_path.parent.mkdir(parents=True, exist_ok=True)
        portrait.save(self.portrait_path)

    def apply_fifo_to_dynamic_memory(self, max_size: int = 10):
        """Apply FIFO rule to dynamic memory to limit its size"""
        dynamic_memory = self.read_dynamic_memory()

        if len(dynamic_memory) > max_size:
            # Keep only the most recent max_size items
            dynamic_memory = dynamic_memory[-max_size:]
            logger.info(f"Applied FIFO rule: dynamic memory trimmed to {max_size} items")

            with open(self.dynamic_memory_path, "w", encoding="utf-8") as f:
                yaml.dump(dynamic_memory, f, allow_unicode=True)
            self.dynamic_memory = dynamic_memory

    def parse_update_ops(self, response: str, memory_type: str) -> dict:  # FIX: Remove concept_id parameter
        """
        Parse the response (yaml format), and return a dict of update ops
        Then call update_static_memory or update_dynamic_memory to perform the update

        Expected format:
        op: add/remove/modify
        target_id: index for remove/modify operations
        memory: memory content
        Note: Both static and dynamic memory now use the same simple string format
        """
        m = re.search(r"```yaml\s*(.*?)```", response, re.S)
        response = m.group(1) if m else response
        try:
            parsed_response = yaml.safe_load(response)
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return {}

        # Handle both single dict and list of dicts
        if isinstance(parsed_response, dict):
            parsed_response = [parsed_response]
        elif not isinstance(parsed_response, list):
            return {}

        for update_op in parsed_response:
            if not update_op or not isinstance(update_op, dict):  # FIX: Add type check
                continue

            op = update_op.get("op", "add")
            memory = update_op.get("memory", None)
            target_id = update_op.get("target_id", None)  # Changed: default to None instead of 0

            # Validate required target_id for remove/modify operations
            if op in ["remove", "modify"] and target_id is None:
                logger.error(f"Operation '{op}' requires target_id but none was provided. Skipping operation.")
                continue

            # Handle case where target_id might be a list (defensive programming)
            if isinstance(target_id, list) and len(target_id) > 0:
                target_id = target_id[0]

            # Convert to int if needed and validate
            if target_id is not None:
                try:
                    target_id = int(target_id)
                except (ValueError, TypeError):
                    logger.error(f"Invalid target_id type: {type(target_id)}, value: {target_id}. Skipping operation.")
                    continue

                # Validate that target_id is positive (1-indexed input)
                if target_id <= 0:
                    logger.error(f"Invalid target_id: {target_id}. Must be >= 1 (1-indexed). Skipping operation.")
                    continue

                # Convert from 1-indexed (model format) to 0-indexed (Python)
                target_id = target_id - 1

                # Validate range against current memory size
                if op in ["remove", "modify"]:
                    current_memory = self.static_memory if memory_type == "static" else self.dynamic_memory
                    if not (0 <= target_id < len(current_memory)):
                        logger.error(
                            f"target_id {target_id + 1} (1-indexed) out of range. "
                            f"Valid range: [1, {len(current_memory)}]. Current {memory_type} memory has {len(current_memory)} items. Skipping operation."
                        )
                        continue
            else:
                target_id = 0  # Default for add operation (not used)

            if memory_type == "static":
                self.update_static_memory(memory, op, target_id)
            else:
                self.update_dynamic_memory(memory, op, target_id)

        return parsed_response


class ConceptManager:
    def __init__(self, model_name: str = "default"):
        self.model_name = model_name
        self.memory_path = Path("memory") / model_name
        self.memory_path.mkdir(parents=True, exist_ok=True)
        self.memories = []
        self.retrieval_target = []

    def read_memories(self):
        """Initialize memories from existing concept directories"""
        self.memories.clear()  # Clear existing memories
        for memory_path in self.memory_path.iterdir():
            if memory_path.is_dir():
                concept_id = memory_path.name
                memory_manager = MemoryManager(concept_id, self.model_name)
                self.memories.append(memory_manager)

    def get_concept_retrieval_target(self) -> list:  # FIX: Add return value
        """FIX: Return the retrieval targets instead of just setting them"""
        self.retrieval_target.clear()  # Clear existing targets

        for memory in self.memories:
            portrait = memory.read_portrait()
            static_memory = memory.read_static_memory()
            visual_prompt = ""

            for m in static_memory:
                # Since static memory is now a simple list of strings like dynamic memory
                if isinstance(m, str) and "visual" in m.lower():
                    visual_prompt += f"{m}\n"

            if not visual_prompt:
                visual_prompt = "NONE"

            self.retrieval_target.append((portrait, visual_prompt))

        return self.retrieval_target

    def get_concept_id(self, concept_idx: int) -> Optional[str]:  # FIX: Add boundary check and return type
        """FIX: Add boundary checking and proper error handling"""
        if not (0 <= concept_idx < len(self.memories)):
            logger.error(f"Invalid concept index: {concept_idx}")
            return None
        return self.memories[concept_idx].concept_id

    def get_concept_memory(self, concept_id: str) -> Optional[MemoryManager]:
        target_memory = None
        for memory in self.memories:
            if memory.concept_id == concept_id:
                print(memory.concept_id)
                target_memory = memory
                break
        target_static_memory = target_memory.read_static_memory()
        target_dynamic_memory = target_memory.read_dynamic_memory()
        return target_static_memory, target_dynamic_memory