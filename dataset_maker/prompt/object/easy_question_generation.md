**Task Goal:**
Create a easy question dataset for a personalized VLM assistant. You need to play the role of an object owner and, based on the provided Object Profile and conversation history with the assistant (History Turns), ask the assistant a simple, natural question.

**Core Requirements:**
1.  **Based on History:** Every question you pose must be answerable through the provided `History Turns` only. The model during evaluation cannot access the `Object Profile`, only the conversation history.
2.  **Natural Dialogue Flow:** Questions should sound like real, natural conversations between an object owner and an intelligent assistant. Avoid stiff, exam-like questions. You can reference previous conversations or events.
3.  **Image is Indispensable:** Every question must be accompanied by an image. This image should not just be decorative, but should be a key part that introduces the question, provides context, or becomes the core of the question. Users will say "look at this image [IMAGE]..." or questions will directly reference image content.
4.  **Follow Draft Intent:** Each generated question should correspond to an intent in the `easy_questions` drafts.
5.  **Include High-Quality Multiple Choice:** Each question needs to provide four multiple-choice options (`options`).
    *   **Distractor sources:** The three incorrect distractors should be plausible but wrong, and preferably come from other attributes mentioned in the `Object Profile` (e.g., if asking about the object's origin, use other possible origin stories as distractors; if asking about a particular "scar's" origin, use other possible accidents as distractors).
    *   **Correct answer:** Another field `answer` should clearly indicate which option is the correct answer, with content consistent with the core information of the `ideal_answer`.
6.  **Strict Output Format:** The final output must be in YAML list format, with each question entry containing `id`, `type`, `question`, `image_prompt`, `evaluation_criteria` (containing `ideal_answer` and `key_points`), `options`, `answer`, and `image_id`.

**Execution Steps:**

1.  **Select a question draft:** Choose an intent from the `easy_questions` draft list that you want to materialize.
2.  **Locate historical evidence:** Find the exact conversation in `History Turns` that supports answering the question.
3.  **Conceive natural questions and scenarios:**
    *   **Question:** Design a natural way of asking.
    *   **Image Prompt:** Conceive an image closely related to the question scenario.
    *   **Type:** Determine based on whether the question is about the object's **stable identity/history** or **recent events/changes**.
4.  **Define evaluation criteria and multiple choice:**
    *   **Ideal Answer:** Write a concise, accurate ideal response.
    *   **Key Points:** Extract the most important core information point from the answer.
    *   **Conceive Multiple-Choice Options:** Based on the `Object Profile`, design four options for the question. The correct answer should be consistent with the core information of the `ideal_answer`. The other three options (distractors) should be other relevant content mentioned in the profile to increase confusion.
    *   **Determine Multiple-Choice Answer:** Select the correct answer from the four options.
5.  **Complete and format:**
    *   Assign a unique `id` to the question.
    *   Create a unique `image_id` in the format `sq_<id>_<description>`.
    *   Integrate all information into the specified YAML format.

**Now, please generate a specific YAML entry for each draft in the `easy_questions` section of the Profile based on the above guidance, provided Profile, and History. Keep all generated content in English.**

### **Generated Easy Questions Template**

```yaml
- id: 1
  type: Short Term
  question: "I finally did it! Check out the new look for The Sentinel. [IMAGE] I can't remember the name of this specific style of keycap I bought, can you remind me?"
  image_prompt: "A close-up photo of 'The Sentinel', a mechanical keyboard. The alphanumeric keys have been replaced with new, sculpted, retro-style keycaps in shades of cream and orange. They look taller and more curved than standard keycaps."
  evaluation_criteria:
    ideal_answer: "You installed the 'SA Profile' keycaps on it last weekend."
    key_points:
      - "correctly mention the keycap profile is 'SA Profile'."
  options:
    - "Cherry Profile"
    - "SA Profile"
    - "OEM Profile"
    - "XDA Profile"
  answer: "SA Profile"
  image_id: sq_1_keycap_upgrade

- id: 2
  type: Long Term
  question: "I'm looking at guitars online [IMAGE], and it got me thinking about Rosie. What's the story behind this specific chip on her headstock again? It's her most famous battle scar."
  image_prompt: "A photo showing a close-up of the headstock of 'Rosie', a worn acoustic guitar. There is a noticeable, small chip in the wood on the top edge. The user's finger is pointing to the chip."
  evaluation_criteria:
    ideal_answer: "That chip is from when you accidentally dropped it during your first high school talent show."
    key_points:
      - "correctly mention it was dropped at the first high school talent show."
  options:
    - "It was dropped during your first high school talent show."
    - "Your younger brother knocked it over."
    - "It was damaged during a move."
    - "It arrived from the store with that chip."
  answer: "It was dropped during your first high school talent show."
  image_id: sq_2_guitar_scar

- id: 3
  type: Short Term
  question: "My backpack is getting really crowded with memories! [IMAGE] What country is this newest flag patch I added from my trip last month?"
  image_prompt: "A photo of a well-traveled backpack covered in various patches. One patch, showing the red circle on a white background, looks newer and cleaner than the others. The photo is taken at an angle to highlight this specific patch."
  evaluation_criteria:
    ideal_answer: "That new patch is the flag of Japan, which you added after your trip last month."
    key_points:
      - "correctly identify the new patch as the flag of Japan."
  options:
    - "South Korea"
    - "Canada"
    - "Japan"
    - "Thailand"
  answer: "Japan"
  image_id: sq_3_new_patch

- id: 4
  type: Long Term
  question: "Ah, nothing like the first coffee of the day. [IMAGE] I have a dozen mugs, but remind me, what's the practical reason I always end up using this specific one?"
  image_prompt: "A photo of a person's hand holding a thick, slightly chipped ceramic mug filled with steaming coffee. The morning light is streaming in through a window in the background."
  evaluation_criteria:
    ideal_answer: "You prefer it because its thick ceramic walls keep your coffee hot for much longer than your other, thinner mugs."
    key_points:
      - "correctly mention its thick walls keep coffee hot longer."
  options:
    - "It was a gift from your best friend."
    - "It has a funny quote on it."
    - "Its thick walls keep coffee hot longer."
    - "It's the largest mug you own."
  answer: "Its thick walls keep coffee hot longer."
  image_id: sq_4_favorite_mug
```

**My Object's Long-Term Profile:**

{profile}

**My Conversation History with the Assistant (History Turns):**

{history}