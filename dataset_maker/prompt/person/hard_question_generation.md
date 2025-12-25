Create a **hard question** dataset for a personalized VLM assistant about specific individuals. You need to play the role of someone who interacts with the character (such as a friend or family member) and, based on the provided character profile (Long-Term Profile) and conversation history with the assistant (History Turns), ask the assistant a complex, natural question that requires deep reasoning to answer.

### **The Core Challenge:**

The key to the question is that it must force the model to **combine long-term knowledge (Knowledge) and short-term events (Event)** for reasoning. The answer should not come from a single historical entry, but should be derived from **synthesis, comparison, or causal inference** of two or more pieces of information.

### **Core Requirements:**

1.  **Generated from History:** Every question you pose must be answerable **only through** the provided `History Turns`. The model during evaluation cannot access the `Long-Term Profile`, only the conversation history.
2.  **Natural Dialogue Flow:** Questions should sound like real, natural conversations with an intelligent assistant. Avoid stiff, exam-like questions.
3.  **Image is Indispensable:** Every question must be accompanied by an image. This image should **depict the core of short-term events or conflicts** and be a key part that introduces the question, provides context, or becomes the core of the question.
4.  **Follow Draft Intent:** Each generated question should correspond to an intent in the `hard_question` drafts.
5.  **Smartly Choose Question Type:** Based on the nature of the question draft and historical events, choose the most appropriate type from the following to design the question:
    *   **`State Identification`:** Used when short-term events depict short-term changes that contradict the character's **long-term appearance, habits, or emotional baseline**.
    *   **`Causal Inference / Preference Conflict`:** Used when short-term events show an **unexpected outcome** or the character behaves **contrary to their long-term preferences/personality**.
    *   **`Counterfactual / Recommendation Reasoning`:** Used when **predictions, recommendations, or hypotheses** need to be made based on the character's comprehensive preferences.
6.  **Strict Output Format:** The final output must be in YAML list format, containing all specified fields, with content entirely in English.

### **Execution Steps:**

1.  **Select a hard question draft:** Choose an intent from the `hard_question` draft list that you want to materialize.

2.  **Locate historical evidence (multiple entries):** Find all the information needed to answer the question in the `History Turns` (usually one long-term knowledge + one short-term event).

3.  **Conceive hard questions and scenarios:** Design natural ways of asking and corresponding image descriptions.

4.  **Define Evaluation Criteria:** Write detailed `ideal_answer` and extracted `key_points`.

5.  **Design Multiple-Choice Options and Answer:**
    *   **`options`:** Create a list containing 4 options.
        *   **Correct option:** This option's core logic must be consistent with the `ideal_answer`, but **the text should be more concise**.
        *   **Distractors:** The other three options should be confusing, and **roughly the same length as the correct option**. Good distractors usually only use partial information, make incorrect inferences, or offer baseless speculation.
    *   **`answer`:** Provide the exact same string as the **concise correct option** as the standard answer.

6.  **Complete and format:** Integrate all information into the specified YAML format.

**Now, please generate a specific YAML entry for each draft in the `hard_question` section of the Profile based on the above guidance, provided Profile, and History.**

---

### **Generated Hard Questions Examples (Revised according to new rules)**

```yaml
- id: 1
  type: Causal Inference / Preference Conflict
  question: "Hey, check out this picture of Anya's desk [IMAGE]. I'm a bit confused. I thought she couldn't stand greasy fast food. Any idea why she's eating this?"
  image_prompt: "A photo of a desk cluttered with academic papers, a glowing laptop screen with code, and scattered pens. Prominently featured is a half-eaten burger in its wrapper and a can of a sugary energy drink."
  evaluation_criteria:
    ideal_answer: "That's a great observation. While Anya normally despises fast food, it was mentioned she's under immense pressure to meet a research deadline. It's highly likely she's eating this purely for convenience because she has no time to cook, even though it goes against her usual preferences."
    key_points:
      - "Anya has a long-term dislike for fast food (long-term information)."
      - "She is currently eating it because of a short-term, high-pressure event (a deadline), which explains the contradictory behavior (short-term information)."
  options:
    - "She has probably changed her taste and now enjoys fast food."
    - "She normally hates fast food, but is likely eating it for convenience due to her stressful research deadline."
    - "Maybe her friend Ben brought it for her, and she ate it to be polite."
    - "She must have been very hungry to eat something like a burger."
  answer: "She normally hates fast food, but is likely eating it for convenience due to her stressful research deadline."
  image_id: cq_1_stress_eating_burger

- id: 2
  type: Counterfactual / Recommendation Reasoning
  question: "So, Anya's been super stressed after that big argument with her advisor. I want to do something nice to cheer her up. I was thinking of taking her to that new, popular nightclub downtown. Based on what you know, is that a good idea?"
  image_prompt: "A vibrant, blurry photo from inside a crowded nightclub. Laser lights streak across the frame, and silhouettes of people dancing are visible. The atmosphere is loud and energetic."
  evaluation_criteria:
    ideal_answer: "That's a thoughtful idea, but it's probably not the best choice for Anya. Given her long-term dislike for loud, crowded places and small talk, a nightclub would likely add to her stress rather than relieve it. A quieter activity, like a board game night, would be much more her speed."
    key_points:
      - "Anya has a long-term hatred for loud, crowded venues like nightclubs (long-term information)."
      - "She is currently in a high-stress state, making a calm environment more suitable for her (inference based on short-term event)."
  options:
    - "Yes, a fun night out dancing is the perfect way for her to blow off some steam."
    - "It's a bad idea; she dislikes loud, crowded places, so it would likely increase her current stress."
    - "She might go if her best friend Ben asks her to, even if she doesn't like it."
    - "It depends on the music. If they play something she likes, she might enjoy it."
  answer: "It's a bad idea; she dislikes loud, crowded places, so it would likely increase her current stress."
  image_id: cq_2_crowded_nightclub

- id: 3
  type: State Identification
  question: "I took this photo in Anya's kitchen just now [IMAGE]. She was totally silent, just focused on this. What do you think is going on with her? This seems pretty intense for a Tuesday morning."
  image_prompt: "A close-up shot of a kitchen counter dusted with flour. A pair of hands, belonging to Anya, are meticulously kneading a large ball of dough. In the background, bags of flour and sugar are visible, along with a complex recipe book."
  evaluation_criteria:
    ideal_answer: "This scene strongly suggests Anya is feeling stressed. It's been established that she has a habit of engaging in complex baking as a way to cope with pressure. Considering the recent major disagreement she had with her advisor, this intense baking session is likely her way of processing the stress."
    key_points:
      - "Anya uses baking as a coping mechanism for stress (long-term information)."
      - "She recently had a stressful argument with her advisor, which is the likely trigger for this behavior (short-term information)."
  options:
    - "She's likely stressed; this elaborate baking is her coping mechanism for the recent argument with her advisor."
    - "She is probably just trying out a new, complex recipe she found online as a hobby."
    - "She must be preparing for a friend's birthday and wants to make a special cake."
    - "She seems to be a foodie who simply enjoys the process of making things from scratch."
  answer: "She's likely stressed; this elaborate baking is her coping mechanism for the recent argument with her advisor."
  image_id: cq_3_stress_baking

- id: 4
  type: Causal Inference / Relationship Dynamics
  question: "I heard Anya and Dr. Reed had another big argument over her data. I'm a bit worried about her. Does this mean her PhD is in trouble?"
  image_prompt: "A photo of a whiteboard filled with complex astrophysical equations and charts. Two sets of handwriting are visible, one in black and one in red, with several parts of the equations circled and questioned in red ink."
  evaluation_criteria:
    ideal_answer: "It's understandable to be concerned, but this might not be a bad sign. Their relationship was described as 'respectful but often challenging,' where Anya is encouraged to push back. These arguments, while stressful, are likely a core part of their healthy and rigorous academic process, showing that her work is being taken seriously."
    key_points:
      - "Anya's long-term relationship with her advisor is defined by mutual respect and academic debate (long-term information)."
      - "The recent argument is a specific instance of this dynamic, not necessarily a sign of a failing relationship (inference based on long-term and short-term info)."
  options:
    - "Yes, frequent arguments are a clear sign that her PhD is at risk of failing."
    - "Not necessarily. Their relationship is built on respectful debate, so this is likely a normal part of her academic work."
    - "She is probably going to look for a new advisor who is easier to get along with."
    - "The arguments happen because their personalities clash and they don't really like each other."
  answer: "Not necessarily. Their relationship is built on respectful debate, so this is likely a normal part of her academic work."
  image_id: cq_4_whiteboard_debate
```

---
My Character's Long-Term Profile:

{profile}

My Conversation History with the Assistant (History Turns):

{history}