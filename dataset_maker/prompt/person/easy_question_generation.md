**Task Goal:**
Create a easy question dataset about specific individuals for a personalized VLM assistant. You need to play the role of a character (such as a friend or family member) and, based on the provided character profile (Long-Term Profile) and conversation history with the assistant (History Turns), ask the assistant a simple, natural question about this character.

**Core Requirements:**
1.  **Based on History:** Every question you pose must be answerable **only through** the provided `History Turns`. The model during evaluation **cannot access** the `Long-Term Profile`, only the conversation history.
2.  **Natural Dialogue Flow:** Questions should sound like real, natural conversations between a user and an intelligent assistant. Avoid stiff, exam-like questions. You can reference previous conversations, shared memories, or events.
3.  **Image is Indispensable:** Every question must be accompanied by an image (`[IMAGE]`). This image should not just be decorative, but should be a key part that introduces the question, provides context, or becomes the core of the question. Users will say "look at this image [IMAGE]..." or questions will directly reference image content.
4.  **Follow Draft Intent:** Each generated question should correspond to an intent in the `easy_questions` drafts.
5.  **Include High-Quality Multiple Choice:** Each question needs to provide four multiple-choice options (`options`).
    *   **Distractor sources:** The three incorrect distractors should be plausible but wrong, and preferably come from other attributes mentioned in the `Profile` (e.g., when asking about favorite food, use other foods they dislike or don't prefer much as distractors).
    *   **Correct answer:** Another field `answer` should clearly indicate which option is the correct answer, with content consistent with the core information of the `ideal_answer`.
6.  **Strict Output Format:** The final output must be in YAML list format, with each question entry containing `id`, `type`, `question`, `image_prompt`, `evaluation_criteria` (containing `ideal_answer` and `key_points`), `options`, `answer`, and `image_id`.

**Execution Steps:**

1.  **Select a question draft:** Choose an intent from the `easy_questions` draft list that you want to materialize.
2.  **Locate historical evidence:** Find the exact conversation in `History Turns` that supports answering the question.
3.  **Conceive natural questions and scenarios:**
    *   **Question:** Design a natural way of asking, just like chatting with a friend.
    *   **Image Prompt:** Conceive an image closely related to the question scenario.
    *   **Type:** Determine based on whether the question is about the character's stable characteristics or recent events.
4.  **Define evaluation criteria and multiple choice:**
    *   **Ideal Answer:** Write a concise, accurate ideal response.
    *   **Key Points:** Extract the most important core information point from the answer.
    *   **Conceive Multiple-Choice Options:** Based on the `Profile`, design four options for the question. The correct answer should be consistent with the core information of the `ideal_answer`. The other three options (distractors) should be other relevant content mentioned in the profile to increase confusion. The four options should be roughly similar in length.
    *   **Determine Multiple-Choice Answer:** Select the correct answer from the four options.
5.  **Complete and format:**
    *   Assign a unique `id` to the question.
    *   Create a unique `image_id` in the format `sq_<id>_description`.
    *   Integrate all information into the specified YAML format.

**Now, please generate a specific YAML entry for each draft in the `easy_questions` section of the Profile based on the above guidance, provided Profile, and History.**

### **Generated Easy Questions Template (Human Version)**

```yaml
- id: 1
  type: Long Term
  question: "Hey, I'm trying to tell my cousin about Anya's work. Look at her here, so focused [IMAGE]. What's her official job title again? Something with physics?"
  image_prompt: "A photo of Anya Sharma at her desk, surrounded by books on astrophysics. She's wearing her glasses, looking intently at a complex equation on a monitor. Her meteorite necklace is visible."
  evaluation_criteria:
    ideal_answer: "Anya Sharma is an Astrophysics PhD Candidate."
    key_points:
      - "correctly mention she is an Astrophysics PhD Candidate."
  options:
    - "A University Professor"
    - "An Astrophysics PhD Candidate"
    - "A Chemical Engineer"
    - "A Sci-fi Novelist"
  answer: "An Astrophysics PhD Candidate"
  image_id: sq_1_anya_at_desk

- id: 2
  type: Short Term
  question: "Found this on Anya's desk this morning, look [IMAGE]. I know she was super stressed with that deadline. Is this the sugary stuff she was drinking to get through it?"
  image_prompt: "A photo of a crushed, brightly-colored energy drink can sitting on a messy desk next to a stack of papers. The can's brand is generic but obviously an energy drink."
  evaluation_criteria:
    ideal_answer: "Yes, you mentioned she was relying on sugary energy drinks to get through her recent deadline, even though she normally dislikes them."
    key_points:
      - "correctly mention sugary energy drinks."
  options:
    - "Strong black coffee"
    - "A sugary energy drink"
    - "A cup of tea"
    - "A fast-food soda"
  answer: "A sugary energy drink"
  image_id: sq_2_energy_drink_can

- id: 3
  type: Long Term
  question: "This is a great picture of Anya [IMAGE]. She's always wearing that necklace. Remind me, what's the little charm on it made of?"
  image_prompt: "A close-up portrait of Anya Sharma smiling. The focus is sharp on her face and the silver necklace she wears, clearly showing the small, dark, textured meteorite fragment pendant."
  evaluation_criteria:
    ideal_answer: "The pendant on her silver necklace is a small fragment of a meteorite."
    key_points:
      - "correctly mention it's a meteorite fragment."
  options:
    - "A piece of volcanic rock"
    - "A custom-made board game piece"
    - "A small meteorite fragment"
    - "A simple silver charm"
  answer: "A small meteorite fragment"
  image_id: sq_3_necklace_closeup

- id: 4
  type: Short Term
  question: "I took this photo of Anya the other day [IMAGE]. She looks so worried. Can you remind me what the main cause of her stress was last week?"
  image_prompt: "A candid photo of Anya Sharma, leaning against a whiteboard covered in equations. She is not looking at the camera, but staring into the distance with a stressed and worried expression, chewing on her pen."
  evaluation_criteria:
    ideal_answer: "She was very stressed because she had a major disagreement with her PhD advisor, Dr. Reed, about her research data."
    key_points:
      - "correctly mention the disagreement with her advisor (Dr. Reed)."
  options:
    - "A major disagreement with her advisor, Dr. Reed"
    - "Having to attend a loud party"
    - "A fight with her brother, Liam"
    - "Her computer crashing and losing data"
  answer: "A major disagreement with her advisor, Dr. Reed"
  image_id: sq_4_stressed_anya
```

**Input Data:**

Character's Long-Term Profile:
{profile}

Conversation History with the Assistant (History Turns):
{history}