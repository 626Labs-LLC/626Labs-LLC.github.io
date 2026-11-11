// Bacon confetti for the Kevin-Bacon-on-his-birthday result. Pure CSS
// strips, positions fixed per index so a render is deterministic (tests,
// screenshots). Decorative only: aria-hidden, and hidden outright under
// prefers-reduced-motion (see .btw-bacon-confetti in widget.css).

const STRIPS = 18;

export function BaconConfetti() {
  return (
    <div className="btw-bacon-confetti" aria-hidden="true" data-testid="bacon-confetti">
      {Array.from({ length: STRIPS }, (_, i) => {
        // Spread across the card, stagger the drop, vary the tumble.
        const left = (i * 37 + 11) % 96;
        const delay = (i * 173) % 1400;
        const duration = 2600 + ((i * 251) % 1400);
        const spin = i % 2 === 0 ? 1 : -1;
        return (
          <span
            key={i}
            className="btw-bacon-strip"
            style={
              {
                left: `${left}%`,
                animationDelay: `${delay}ms`,
                animationDuration: `${duration}ms`,
                '--btw-spin': spin,
              } as React.CSSProperties
            }
          />
        );
      })}
    </div>
  );
}
