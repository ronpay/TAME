**Task Goal:**

Create a **hard question** dataset for a personalized VLM assistant. You need to play the role of an object owner and, based on the provided Object Profile and conversation history with the assistant (History Turns), ask the assistant a complex, natural question that requires reasoning to answer.

### **The Core Challenge:**

The key to the question is that it must force the model to **combine long-term knowledge (Knowledge) and short-term events (Event)** for reasoning. The answer should not come from a single historical entry, but should be derived from **synthesis, comparison, or causal inference** of two or more pieces of information.

### **Core Requirements:**

1.  **Generated from History:** Every question you pose must be answerable **only through** the provided `History Turns`. The model during evaluation cannot access the `Object Profile`, only the conversation history.
2.  **Natural Dialogue Flow:** Questions should sound like real, natural conversations between an object owner and an intelligent assistant. Avoid stiff, exam-like questions.
3.  **Image is Indispensable:** Every question must be accompanied by an image. This image should **depict the core of short-term events or conflicts** and be a key part that introduces the question, provides context, or becomes the core of the question.
4.  **Follow Draft Intent:** Each generated question should correspond to an intent in the `hard_question` drafts.
5.  **Smartly Choose Question Type:** Based on the nature of the question draft and historical events, choose the most appropriate type from the following to design the question:
    *   **`State Identification`:** Used when short-term events describe short-term changes that contradict the object's **long-term characteristics or regular state** (e.g., a usually dirty backpack being polished to a shine).
    *   **`Causal Inference`:** Used when short-term events show an **unexpected decision or outcome** (e.g., the owner bought a new keyboard but still uses the old one).
    *   **`Counterfactual Reasoning`:** Used when **predictions, recommendations, or hypotheses** need to be made based on the object's comprehensive characteristics.
6.  **Strict Output Format:** The final output must be in YAML list format, containing all specified fields.

### **Execution Steps:**

1.  **Select a hard question draft:** Choose an intent from the `hard_question` draft list that you want to materialize. For example, select `"Pose a conflict question: ...why did the owner choose to repair this old object instead of buying a new one?"`

2.  **Locate historical evidence (multiple entries):** Find all the information needed to answer the question in the `History Turns`. This usually includes:
    *   One long-term knowledge entry: `Turn 1` mentions `"'The Sentinel' is my most important possession... a gift to celebrate my first job."`
    *   One short-term event entry: `Turn 3` mentions `"I had to learn how to solder to replace a failing switch myself."`

3.  **Conceive hard questions and scenarios:**
    *   **Choose Question Type:** The above example is a typical `Causal Inference`.
    *   **Question:** Design a natural way of asking, for example: "Look at my weekend masterpiece [IMAGE]. Honestly, it took me an entire afternoon to fix it. Why do you think I didn't just buy a new one instead of going through all this trouble to repair this old keyboard?"
    *   **Image Prompt:** Describe an image of the short-term event, such as a close-up of the owner using a soldering iron to repair the keyboard.

4.  **Define Evaluation Criteria:**
    *   **Ideal Answer:** Write an ideal response that **combines long-term knowledge and short-term events**. For example: "This is your keyboard 'The Sentinel'. You chose to spend time repairing it instead of buying a new one because it's not just a tool. It's a memento of your first job and has special personal meaning to you. Repairing it is also maintaining that emotional connection."
    *   **Key Points:** Extract the most important **two core information points** from the answer and clearly mark their source types.

5.  **Design Multiple-Choice Options and Answer:**
    *   **`options`:** Create a list containing 4 options.
        *   **Correct option:** There must be one option that is completely consistent with the core logic of the `ideal_answer`.
        *   **Distractors:** The other three options should be confusing. Good distractors usually:
            *   Only use long-term knowledge (e.g., "because you like the typing feel of this keyboard").
            *   Only describe short-term events without reasoning (e.g., "because you just wanted to learn how to use a soldering iron").
            *   Conform to general logic but contradict historical records (e.g., "because buying a new one is too expensive").
            *   Make incorrect or opposite inferences about historical information (e.g., "you repaired it to sell it for a good price").
    *   **`answer`:** Provide the exact same string as the correct option as the standard answer.

6.  **Complete and format:**
    *   Assign a unique `id` to the question, starting from 1.
    *   Create a unique `image_id` in the format `cq_<id>_<description>`.
    *   Integrate all information into the specified YAML format, with content entirely in English.

**Now, please generate a specific YAML entry for each draft in the `hard_question` section of the Profile based on the above guidance, provided Profile, and History. Keep all generated content in English.**

---

### **Generated Hard Questions Examples**

```yaml
- id: 1
  type: Causal Inference
  question: "Look at this photo from my desk yesterday [IMAGE]. I had the brand new keyboard right there, but I still used 'The Sentinel' to finish my project. Why do you think I did that?"
  image_prompt: "A photo of a work desk. In the center is the old, well-used mechanical keyboard 'The Sentinel'. To the side, a brand new, sleek keyboard is visible, still partially in its box. Code is visible on the monitor in the background."
  evaluation_criteria:
    ideal_answer: "Even though the new keyboard was available, you chose 'The Sentinel' for your important project. This is likely because The Sentinel isn't just a tool for you; it's your long-term, reliable partner for creation. When facing a challenge, you trusted your proven companion over a new, unfamiliar one."
    key_points:
      - "The Sentinel has a long-term role as a reliable partner for creation (long-term information)."
      - "Faced with a high-stakes project, you defaulted to your trusted tool instead of the new one (reasoned inference from short-term event)."
  options:
    - "Because you haven't had time to set up the new keyboard yet."
    - "Even though the new keyboard was available, you chose 'The Sentinel' for your important project. This is likely because The Sentinel isn't just a tool for you; it's your long-term, reliable partner for creation. When facing a challenge, you trusted your proven companion over a new, unfamiliar one."
    - "The new keyboard was probably more expensive, and you wanted to keep it in pristine condition."
    - "You were just testing to see if The Sentinel still worked before switching to the new one."
  answer: "Even though the new keyboard was available, you chose 'The Sentinel' for your important project. This is likely because The Sentinel isn't just a tool for you; it's your long-term, reliable partner for creation. When facing a challenge, you trusted your proven companion over a new, unfamiliar one."
  image_id: cq_1_old_vs_new

- id: 2
  type: State Identification
  question: "Here's a picture of my backpack ready for my trip tomorrow [IMAGE]. It looks so... strange. Based on what you know about it, can you explain why it looks so out of character?"
  image_prompt: "A photo of a well-traveled, rugged backpack standing next to a neatly folded business suit on a bed. The backpack has been meticulously cleaned; its usual dust and grime are gone, and it looks unusually neat and tidy."
  evaluation_criteria:
    ideal_answer: "That's your backpack, which is normally a symbol of rugged adventure and is usually covered in the marks of your travels. It looks 'out of character' now because it has been spotlessly cleaned for your formal business trip. Its current pristine state is in direct conflict with its long-term identity as a well-traveled companion."
    key_points:
      - "The backpack's long-term identity is a rugged, well-traveled adventure companion (long-term information)."
      - "It is currently spotlessly clean for a formal trip, which conflicts with its identity (short-term state vs. long-term identity)."
  options:
    - "You probably just bought a new backpack that looks like the old one."
    - "It's just the lighting in the room that makes it look different."
    - "That's your backpack, which is normally a symbol of rugged adventure and is usually covered in the marks of your travels. It looks 'out of character' now because it has been spotlessly cleaned for your formal business trip. Its current pristine state is in direct conflict with its long-term identity as a well-traveled companion."
    - "You must have washed it because it got something spilled on it."
  answer: "That's your backpack, which is normally a symbol of rugged adventure and is usually covered in the marks of your travels. It looks 'out of character' now because it has been spotlessly cleaned for your formal business trip. Its current pristine state is in direct conflict with its long-term identity as a well-traveled companion."
  image_id: cq_2_clean_backpack

- id: 3
  type: Counterfactual Reasoning
  question: "My friend wants to borrow my guitar, 'Rosie', for a heavy metal band practice this weekend. Here she is, looking all peaceful [IMAGE]. Would that be a good idea?"
  image_prompt: "A warm, atmospheric photo of 'Rosie', the acoustic guitar. It's resting on a stand in a cozy room. The wood has a soft glow, and it exudes a sense of calm, history, and gentleness."
  evaluation_criteria:
    ideal_answer: "That might not be the best idea. You've described Rosie as your old, cherished companion with a gentle, mellow tone, perfect for personal, emotional songs. Using her for a heavy metal practice, which is aggressive and loud, would be a huge clash with her inherent character and history. There's also a risk of damaging such a sentimental item."
    key_points:
      - "Rosie has a long-term identity as a gentle, mellow, sentimental object (long-term information)."
      - "Heavy metal practice is an aggressive, loud activity that clashes with Rosie's character and poses a risk (reasoned prediction based on short-term proposal)."
  options:
    - "Sure, a guitar is a guitar, it should be fine for any music style."
    - "That might not be the best idea. You've described Rosie as your old, cherished companion with a gentle, mellow tone, perfect for personal, emotional songs. Using her for a heavy metal practice, which is aggressive and loud, would be a huge clash with her inherent character and history. There's also a risk of damaging such a sentimental item."
    - "Yes, it would be cool to see if Rosie can handle heavy metal music."
    - "No, because your friend might not return it on time."
  answer: "That might not be the best idea. You've described Rosie as your old, cherished companion with a gentle, mellow tone, perfect for personal, emotional songs. Using her for a heavy metal practice, which is aggressive and loud, would be a huge clash with her inherent character and history. There's also a risk of damaging such a sentimental item."
  image_id: cq_3_rosie_and_metal
```

**My Object's Long-Term Profile:**

{profile}

**My Conversation History with the Assistant (History Turns):**

{history}