from agents.student_agent import StudentAgent
from agents.teacher_agent import TeacherAgent
from teaching_methods.flipped_classroom import run_flipped_classroom
from teaching_methods.direct_instruction import run_direct_instruction

def run_simulation(method="flipped", student_name="Student A"):
    student = StudentAgent(student_name)
    teacher = TeacherAgent()

    if method == "flipped":
        final_state = run_flipped_classroom(student, teacher)
    else:
        final_state = run_direct_instruction(student, teacher)

    return {
        "student": student_name,
        "method": method,
        "final_state": final_state,
        "memory_history": student.memory.history
    }


# Example
if __name__ == "__main__":
    result = run_simulation("flipped")
    print(result)
