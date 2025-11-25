
class LearningEnvironment:
    def __init__(self, students, teacher):
        self.students = students
        self.teacher = teacher

    def run_flipped_classroom(self):
        """1. Pre-class video  2. In-class activity"""

        # Step 1: Students watch at home
        for s in self.students:
            s.watch_video()

        # Step 2: In-class session
        for s in self.students:
            self.teacher.conduct_activity(s)

    def run_direct_instruction(self):
        """Teacher leads lecture, less student autonomy."""
        for s in self.students:
            self.teacher.conduct_activity(s)
