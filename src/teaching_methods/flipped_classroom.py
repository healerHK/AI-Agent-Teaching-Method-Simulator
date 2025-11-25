def run_flipped_classroom(student, teacher):
    # Phase 1: Pre-class self-learning
    student.absorb_instruction(clarity=0.4)  # lower clarity without teacher

    # Phase 2: Class activities
    for _ in range(2):
        teacher.run_activity(student, difficulty=0.4)

    # Student questions
    teacher.answer_questions(student)

    return student.get_state()
