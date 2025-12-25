from pathlib import Path

import yaml


class QASystem:
    def __init__(self, model_id: str):
        self.questions = self.load_question_for_all_concepts()
        self.cnt = 0

    def load_question_single(self, concept_id: str, q: dict, difficulty: str = "unknown"):
        qid = q["id"]
        question = q["question"]
        ideal_answer = q["evaluation_criteria"]["ideal_answer"]
        key_points = q["evaluation_criteria"]["key_points"]
        options = q["options"]
        options_answer = q["answer"]
        img_path = f"data/concept/{concept_id}/img/{q['image_id']}.png"
        return {
            "qid": qid,
            "concept_id": concept_id,
            "question": question,
            "ideal_answer": ideal_answer,
            "key_points": key_points,
            "img_path": img_path,
            "options": options,
            "options_answer": options_answer,
            "difficulty": difficulty,
        }

    def load_question_by_concept(self, concept_id: str):
        easy_question_path = Path("data/concept") / concept_id / "easy_question.yaml"
        hard_question_path = Path("data/concept") / concept_id / "hard_question.yaml"

        all_questions = []

        # Load easy questions
        if easy_question_path.exists():
            try:
                with open(easy_question_path, "r", encoding="utf-8") as f:
                    easy_questions = yaml.load(f, Loader=yaml.SafeLoader)
                if easy_questions:
                    all_questions.extend([self.load_question_single(concept_id, q, "easy") for q in easy_questions])
            except (FileNotFoundError, yaml.YAMLError, IOError) as e:
                print(f"Error loading easy questions for concept {concept_id}: {e}")

        # Load hard questions
        if hard_question_path.exists():
            try:
                with open(hard_question_path, "r", encoding="utf-8") as f:
                    hard_questions = yaml.load(f, Loader=yaml.SafeLoader)
                if hard_questions:
                    all_questions.extend([self.load_question_single(concept_id, q, "hard") for q in hard_questions])
            except (FileNotFoundError, yaml.YAMLError, IOError) as e:
                print(f"Error loading hard questions for concept {concept_id}: {e}")

        return all_questions

    def load_question_for_all_concepts(self):
        concepts_path = Path("data/concept")
        if not concepts_path.exists():
            print(f"Concepts directory not found: {concepts_path}")
            return []

        concepts = concepts_path.iterdir()
        questions = []
        for concept in concepts:
            if concept.is_dir():  # Only process directories
                questions.extend(self.load_question_by_concept(concept.name))
        return questions



    def __iter__(self):
        self.cnt = 0  # FIX: Reset counter to make iterator reusable
        return self

    def __next__(self):
        if self.cnt >= len(self.questions):
            raise StopIteration
        question = self.questions[self.cnt]
        self.cnt += 1
        return question

    def reset(self):
        """Reset the iterator to allow re-iteration"""
        self.cnt = 0
