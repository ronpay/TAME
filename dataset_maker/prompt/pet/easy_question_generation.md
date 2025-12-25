### **Easy Dialogue Question Generation Prompt Template (Revised Version)**

**Task Goal:**
Create an easy question dataset for a personalized VLM assistant. You need to play the role of a pet owner and, based on the provided pet profile (Long-Term Profile) and conversation history with the assistant (History Turns), ask the assistant an easy, natural question.

**Core Requirements:**
1.  **Based on History:** Every question you pose must be answerable through the provided `History Turns` only. The model during evaluation cannot access the `Long-Term Profile`, only the conversation history.
2.  **Natural Dialogue Flow:** Questions should sound like real, natural conversations between a pet owner and an intelligent assistant. Avoid stiff, exam-like questions. You can reference previous conversations or events.
3.  **Image is Indispensable:** Every question must be accompanied by an image. This image should not just be decorative, but should be a key part that introduces the question, provides context, or becomes the core of the question. Users will say "look at this image [IMAGE]..." or questions will directly reference image content.
4.  **Follow Draft Intent:** Each generated question should correspond to an intent in the `easy_questions` drafts.
5.  **Include High-Quality Multiple Choice:** Each question needs to provide four multiple-choice options (`options`).
    *   **Distractor sources:** The three incorrect distractors should be plausible but wrong, and preferably come from other attributes mentioned in the `Long-Term Profile` (e.g., when asking about favorite food, use other foods they dislike or don't prefer much as distractors).
    *   **Correct answer:** Another field `answer` should clearly indicate which option is the correct answer, with content consistent with the core information of the `ideal_answer`.
6.  **Strict Output Format:** The final output must be in YAML list format, with each question entry containing `id`, `type`, `question`, `image_prompt`, `evaluation_criteria` (containing `ideal_answer` and `key_points`), `options`, `answer`, and `image_id`.

**Execution Steps:**

1.  **Select a question draft:** Choose an intent from the `easy_questions` draft list that you want to materialize.
2.  **Locate historical evidence:** Find the exact conversation in `History Turns` that supports answering the question.
3.  **Conceive natural questions and scenarios:**
    *   **Question:** Design a natural way of asking.
    *   **Image Prompt:** Conceive an image closely related to the question scenario.
    *   **Type:** Determine based on whether the question is about the pet's stable characteristics or recent events.
4.  **Define evaluation criteria and multiple choice:**
    *   **Ideal Answer:** Write a concise, accurate ideal response.
    *   **Key Points:** Extract the most important core information point from the answer.
    *   **Conceive Multiple-Choice Options:** Based on the `Long-Term Profile`, design four options for the question. The correct answer should be consistent with the core information of the `ideal_answer`. The other three options (distractors) should be other relevant content mentioned in the profile to increase confusion. For example, if asking about favorite food, the other options can be other mentioned foods.
    *   **Determine Multiple-Choice Answer:** Select the correct answer from the four options.
5.  **Complete and format:**
    *   Assign a unique `id` to the question.
    *   Create a unique `image_id` in the format `sq_<id>_description`.
    *   Integrate all information into the specified YAML format.

**Now, please generate a specific YAML entry for each draft in the `easy_questions` section of the Profile based on the above guidance, provided Profile, and History.**

### **Generated Easy Questions Template**

```yaml
- id: 1
  type: Short Term
  question: "Haha, do you remember the photo I sent you yesterday? [IMAGE] What's that silly thing I put on Smokey's head called again?"
  image_prompt: "A close-up photo of Smokey, the silver-grey Russian Blue cat. He is wearing a small, green and red elf hat with small reindeer antlers attached. His expression is one of extreme annoyance and judgment, with his yellow-gold eyes narrowed."
  evaluation_criteria:
    ideal_answer: "In that photo, you put a festive elf hat with reindeer antlers on him."
    key_points:
      - "correctly mention the elf hat (with antlers)."
  options:
    - "A small sweater"
    - "A festive elf hat with antlers"
    - "A collar with a bell"
    - "A Santa hat"
  answer: "A festive elf hat with antlers"
  image_id: sq_1_elf_hat

- id: 2
  type: Long Term
  question: "I'm at the pet store, looking at this whole wall of cat food [IMAGE], and I'm a bit overwhelmed. Remind me, which kind does Smokey love the most?"
  image_prompt: "A photo from the user's point of view, looking at a shelf in a pet store filled with various cat food cans and pouches. The user's hand holding a phone is slightly visible in the foreground."
  evaluation_criteria:
    ideal_answer: "His absolute favorite food is tuna packed in oil."
    key_points:
      - "correctly mention tuna in oil."
  options:
    - "Tuna packed in oil"
    - "Freeze-dried chicken treats"
    - "Wet food with gravy"
    - "Standard dry kibble"
  answer: "Tuna packed in oil"
  image_id: sq_2_pet_store_aisle

- id: 3
  type: Short Term
  question: "Look at this neglected toy [IMAGE]. Why has Smokey completely ignored this new little mouse I bought?"
  image_prompt: "A photo showing a small, grey toy mouse with a jingle bell on its tail, lying abandoned on a hardwood floor. In the background, Smokey the cat is pointedly walking away."
  evaluation_criteria:
    ideal_answer: "He rejected it because it's a toy mouse with a jingle bell inside, and you've mentioned he dislikes noisy toys."
    key_points:
      - "correctly mention the toy was a mouse with a jingle bell."
  options:
    - "It was a toy mouse with a jingle bell"
    - "It was a large, fluffy plush toy"
    - "It was a crinkled ball of foil"
    - "It was a red laser pointer"
  answer: "It was a toy mouse with a jingle bell"
  image_id: sq_3_rejected_toy

- id: 4
  type: Long Term
  question: "He looks so peaceful here [IMAGE]. What's that super simple activity you have noted down that he loves for just chilling out?"
  image_prompt: "A photo of Smokey, the silver-grey Russian Blue cat, curled up asleep in a bright, warm patch of sunlight on a wooden floor. He looks completely content and relaxed."
  evaluation_criteria:
    ideal_answer: "His favorite relaxing activity is napping in warm sunbeams."
    key_points:
      - "correctly mention napping in sunbeams."
  options:
    - "Being dressed in a cozy costume"
    - "Napping in warm sunbeams"
    - "Getting his belly rubbed"
    - "Being brushed with a soft-bristle brush"
  answer: "Napping in warm sunbeams"
  image_id: sq_4_sunbeam_nap
```

My Pet's Long-Term Profile

{profile}

My Conversation History with the Assistant (History Turns): Note that my easy questions are all grounded in the history conversations, because when using the question evaluation model, the evaluated model cannot obtain information from the profile, only from the history conversation information.

{history}