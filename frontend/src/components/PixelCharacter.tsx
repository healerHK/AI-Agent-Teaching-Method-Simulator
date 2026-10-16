interface PixelCharacterProps {
  name: string;
  role: string;
  variant: string;
  active?: boolean;
}

export function PixelCharacter({ name, role, variant, active = false }: PixelCharacterProps) {
  return (
    <article className={`pixel-character ${variant} ${active ? 'active' : ''}`}>
      <div className="pixel-avatar" aria-hidden="true">
        <span className="pixel-hair" />
        <span className="pixel-face">
          <i />
          <i />
        </span>
        <span className="pixel-body" />
      </div>
      <div>
        <strong>{name}</strong>
        <small>{role}</small>
      </div>
    </article>
  );
}
