import re
from pathlib import Path
from typing import List, Optional, Tuple

import yaml
from loguru import logger
from PIL import Image

from method.utils.memory_utils import ConceptManager, MemoryManager
from method.utils.mllm_factory import MLLMFactory
from method.utils.retrieval_utils import Detector, Retriever

"""
Double Memory Personalized MLLM System

This module implements a training-free and state-aware personalized MLLM assistant
that maintains both static (stable characteristics) and dynamic (contextual) memory.
"""

# Model shortcuts mapping
MODEL_SHORTCUTS = {"qwenvl": "Qwen/Qwen2.5-VL-7B-Instruct", "internvl": "OpenGVLab/InternVL3-8B"}


def get_model_id(model_arg: str) -> str:
    """Convert model shortcut to full model ID"""
    return MODEL_SHORTCUTS.get(model_arg, model_arg)


def get_model_short_name(model_id: str) -> str:
    """Get short name for model ID"""
    for short_name, full_id in MODEL_SHORTCUTS.items():
        if full_id == model_id:
            return short_name
    # Fallback: use last part of model ID
    return model_id.split("/")[-1].replace("-", "_").lower()


class TAME:
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.model_short_name = get_model_short_name(model_id)
        self.model = MLLMFactory(model_id)
        self.history_path = Path("data/concept")
        self._detector = None
        self._retriever = None

        self.concept_manager = ConceptManager(self.model_short_name)
        self.concept_manager.read_memories()  # FIX: Initialize concept memories

    @property
    def detector(self) -> Detector:
        """Lazy-load detector on first access"""
        if self._detector is None:
            logger.info("Loading detector (lazy-loaded).")
            self._detector = Detector()
        return self._detector

    @property
    def retriever(self) -> Retriever:
        """Lazy-load retriever on first access"""
        if self._retriever is None:
            logger.info("Loading retriever (lazy-loaded).")
            self._retriever = Retriever()
        return self._retriever

    def dump_numbered_list(self, list: list) -> str:
        return "\n".join([f"{i + 1}. {item}" for i, item in enumerate(list)])

    def memory_exists(self, concept_id: str) -> bool:
        """Check if memory files already exist for a concept"""
        memory_manager = MemoryManager(concept_id, self.model_short_name)
        return memory_manager.static_memory_path.exists() or memory_manager.dynamic_memory_path.exists()

    # read history for all concepts
    def read_history_all(self):
        skipped_count = 0
        processed_count = 0

        for concept_dir in self.history_path.iterdir():
            if concept_dir.is_dir():
                concept_id = concept_dir.name

                # Skip if memory already exists for this concept
                if self.memory_exists(concept_id):
                    skipped_count += 1
                    logger.info(f"Skipping {concept_id} - memory already exists")
                    continue

                processed_count += 1
                self.read_history(concept_id)

        logger.info(f"Memory building completed: {processed_count} processed, {skipped_count} skipped")

    def read_history(self, concept_id: str):
        """Add comprehensive error handling"""
        logger.info(f"Reading history for concept {concept_id}")
        history_path = self.history_path / concept_id / "history.yaml"

        if not history_path.exists():
            logger.warning(f"History file not found: {history_path}")
            return

        with open(history_path, "r", encoding="utf-8") as f:
            history = yaml.safe_load(f)

        if not history:
            logger.warning(f"Empty history file: {history_path}")
            return

        # iterate through history
        for turn in history:
            if not isinstance(turn, dict):
                logger.warning(f"Invalid turn format: {turn}")
                continue

            image_id = turn.get("image_id")
            if image_id:
                image_path = self.history_path / concept_id / "img" / f"{image_id}.png"
                image = Image.open(image_path).convert("RGB")
            else:
                image = None

            self.read_history_single_turn(
                concept_id, image, turn.get("user_input", ""), turn.get("assistant_response", "")
            )

    def read_history_single_turn(
        self, concept_id: str, img: Optional[Image.Image], question: str, answer: str
    ):
        """FIX: Add parameter validation and error handling"""
        if not concept_id:
            logger.error("concept_id cannot be empty")
            return

        memory_manager = MemoryManager(concept_id, self.model_short_name)
        dynamic_memory = memory_manager.read_dynamic_memory()

        # Normal dynamic memory processing
        memory_type = "dynamic"
        memory_prompt_type = "dynamic"

        # Part 2: Process memory updates
        memory_prompt = f"""You are a strict Data Entry Assistant for `{concept_id}`.
Your task is to update the **Dynamic Memory** (temporary buffer) based on the **Current Conversation**.

## GOAL
Extract **new information** provided in the conversation.
- If the User provides new facts, preferences, or current status -> **ADD** to memory.
- If the User updates/corrects existing info -> **MODIFY** the existing memory.
- If the conversation is just chit-chat (greetings, thanks) -> **DO NOTHING** (Output []).

## INPUT DATA
**Existing Dynamic Memory:**
```yaml
{self.dump_numbered_list(dynamic_memory if memory_type == "dynamic" else memory_manager.read_static_memory())}

```

**Current Conversation:**

* User Input: "{question}"
* Assistant Response: "{answer}"
* Attached Image: {"Yes" if img else "No"}

## CRITICAL RULES

1. **Be Specific:** Do not write "User asked a question." Write "User asked about the weather."
2. **No Duplicates:** Check the "Existing Dynamic Memory" list. If the info is already there, do not add it again.
3. **Concise:** Keep memory strings under 25 words.
4. **Context:** Use the name "{concept_id}" instead of "it" or "he/she".
5. **Visual:** Include the word "visual" to the memory if it relates to appearance.

## EXAMPLES

**Conversation:** "My cat Luna is limping today."
**Action:** ADD -> "Luna is limping today."

**Conversation:** "Hello, how are you?"
**Action:** IGNORE (No useful info).

**Conversation:** (User corrects a mistake) "Actually, Luna is 5 years old, not 4."
**Action:** MODIFY (Find index of old age memory) -> "Luna is 5 years old."

## OUTPUT FORMAT

Provide a `# Analysis` comment first, then the YAML code box.

# Analysis:
# - The user mentioned [X]. This is new information. I will ADD it.
# - The user said "Thanks". This is noise. I will IGNORE it.

```yaml
- concept_id: "{concept_id}"
  op: "add" # or "modify" or "remove"
  memory: "The specific content extracted"
  target_id: 1 # Only required for 'modify' or 'remove'
```

If no updates are needed, output: []

Generate the output: (Start with # Analysis then YAML code box)
"""

        if img is not None:
            memory_response = self.model.chat_img(memory_prompt, img)
        else:
            memory_response = self.model.chat_text(memory_prompt)
        logger.info(f"{memory_prompt_type.title()} memory update: {memory_response.replace('\n', ' ')}")

        # Use normal memory processing
        memory_manager.parse_update_ops(memory_response, memory_type)

        # Log the number of operations processed
        try:
            yaml_match = re.search(r"```yaml\s*(.*?)```", memory_response, re.DOTALL)
            if yaml_match:
                yaml_content = yaml_match.group(1)
            else:
                yaml_content = memory_response

            parsed_ops = yaml.safe_load(yaml_content)
            if isinstance(parsed_ops, list):
                logger.info(f"Processed {len(parsed_ops)} dynamic memory operations")
            elif parsed_ops is None or (isinstance(parsed_ops, list) and len(parsed_ops) == 0):
                logger.info("Processed 0 dynamic memory operations")
        except Exception as e:
            logger.debug(f"Could not count dynamic operations: {e}")

        static_memory = memory_manager.read_static_memory()
        dynamic_memory = memory_manager.read_dynamic_memory()

        # if static_memory is empty, use the image to generate a portrait
        if not static_memory and img is not None:  # FIX: Add img None check
            memory_manager.save_portrait(img)

        # Part 1: Process static memory updates based on dynamic memory analysis (transfer step)
        # Analyze dynamic memory to identify persistent attributes for static memory
        updated_dynamic_memory = memory_manager.read_dynamic_memory()

        if updated_dynamic_memory:  # Only process if there's dynamic memory to analyze
            static_analysis_prompt = f"""You are a strict Memory Manager. Your goal is to move PERMANENT FACTS from Dynamic Memory to Static Memory, while leaving TEMPORARY EVENTS alone.

## INPUT DATA
Current Dynamic Memory (Recent observations) for `{concept_id}`:
```yaml
{self.dump_numbered_list(updated_dynamic_memory)}

```

Current Static Memory (Long-term facts) for `{concept_id}`:

```yaml
{self.dump_numbered_list(static_memory)}

```

## CLASSIFICATION RULES (CRITICAL)

1. **PERMANENT FACTS (MOVE these):**
* Characteristics that rarely change.
* Examples: Names, species, breeds, personality traits (e.g., "timid"), physical features (e.g., "white fur"), favorite foods, owner's name.
* Action: Create a `static_ops` to ADD it and a `dynamic_ops` to REMOVE it.
* Visual Cues: Include the word "visual" to the memory if it relates to appearance.


2. **TEMPORARY EVENTS (DO NOT MOVE):**
* Things happening right now or recently.
* Examples: Eating, sleeping, walking, feeling hungry, distinct conversations, mood swings.
* Action: **IGNORE**. Do not create any operations for these.


## OUTPUT FORMAT

Provide a `# Analysis` comment first, then the YAML code box.

Example Output Structure:

# Analysis:
# - Dynamic Memory 1 (Luna is sleeping): This is a temporary EVENT. Ignore.
# - Dynamic Memory 2 (Luna is a cat): This is a FACT. Move to Static.

```yaml
# **Dynamic Memory Operations** (to remove transferred items):
dynamic_ops:
- concept_id: "{concept_id}"
  op: "remove"
  target_id: 2 # Removing Item 2 because it was moved

# **Static Memory Operations** (to add/modify/remove persistent information) (duplicate items should be removed):
static_ops:
- concept_id: "{concept_id}"
  op: "add"
  memory: "Luna is a cat" # The content of the fact
```

If no Permanent Facts are found, return empty lists:

```yaml
dynamic_ops: []
static_ops: []
```

Generate the output: (Start with # Analysis then YAML code box)
"""

            # Get response from model
            if img is not None:
                memory_transform_response = self.model.chat_img(static_analysis_prompt, img)
            else:
                memory_transform_response = self.model.chat_text(static_analysis_prompt)

            logger.info(f"Static memory update: {memory_transform_response.replace('\n', ' ')}")

            # Parse and execute the memory operations using existing parse_update_ops function
            try:
                # Extract YAML content
                yaml_match = re.search(r"```yaml\s*(.*?)```", memory_transform_response, re.DOTALL)
                if yaml_match:
                    yaml_content = yaml_match.group(1)
                else:
                    yaml_content = memory_transform_response

                parsed_response = yaml.safe_load(yaml_content)

                if isinstance(parsed_response, dict):
                    # Process dynamic memory operations (removals) using parse_update_ops
                    dynamic_ops = parsed_response.get("dynamic_ops", [])
                    if dynamic_ops:
                        # Convert to YAML string format that parse_update_ops expects
                        dynamic_yaml = yaml.dump(dynamic_ops, allow_unicode=True)
                        memory_manager.parse_update_ops(f"```yaml\n{dynamic_yaml}```", "dynamic")

                    # Process static memory operations (additions/modifications) using parse_update_ops
                    static_ops = parsed_response.get("static_ops", [])
                    if static_ops:
                        # Convert to YAML string format that parse_update_ops expects
                        static_yaml = yaml.dump(static_ops, allow_unicode=True)
                        memory_manager.parse_update_ops(f"```yaml\n{static_yaml}```", "static")

                    logger.info(
                        f"Processed {len(dynamic_ops)} dynamic and {len(static_ops)} static memory operations"
                    )

            except Exception as e:
                logger.error(f"Error processing static memory from dynamic memory: {e}")
                logger.debug(f"Raw response: {memory_transform_response}")

        # Apply FIFO rule to dynamic memory at the end
        memory_manager.apply_fifo_to_dynamic_memory(max_size=10)

    def identify_concept(self, img: Image.Image, question: str) -> Optional[str]:  # Add return type hint
        """Add comprehensive error handling and validation"""
        if img is None:
            logger.error("Image cannot be None")
            return None

        concept_profiles = self.concept_manager.get_concept_retrieval_target()  # Now returns value

        if not concept_profiles:
            logger.warning("No concept profiles available")
            return None

        detected_objects = self.detector.detect_and_crop(
            img, ["animal", "person", "household item", "personal belonging"]
        )
        logger.debug(f"Detected objects: {detected_objects}")

        # If no objects detected, use the original image
        if not detected_objects:
            logger.info("No objects detected, using original image")
            detected_objects = [img]

        concept_idx = self.retriever.retrieve_concept(detected_objects, concept_profiles)
        concept_id = self.concept_manager.get_concept_id(concept_idx)

        return concept_id

    def get_context_prompt(
        self, concept_id: str, question: str | None = None, img: Optional[Image.Image] = None
    ) -> str:
        """
        Get the context prompt for a specific concept using both static and dynamic memory.
        If question and/or image are provided, performs memory alignment to extract relevant information.

        Args:
            concept_id: The identifier of the concept
            question: Optional question to align memory against
            img: Optional image to consider during memory alignment

        Returns:
            str: The formatted context prompt containing memory information, potentially aligned to the question
        """
        if not concept_id:
            logger.error("concept_id cannot be empty")
            return ""

        memory_manager = MemoryManager(concept_id, self.model_short_name)

        static_memory = memory_manager.read_static_memory()
        dynamic_memory = memory_manager.read_dynamic_memory()

        # Handle alignment based on whether question is provided
        if question:
            # Build the original memory context
            original_context = self._build_memory_context(concept_id, static_memory, dynamic_memory)

            # Create alignment prompt
            alignment_prompt = f"""# TASK: MEMORY EXTRACTION
You are a precise information extraction agent. Your goal is to identify and list specific, detailed memories from the provided [MEMORY] that relate to the [USER QUESTION].

# CONSTRAINTS
- **OUTPUT FORMAT:** Use a simple bulleted list only.
- **DO NOT ANSWER:** Do not answer the question itself. 
- **NO PROSE:** Do not include an intro, outro, or conversational filler.
- **ACCURACY:** Only extract memories present in the [MEMORY].

# INPUT DATA
- **USER QUESTION:** "{question}"
- **IMAGE ATTACHED:** {"Yes" if img else "No"}
- **MEMORY CONTENT:** ---
{original_context}
---

# INSTRUCTIONS
1. Analyze the [USER QUESTION] to determine what specific information is being sought.
2. Scan the [MEMORY CONTENT] for memories, including specific attributes like dates, names, colors, or quantities.
3. **DETAIL LEVEL:** Provide descriptive phrases rather than single words (e.g., "The blue sedan" instead of just "car").
4. List each relevant detail as a single, concise bullet point.
5. Stop immediately after the last bullet point.

# EXTRACTED MEMORIES:
"""

            # Use appropriate model method based on whether image is provided
            if img is not None:
                aligned_response = self.model.chat_img(alignment_prompt, img)
            else:
                aligned_response = self.model.chat_text(alignment_prompt)

            logger.info(f"Memory aligned for question: {question[:50]}...")
            return aligned_response
        else:
            # Return original memory context without alignment (no question)
            return self._build_memory_context(concept_id, static_memory, dynamic_memory)

    def answer_question(
        self, concept_id: str, question: str, context_prompt: str, img: Optional[Image.Image] = None
    ) -> str:
        """
        Answer a question about a specific concept using the provided context prompt.

        Args:
            concept_id: The identifier of the concept
            question: The question to answer
            context_prompt: The formatted context prompt containing memory information
            img: Optional image that may be related to the question

        Returns:
            str: The comprehensive answer based on memory context
        """
        if not concept_id or not question:  # FIX: Add parameter validation
            logger.error("concept_id and question cannot be empty")
            return "Error: Invalid parameters provided."

        # Create the main prompt for answering the question
        answer_prompt = f"""# TASK: Personalized Concept Analysis
You are a precision-focused AI assistant. Your goal is to answer questions about a specific CONCEPT by synthesizing its permanent traits (Static) and its current state (Dynamic).

# INPUT DATA
- **CONCEPT CONTEXT**: {context_prompt}
- **USER QUESTION**: "{question}"
- **IMAGE STATUS**: {"Image provided: Yes" if img else "Image provided: No"}

# ANALYSIS REQUIREMENTS
To provide a complete answer, you must evaluate:
1. **Static Profile**: What are the permanent traits, core preferences, and stable features of this concept?
2. **Dynamic State**: What are the recent updates, temporary changes, or current behaviors?
3. **Synthesis**: If recent data contradicts permanent traits, highlight the shift (e.g., "Usually X, but currently Y").

# OUTPUT CONSTRAINTS (STRICT)
- **Format**: Write exactly ONE concise paragraph. 
- **Style**: Be conversational but factually dense.
- **Accuracy**: Use only the provided memory context. If the answer is unknown, state that clearly.
- **Visuals**: If an image is present, integrate visual evidence with the known conceptual features.

# RESPONSE:
[Insert your single-paragraph response here]"""

        # Use appropriate model method based on whether image is provided
        if img is not None:
            response = self.model.chat_img(answer_prompt, img)
        else:
            response = self.model.chat_text(answer_prompt)

        return response

    def answer_choice_question(
        self,
        concept_id: str,
        question: str,
        options: List[str],
        context_prompt: str,
        img: Optional[Image.Image] = None,
    ) -> str:
        """
        Answer a multiple choice question about a specific concept using the provided context prompt.

        Args:
            concept_id: The identifier of the concept
            question: The question to answer
            options: List of 4 options for the multiple choice question
            context_prompt: The formatted context prompt containing memory information
            img: Optional image that may be related to the question

        Returns:
            str: The selected option (A, B, C, or D)
        """
        if not concept_id or not question or not options:
            logger.error("concept_id, question, and options cannot be empty")
            return "Error: Invalid parameters provided."

        if len(options) != 4:
            logger.error("Exactly 4 options must be provided")
            return "Error: Exactly 4 options required."

        # Format options as A, B, C, D
        formatted_options = "\n".join([f"{chr(65 + i)}. {option}" for i, option in enumerate(options)])

        # Create the main prompt for answering the multiple choice question
        choice_prompt = f"""You are a personalized AI assistant with detailed knowledge about specific concepts and their current states. You have access to both static stable information and dynamic contextual information about the concept.

# CONCEPT INFORMATION
{context_prompt}

# MULTIPLE CHOICE QUESTION
Question: "{question}"
{"Image provided: Yes" if img else "Image provided: No"}

Options:
{formatted_options}

# YOUR TASK
Based on the available memory information about the concept, select the most appropriate answer from the given options. Consider both:
1. **Static characteristics**: Permanent traits, preferences, and features
2. **Dynamic context**: Recent events, temporary changes, current states

# RESPONSE GUIDELINES
- Analyze each option carefully against the memory information
- Choose the option that best matches the concept's characteristics and current context
- If there's a conflict between static and dynamic information, prioritize the most relevant information for the question
- Respond with ONLY the letter (A, B, C, or D) of your chosen answer

Generate your response (only the letter):"""

        # Use appropriate model method based on whether image is provided
        if img is not None:
            response = self.model.chat_img(choice_prompt, img)
        else:
            response = self.model.chat_text(choice_prompt)

        # Extract only the letter from the response
        choice_match = re.search(r"[ABCD]", response.strip().upper())
        if choice_match:
            return choice_match.group()
        else:
            logger.warning(f"Could not extract valid choice from response: {response}")
            return "A"  # Default to A if no valid choice found

    def complete_qa_workflow(
        self,
        img_path: str,
        question: str,
        options: Optional[List[str]] = None,
        options_answer: Optional[str] = None,
        ground_truth_concept_id: Optional[str] = None,
    ) -> Tuple[Optional[str], str, Optional[str]]:
        """
        Complete question-answering workflow: identify concept and answer both free-text and choice questions.

        Args:
            img_path: Path to image containing the concept to identify
            question: Question to answer about the concept
            options: Optional list of 4 options for multiple choice question
            options_answer: Optional correct answer for the choice question (for reference)
            ground_truth_concept_id: Optional ground truth concept ID for comparison

        Returns:
            tuple: (concept_id, free_text_answer, choice_answer) - The identified concept, free-text answer, and choice answer
        """
        from colorama import Fore, Style

        if not img_path or not question:
            logger.error("img_path and question cannot be None/empty")
            return None, "Error: Invalid parameters provided.", None

        # Step 1: Identify the concept in the image
        try:
            img = Image.open(img_path).convert("RGB")
        except Exception as e:
            logger.error(f"Error opening image: {e}")
            return None, "Error: Could not open image.", None

        concept_id = self.identify_concept(img, question)

        if concept_id is None:
            return None, "Error: Could not identify any concept in the image.", None

        # Log concept identification result
        if ground_truth_concept_id:
            is_correct = concept_id == ground_truth_concept_id
            status_symbol = " ✅" if is_correct else ""
            logger.info(
                f"{Fore.CYAN}Concept Identification{Style.RESET_ALL}: Predicted={concept_id}, Ground Truth={ground_truth_concept_id}{status_symbol}"
            )
        else:
            logger.info(f"{Fore.CYAN}Concept Identification{Style.RESET_ALL}: Predicted={concept_id}")

        # Step 2: Get context prompt for the identified concept
        context_prompt = self.get_context_prompt(concept_id, question, img)

        # Step 3: Answer the free-text question using the context prompt
        free_text_answer = self.answer_question(concept_id, question, context_prompt, img)

        # Step 4: Answer the choice question if options are provided
        choice_answer = None
        if options and len(options) == 4:
            choice_answer = self.answer_choice_question(concept_id, question, options, context_prompt, img)

        return concept_id, free_text_answer, choice_answer

    def _build_memory_context(self, concept_id: str, static_memory: list, dynamic_memory: list) -> str:
        """
        Build a comprehensive context string from both memory types.

        Args:
            concept_id: The concept identifier
            static_memory: List of static memory entries
            dynamic_memory: List of dynamic memory entries

        Returns:
            str: Formatted context string
        """
        context_parts = [f"Concept ID: {concept_id}\n"]

        # Process static memory
        if static_memory:
            context_parts.append("## STATIC MEMORY")

            for memory_item in static_memory:
                if isinstance(memory_item, str):
                    context_parts.append(f"- {memory_item}")
                else:
                    context_parts.append(f"- {str(memory_item)}")

        # Process dynamic memory
        context_parts.append("\n## DYNAMIC MEMORY")
        if dynamic_memory:
            for memory_item in dynamic_memory:
                if isinstance(memory_item, str):
                    context_parts.append(f"- {memory_item}")
                else:
                    context_parts.append(f"- {str(memory_item)}")
        else:
            context_parts.append("No recent contextual information available.")

        return "\n".join(context_parts)
