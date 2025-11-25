import random
import math
from agents.memory_module import MemoryModule


class StudentAgent:
    def __init__(self, name):
        self.name = name

        # --- Profile ---
        self.prior_knowledge = random.uniform(0.2, 0.7)
        self.learning_style = random.choice(["visual", "verbal", "social"])
        self.personality = {
            "openness": random.random(),
            "conscientiousness": random.random(),
            "extraversion": random.random(),
            "agreeableness": random.random(),
            "neuroticism": random.random(),
        }

        # Replace old memory with new module
   
        self.memory = MemoryModule()
        self.memory.knowledge = self.prior_knowledge  # initialize memory knowledge
        self.memory.misconceptions = random.uniform(0.3, 1.0)

        # --- State for metrics ---

        self.participated = False
        self.questions_asked = 0
        self.question_depth = random.uniform(0.1, 1.0)
        self.time_on_task = random.uniform(20, 50)
        self.cognitive_load = random.uniform(0.2, 0.7)

        self.pre_score = None
        self.post_score = None


    # Testing Functions

    def pre_test(self):
        self.pre_score = round(self.memory.knowledge * 100, 2)
        return self.pre_score

    def post_test(self):
        noise = random.uniform(-0.05, 0.1)
        self.post_score = round((self.memory.knowledge + noise) * 100, 2)
        return self.post_score


    # Learning Actions 

    def self_study(self):
        self.memory.update(
            knowledge_delta=random.uniform(0.05, 0.15),
            misconception_delta=-random.uniform(0.01, 0.05),
            engagement_delta=random.uniform(0.01, 0.05)
        )
        self.memory.log("Self-studied learning material")

    def attend_lecture(self):
        self.memory.update(
            knowledge_delta=random.uniform(0.03, 0.08),
            misconception_delta=-random.uniform(0.02, 0.06),
            engagement_delta=random.uniform(-0.02, 0.03)
        )
        self.memory.log("Attended teacher lecture")

    def ask_question(self):
        self.questions_asked += 1
        self.participated = True
        self.memory.update(
            knowledge_delta=random.uniform(0.01, 0.03),
            misconception_delta=-random.uniform(0.01, 0.03),
            engagement_delta=random.uniform(0.03, 0.08)
        )
        self.memory.log("Asked a question")

    def correct_misconception(self):
        self.memory.update(
            knowledge_delta=random.uniform(0.02, 0.06),
            misconception_delta=-random.uniform(0.05, 0.15),
            engagement_delta=0
        )
        self.memory.log("Misconception corrected")
