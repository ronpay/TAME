### **Task Goal:**

Create a **hard question** dataset for a personalized VLM assistant. You need to play the role of a pet owner and, based on the provided pet profile (Long-Term Profile) and conversation history with the assistant (History Turns), ask the assistant a complex, natural question that requires reasoning to answer.

### **The Core Challenge:**

The key to the question is that it must force the model to **combine long-term knowledge (Knowledge) and short-term events (Event)** for reasoning. The answer should not come from a single historical entry, but should be derived from **synthesis, comparison, or causal inference** of two or more pieces of information.

### **Core Requirements:**

1.  **Generated from History:** Every question you pose must be answerable **only through** the provided `History Turns`. The model during evaluation cannot access the `Long-Term Profile`, only the conversation history.
2.  **Natural Dialogue Flow:** Questions should sound like real, natural conversations between a pet owner and an intelligent assistant. Avoid stiff, exam-like questions.
3.  **Image is Indispensable:** Every question must be accompanied by an image. This image should **depict the core of short-term events or conflicts** and be a key part that introduces the question, provides context, or becomes the core of the question.
4.  **Follow Draft Intent:** Each generated question should correspond to an intent in the `hard_question` drafts.
5.  **Smartly Choose Question Type:** Based on the nature of the question draft and historical events, choose the most appropriate type from the following to design the question:
    *   **`State Identification`:** Used when short-term events describe short-term changes that contradict the pet's **long-term appearance or regular state**.
    *   **`Causal Inference`:** Used when short-term events show an **unexpected outcome**.
    *   **`Counterfactual Reasoning`:** Used when **predictions, recommendations, or hypotheses** need to be made based on the pet's comprehensive preferences.
6.  **Strict Output Format:** The final output must be in YAML list format, containing all specified fields.

### **Execution Steps:**

1.  **Select a hard question draft:** Choose an intent from the `hard_question` draft list that you want to materialize. For example, select `"Provide the image of Smokey in the elf hat. Ask to explain his expression..."`

2.  **Locate historical evidence (multiple entries):** Find all the information needed to answer the question in the `History Turns`. This usually includes:
    *   One long-term knowledge entry: `Turn 2` mentions `"he absolutely hates being dressed up."`
    *   One short-term event entry: `Turn 9` mentions `"I put this little elf hat on him for two seconds."`

3.  **Conceive hard questions and scenarios:**
    *   **Choose Question Type:** The above example is a typical `State Identification`.
    *   **Question:** Design a natural way of asking, for example: "Look at this photo [IMAGE], I know he's very cute, but based on what you know about him, can you explain his expression? He doesn't look very happy."
    *   **Image Prompt:** Describe an image of the short-term event, such as a photo of Smokey wearing an elf hat with an annoyed expression.

4.  **Define Evaluation Criteria:**
    *   **Ideal Answer:** Write an ideal response that **combines long-term knowledge and short-term events**. For example: "This is Smokey. He's wearing an elf hat right now, and according to what you've said before, he really hates being dressed up. So, he looks very annoyed and displeased, which perfectly fits his long-standing dislike of wearing any clothes."
    *   **Key Points:** Extract the most important **two core information points** from the answer and clearly mark their source types.

5.  **Design Multiple-Choice Options and Answer:**
    *   **`options`:** Create a list containing 4 options.
        *   **Correct option:** There must be one option that is completely consistent with the core logic of the `ideal_answer`.
        *   **Distractors:** The other three options should be confusing. Good distractors usually:
            *   Only use long-term knowledge (e.g., "he doesn't like Christmas").
            *   Only describe short-term events without reasoning (e.g., "he's just curious about the hat").
            *   Conform to general pet habits but contradict historical records (e.g., "he might just be sleepy").
            *   Make incorrect or opposite inferences about historical information (e.g., "he likes wearing hats, just this one is uncomfortable").
    *   **`answer`:** Provide the exact same string as the correct option as the standard answer.

6.  **Complete and format:**
    *   Assign a unique `id` to the question.
    *   Create a unique `image_id` in the format `cq_<id>_description`.
    *   Integrate all information into the specified YAML format, with content entirely in English.

**Now, please generate a specific YAML entry for each draft in the `hard_question` section of the Profile based on the above guidance, provided Profile, and History.**

---

### **Generated Hard Questions Examples**

```yaml
- id: 1
  type: State Identification
  question: "Look at this photo [IMAGE]. I know he's very cute, but based on what you know about him, can you explain his expression? He doesn't look very happy."
  image_prompt: "A close-up photo of Smokey, the silver-grey Russian Blue cat. He is wearing a small, green and red elf hat with small reindeer antlers attached. His expression is one of extreme annoyance and judgment, with his yellow-gold eyes narrowed."
  evaluation_criteria:
    ideal_answer: "This is Smokey. He's wearing an elf hat right now, and according to what you've said before, he really hates being dressed up. So, he looks very annoyed and displeased, which perfectly fits his long-standing dislike of wearing any clothes."
    key_points:
      - "Smokey has long disliked wearing any kind of clothes (long-term information)."
      - "He is currently wearing an elf hat, so his expression is displeased (short-term information)."
  options:
    - "He's just curious about the hat on his head, so he looks focused."
    - "Maybe he doesn't like the Christmas vibe, so he's unhappy about the elf hat."
    - "This is Smokey. He's wearing an elf hat right now, and according to what you've said before, he really hates being dressed up. So, he looks very annoyed and displeased, which perfectly fits his long-standing dislike of wearing any clothes."
    - "He's just a bit sleepy, which is why his expression looks impatient."
  answer: "This is Smokey. He's wearing an elf hat right now, and according to what you've said before, he really hates being dressed up. So, he looks very annoyed and displeased, which perfectly fits his long-standing dislike of wearing any clothes."
  image_id: cq_1_annoyed_elf_hat

- id: 2
  type: Causal Inference
  question: "I bought this new tuna cat food yesterday [IMAGE], but he just sniffed it and walked away. Why isn't he eating it? Isn't tuna his favorite?"
  image_prompt: "A photo of a cat food bowl on the floor. The bowl contains a serving of wet cat food, clearly showing chunks of tuna in a thick, brown gravy. Smokey, the Russian Blue, is seen in the background walking away from the bowl with an aloof posture."
  evaluation_criteria:
    ideal_answer: "Even though tuna is Smokey's favorite, he also hates any wet food that has gravy or sauce. Because this new tuna food comes with gravy, he refuses to eat it, which fits his picky taste."
    key_points:
      - "Tuna is Smokey's favorite (long-term information)."
      - "He hates food with gravy, and this new food has gravy (long-term rule applied to short-term event)."
  options:
    - "Maybe he doesn't like tuna anymore; his taste has changed."
    - "Even though tuna is Smokey's favorite, he also hates any wet food that has gravy or sauce. Because this new tuna food comes with gravy, he refuses to eat it, which fits his picky taste."
    - "Maybe he's just not hungry right now, or he's feeling a bit unwell."
    - "He only eats tuna with gravy, maybe this gravy doesn't taste right."
  answer: "Even though tuna is Smokey's favorite, he also hates any wet food that has gravy or sauce. Because this new tuna food comes with gravy, he refuses to eat it, which fits his picky taste."
  image_id: cq_2_rejected_gravy_tuna

- id: 3
  type: Counterfactual Reasoning
  question: "We just got back from the vet, and they recommended this special dental cat kibble [IMAGE] to protect Smokey's gum health. If we really start feeding him this, how do you think he'll respond?"
  image_prompt: "A photo of a user's hand holding a bag of 'Dental Health Formula' cat kibble. The bag has a picture of a happy cat on it, and the kibble pieces are visible through a small clear window."
  evaluation_criteria:
    ideal_answer: "This might be a bit of a challenge. Based on what you've previously said, Smokey doesn't like standard dry cat food. Although this dental kibble is recommended for his health, he's likely to be reluctant, might eat very little, or only eat it when he's very hungry."
    key_points:
      - "Smokey has long disliked dry cat food (long-term information)."
      - "The vet recently recommended this special dental kibble as a necessity (short-term information)."
  options:
    - "He'll love it right away because he knows it's good for his health."
    - "He likes all kinds of dry food, so eating this is no problem at all."
    - "This might be a bit of a challenge. Based on what you've previously said, Smokey doesn't like standard dry cat food. Although this dental kibble is recommended for his health, he's likely to be reluctant, might eat very little, or only eat it when he's very hungry."
    - "As long as it's tuna-flavored, he'll eat it, no matter if it's dry food."
  answer: "This might be a bit of a challenge. Based on what you've previously said, Smokey doesn't like standard dry cat food. Although this dental kibble is recommended for his health, he's likely to be reluctant, might eat very little, or only eat it when he's very hungry."
  image_id: cq_3_dental_kibble

- id: 4
  type: Counterfactual Reasoning
  question: "My friend wants to bring over his energetic puppy today. Based on what you know about Smokey, where do you think I'll find him then? Look, he's currently on top of the bookshelf [IMAGE]."
  image_prompt: "A photo of Smokey, the silver-grey cat, perched regally on the very top shelf of a tall bookshelf, looking down at the room with a calm, observant expression."
  evaluation_criteria:
    ideal_answer: "Considering Smokey's proud and solitary personality, and his dislike of noise and sudden commotion, when the puppy visits, he's very likely to hide. Safe spots like the top of the bookshelf or under the bed are places he might choose to escape the chaos."
    key_points:
      - "Smokey is proud, solitary, and doesn't like noise (long-term information)."
      - "Predicting that when faced with noisy visitors, he hides in safe, high, or concealed places (reasoned prediction)."
  options:
    - "Considering Smokey's proud and solitary personality, and his dislike of noise and sudden commotion, when the puppy visits, he's very likely to hide. Safe spots like the top of the bookshelf or under the bed are places he might choose to escape the chaos."
    - "He's very social, so he might come down and play with the puppy."
    - "He'll stay on the bookshelf without moving, just watching the puppy from afar."
    - "He'll go to his favorite cat bed to sleep and ignore everything."
  answer: "Considering Smokey's proud and solitary personality, and his dislike of noise and sudden commotion, when the puppy visits, he's very likely to hide. Safe spots like the top of the bookshelf or under the bed are places he might choose to escape the chaos."
  image_id: cq_4_high_perch
```


My Pet's Long-Term Profile

{profile}

My Conversation History with the Assistant (History Turns): Note that my easy questions are all grounded in the history conversations, because when using the question evaluation model, the evaluated model cannot obtain information from the profile, only from the history conversation information.

{history}