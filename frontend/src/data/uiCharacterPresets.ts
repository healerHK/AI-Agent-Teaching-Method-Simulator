import type { StudentPersona } from '../types';

export const teacherAvatar = {
  name: 'Teacher',
  display_role: 'Human teacher',
  avatar_variant: 'teacher',
};

export const fallbackPersonas: StudentPersona[] = [
  {
    persona_id: 'high_achiever',
    name: 'Alex',
    display_role: 'High-achieving student',
    learning_profile: 'Usually answers quickly and explains reasoning.',
    misconception_bias: 'Low misconception; may dominate discussion.',
    avatar_variant: 'blue',
  },
  {
    persona_id: 'misconception_student',
    name: 'Mia',
    display_role: 'Misconception-heavy student',
    learning_profile: 'Often reveals useful conceptual misunderstandings.',
    misconception_bias: 'Confuses code lines with runtime repetitions.',
    avatar_variant: 'pink',
  },
  {
    persona_id: 'anxious_beginner',
    name: 'Sam',
    display_role: 'Anxious beginner',
    learning_profile: 'Needs slower scaffolding and reassurance.',
    misconception_bias: 'Unsure how loop variables update.',
    avatar_variant: 'green',
  },
  {
    persona_id: 'disengaged_student',
    name: 'Noah',
    display_role: 'Disengaged student',
    learning_profile: 'Answers briefly unless invited directly.',
    misconception_bias: 'May repeat terms without explanation.',
    avatar_variant: 'orange',
  },
  {
    persona_id: 'curious_student',
    name: 'Lina',
    display_role: 'Curious/distracted student',
    learning_profile: 'Asks extension questions and sometimes jumps ahead.',
    misconception_bias: 'May overgeneralise from one example.',
    avatar_variant: 'purple',
  },
];
