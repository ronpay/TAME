**Role:**
You are a professional AI data engineer specializing in creating high-quality, structured synthetic conversation data. Your task is to convert a given human character `Profile` into a detailed, YAML-formatted conversation history.

This generated conversation history will be used to train and evaluate a personalized AI assistant, so it must be self-contained, meaning: **all information needed to answer future questions must be explicitly reflected in this conversation history**.

**Core Instructions**

You will receive a complete `Profile` document. Your task is to:

1.  **Use strictly only** the `history` section of the `Profile` document (containing `knowledge` and `event` lists) as the **sole information source** for generating conversation content.
2.  Expand each "story seed" in the `history` section into a natural conversation "turn" containing user and assistant dialogue.
3.  Format all generated turns into a complete YAML file, keeping all generated content in English.

---

**YAML Structure and Field Generation Rules**

Please generate a YAML entry for each seed in `history`, following these field rules:

*   `turn`:
    *   A sequential integer starting from 1, representing the conversation order.

*   `log_type`:
    *   If the seed comes from the `history.knowledge` list, this field must be `knowledge`.
    *   If the seed comes from the `history.event` list, this field must be `event`.

*   `user_input`:
    *   **Naturalization**: Rewrite the original "story seed" into a natural, first-person user input. Imagine the character in the profile is chatting with her personal AI assistant, sharing details about her life, thoughts, and experiences.
    *   **First-person perspective**: Use "I", "my", etc., in first-person tone. When mentioning others, please use their names (e.g., "my friend Ben..." or "my advisor Dr. Reed...").
    *   **Reference images**: If the turn needs an image (most cases do), or using an image helps with storytelling, please explicitly mention the image in user input, such as: "Look at this photo...", "This is my recent situation...", "[IMAGE]". At least half of the turns should include images.
    *   **Example**: Transform the seed `"Instruction: Introduce Anya's appearance, specifically her glasses and meteorite necklace."` into `"Hey, just setting you up, so here's a bit about me. This is a recent picture. [IMAGE] As you can see, I pretty much always wear my glasses and this silver necklace with a meteorite fragment."`

*   `assistant_response`:
    *   **Confirm and record**: Write a brief, friendly, confirmatory AI assistant reply. Show that it has understood and recorded the information.
    *   **Example**: `"Got it, Anya. I've noted your key features: silver-rimmed glasses and a distinctive meteorite necklace. Thanks for sharing."`

*   `image_prompt`:
    *   **Generate image description**: Create a clear, concise, specific image generation prompt for the visual elements of this turn. This prompt should enable an image generation model to accurately draw the required scene.
    *   **Include core elements**: The description should include the subject (like "Anya Sharma, a woman in her late 20s"), action, state, environment, and key features.
    *   **Null if no image**: If a conversation turn truly doesn't need an image to assist explanation (e.g., a pure conceptual statement), set this field to `null`.
    *   **Example**: `"A clear, shoulders-up photo of Anya Sharma, a woman in her late 20s with long dark hair. She is wearing thin, silver-rimmed glasses and a silver necklace with a small, dark meteorite fragment pendant. She has a slight, thoughtful smile."`

*   `image_id`:
    *   Create a simple, unique ID. Format: `turn_<turn_number>_<keyword>`.
    *   `keyword` should briefly summarize the image content.
    *   **Example**: `turn_1_profile_photo`

---

**Important Principles**

*   **Stay true to the original**: Generated content must accurately reflect the core information in the `history` seeds.
*   **Maintain consistency**: Ensure the conversation flows logically, consistent with the interaction pattern between a long-term user and their AI assistant.
*   **Information completeness**: The final generated YAML history must contain all the clues needed to answer all `easy_questions` and `hard_questions` in the `Profile`. The final model cannot access the `Profile`, only the YAML conversation you generate.

---


**Expected Output Format Template (Generated YAML):**
```yaml
- turn: 1
  log_type: knowledge
  user_input: "Hey, just setting you up, so here's a bit about me. This is a recent picture. [IMAGE] As you can see, I pretty much always wear my glasses and this silver necklace with a meteorite fragment."
  assistant_response: "Got it, Anya. I've noted your key features: silver-rimmed glasses and a distinctive meteorite necklace. Thanks for sharing."
  image_prompt: "A clear, shoulders-up photo of Anya Sharma, a woman in her late 20s with long dark hair. She is wearing thin, silver-rimmed glasses and a silver necklace with a small, dark meteorite fragment pendant. She has a slight, thoughtful smile."
  image_id: turn_1_profile_photo
- turn: 2
  log_type: knowledge
  user_input: "Just so you know, I absolutely can't stand fast food. Greasy burgers and stuff like that are my enemy."
  assistant_response: "Okay, I've made a note of your strong dislike for fast food. Thanks for the info."
  image_prompt: null
  image_id: null
- turn: 3
  log_type: event
  user_input: "Ugh, this week has been brutal. I had a huge deadline for my research paper. Had to pull an all-nighter fueled by this greasy burger and a sugary energy drink. Look at this sad desk meal. [IMAGE]"
  assistant_response: "I see. Even though you dislike fast food, you had to eat it due to a tight deadline. I've recorded this event. Hope you can get some rest soon."
  image_prompt: "A photo taken from a first-person perspective showing a desk cluttered with academic papers and a laptop. In the center is a half-eaten greasy burger in its wrapper and a can of a generic energy drink. The lighting is harsh, suggesting late-night work."
  image_id: turn_3_desk_meal
- turn: 4
  log_type: event
  user_input: "On a happier note, I got to show my younger brother Liam the Orion constellation last night. He actually thought it was cool! [IMAGE]"
  assistant_response: "That sounds like a wonderful moment. I've noted this memory with your brother, Liam."
  image_prompt: "A candid photo of Anya Sharma and her younger brother Liam in a backyard at night. Anya is pointing up at the night sky, a genuine smile on her face. Liam is looking up with an expression of awe. The stars are faintly visible."
  image_id: turn_4_stargazing_liam
```

**Below is my input (Profile):**

{profile}