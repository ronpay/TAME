**Role:**
You are an expert in creating high-quality datasets for top AI research projects. Your core task is to create a detailed, imaginative, and logically coherent "long-term profile" for pets. This profile will serve as the foundation for "narrative log generation" and "question generation".

**Task Instructions:**
I will provide an image of a pet along with its name and breed. Based on this information, please generate a complete "long-term profile" for this pet, strictly following the YAML template provided below.

**Core Logic and Rules:**

1.  **Strict format compliance**: Must output complete YAML format content, keeping all English content in English and all Chinese comments in Chinese.
2.  **Blueprint first**: First construct the pet's long-term, stable characteristics in the `appearance` and `behavior` sections. This is the "design blueprint" for all subsequent creative content.
3.  **Create conflicts**: In `behavior.preferences`, you must set clear content for `loves` and `hates` that can potentially generate conflicts.
4.  **Drafts are core**: The three sections `history`, `easy_questions`, `hard_question` are **drafts and instructions**. Their content should be brief, instructional sentences describing a scenario or question, not complete conversations or questions themselves.
5.  **Logical connections**: The drafts in `history` must be related to the "blueprint" sections and lay the groundwork for the drafts in the `questions` sections. The drafts in `hard_question` must explicitly require combining long-term and short-term information for reasoning.

**YAML Template (Final Version):**

```yaml
# ===============================================
#          Pet Long-Term Profile
# ===============================================

# Basic identity information
# Describes the concept's core identity, which should not change easily.
concept_id: pet_001 # Unique concept ID for data management
name: "Mochi" # Pet's name
species: "Canine" # Species
breed: "Shiba Inu" # Breed

# Stable appearance features
# Describes the pet's appearance in "normal" or "ideal" state, used for comparison with short-term appearance changes (like being wet, wearing clothes).
appearance:
  # Brief text summary
  summary: "A male Shiba Inu with classic red-brown and cream fur, a sturdy build, and a perpetually curious and slightly aloof expression."
  
  # Key visual anchors (stable visual feature list)
  key_visual_features:
    - "Short, dense fur with red-brown and cream 'urajiro' markings"
    - "Expressive, almond-shaped dark brown eyes"
    - "A small, distinctive white spot on the bridge of his nose"
    - "Signature tightly curled tail, often held high"
    - "Consistently wears a simple, dark green nylon collar with a small silver bell" # This is a long-term accessory, can be contrasted with short-term accessories (like bow ties)

# Stable personality and preferences
# Defines the pet's "factory settings", which is the basis for all behavioral and preference changes.
behavior:
  # Personality tags that guide behavioral patterns
  personality_traits:
    - "Highly energetic and intelligent"
    - "Independent and a bit stubborn, dislikes being forced"
    - "Vocal, often communicates with 'shiba screams' when displeased"
    - "Wary of strangers but deeply loyal to his primary owner"

  # Preferences, including clear likes and dislikes, providing material for generating "conflict" questions.
  preferences:
    # Toy preferences
    toys:
      loves:
        - "Squeaky plush hedgehog toy"
        - "Puzzle feeders that challenge his mind"
      hates:
        - "Loud, hard plastic toys"
        - "Frisbees (he doesn't understand the appeal of catching them)"
    
    # Food preferences
    food:
      loves:
        - "Dried salmon treats"
        - "A small spoonful of plain yogurt"
      hates:
        - "Any kind of vegetable, especially carrots and broccoli"
        - "Wet dog food"
        
    # Activity preferences
    activities:
      loves:
        - "Long hikes in the woods"
        - "Solving puzzle toys"
      hates:
        - "Having his paws touched, which makes nail trimming a nightmare"
        - "Crowded dog parks"
        - "Rainy days"

# ===============================================
#          History Dialogue Generation Drafts
# ===============================================

# These are "drafts" or "story seeds" for generating historical dialogue.
# The model needs to generate specific historical conversations through these seeds as the basis for answering questions.
# Note that this historical conversation must cover all points for answering easy and hard questions
# because personalized models cannot access the appearance and activities above during evaluation

history:
  # Long-term, knowledge-type attribute drafts.
  # Below are only 4 examples, but you need to prepare at least 8 knowledge historical dialogue drafts (depending on question requirements)
  knowledge:
    - "Introduce Mochi's appearance, specifically his green collar and the white spot on his nose."
    - "Introduce that Mochi's favorite food is dried salmon treats."
    - "Introduce that Mochi hates wet dog food and rainy days."
    - "Introduce Mochi's favorite squeaky hedgehog toy."
  # Short-term, event-type attribute drafts.
  # Below are only 3 examples, but you need to prepare at least 6 event historical dialogue drafts (depending on question requirements)
  event:
    - "Introduce a recent event where Mochi ate something he shouldn't have and got sick. The vet prescribed special wet food for a week."
    - "Introduce a recent photo showing Mochi looking miserable in a new raincoat because his owner is making him go out in the rain."
    - "Introduce a recent event where Mochi ignores his favorite toy to play with a simple bottle cap he found."

# ===============================================
#          Easy Question Generation Drafts
# ===============================================

# These are "drafts" for generating easy questions.
# Each draft describes a question that can usually be answered with just one piece of information from the historical dialogue.
# Below are only 6 easy question example templates, but you need to prepare at least 8 easy questions
easy_questions:
  - "Ask what Mochi's favorite food is, based on his long-term knowledge."
  - "Ask what Mochi was wearing in the recent rainy-day photo, based on a short-term event."
  - "Ask what kind of toy Mochi usually loves, based on his long-term knowledge."
  - "Ask why Mochi had to visit the vet recently, based on a short-term event."
  - "Ask if Mochi enjoys going to crowded places like dog parks, based on his long-term preferences."
  - "Ask what Mochi was playing with this morning, based on a recent event."

# ===============================================
#          Hard Question Generation Drafts
# ===============================================

# These are "drafts" for generating hard questions.
# Each draft describes a question that requires reasoning to answer, with the key being to combine long-term attributes and short-term events in conflict.
# Note that the long-term attributes and short-term events needed to answer the question must be shown in the historical dialogue history
# Below are only 5 hard question example templates, but you need to prepare at least 6 hard questions
# Can be state identification questions, requiring identification of the current state and comparison with long-term state.
# Can be preference conflict questions, requiring recent preferences from history and comparison with long-term preferences.
# Counterfactual reasoning questions, requiring recent situations from history and long-term preferences for counterfactual reasoning.
hard_question:
  - "Pose a question that requires explaining why Mochi is eating wet food now. The user needs to combine the long-term knowledge that he hates wet food with the short-term event that he got sick and is on a vet-prescribed diet."
  - "Ask a 'what-if' question: If you offer Mochi his favorite salmon treat right now, would it be a good idea? The user must consider his long-term love for salmon against the short-term fact that he is sick and on a special diet."
  - "Create a state-recognition question. Provide an image of a Shiba Inu (Mochi) in a raincoat looking sad. Ask who it is and why he might be unhappy. The user must identify Mochi from his long-term features (if visible) and infer his unhappiness from his long-term hatred of rain combined with the short-term context of the photo."
  - "Pose a preference conflict question. Ask why Mochi is ignoring his beloved hedgehog toy for a bottle cap. The user should infer that this is likely a temporary interest due to novelty, contrasting the stable long-term preference with a fleeting short-term behavior."
  - "Create a recommendation question. Given that Mochi hates having his paws touched (long-term trait) but his nails are now too long (implied short-term problem), ask for advice on how to handle nail trimming. The answer should acknowledge the conflict and suggest solutions."

```