import type { FormEvent } from 'react';

interface TeacherInputPanelProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled: boolean;
}

export function TeacherInputPanel({ value, onChange, onSubmit, disabled }: TeacherInputPanelProps) {
  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    onSubmit();
  }

  return (
    <form className="teacher-input pixel-panel" onSubmit={handleSubmit}>
      <label htmlFor="teacher-message">Teacher message</label>
      <textarea
        id="teacher-message"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Example: Before we run it, how many times will print(number) execute?"
        rows={3}
      />
      <button className="pixel-button" disabled={disabled || !value.trim()}>
        Send to class
      </button>
    </form>
  );
}
