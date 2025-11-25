import random

class TeacherAgent:
    def __init__(self, name="Teacher", clarity=0.8, patience=0.7):
        self.name = name
        self.clarity = clarity        # affects instruction quality
        self.patience = patience      # affects whether students get extra help

    def deliver_instruction(self, student):
        effective_clarity = self.clarity * (0.8 + random.uniform(-0.1, 0.1))
        student.absorb_instruction(effective_clarity)

    def run_activity(self, student, difficulty=0.5):
        adjusted_difficulty = difficulty - (0.1 * self.patience)
        student.attempt_activity(adjusted_difficulty)

    def answer_questions(self, student):
        student.ask_question()
