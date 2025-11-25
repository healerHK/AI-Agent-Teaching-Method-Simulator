def run_direct_instruction(student, teacher):
    # Phase 1: Teacher gives clear instruction
    teacher.deliver_instruction(student)

    # Phase 2: Guided activity
    teacher.run_activity(student, difficulty=0.5)

    # Phase 3: Q&A
    teacher.answer_questions(student)

    return student.get_state()
