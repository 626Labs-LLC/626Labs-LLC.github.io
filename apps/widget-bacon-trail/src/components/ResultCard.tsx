import { CheckCircle2, Clock } from 'lucide-react';
import type { Outcome, TrailStep } from '../types';
import { displayBaconNumber } from '../lib/baconNumber';
import { BaconConfetti } from './BaconConfetti';
import { TrailBreadcrumb } from './TrailBreadcrumb';

interface Props {
  outcome: Outcome;
  filmCount: number;
  trail: TrailStep[];
  ctaUrl: string;
  ctaLabel: string;
  onPlayAgain: () => void;
  baconBirthday?: boolean;
}

// Epic 5 — closing moment. `--success` alone for the found state (no
// `--warning` glow per PRD decision C). `--danger` kept tasteful for
// out-of-films. Always shows the walked trail + two CTAs.
export function ResultCard({ outcome, filmCount, trail, ctaUrl, ctaLabel, onPlayAgain, baconBirthday = false }: Props) {
  const found = outcome === 'found';

  if (baconBirthday) {
    // Kevin Bacon picked on his own birthday: the trail is just him.
    return (
      <div className="btw-result is-found is-bacon-birthday" role="status" aria-live="polite">
        <BaconConfetti />
        <CheckCircle2 size={42} strokeWidth={1.5} className="btw-result-icon found" aria-hidden="true" />
        <h3 className="btw-result-headline">
          You found Kevin Bacon in <span className="count">0</span> films.
        </h3>
        <p className="btw-result-sub">Bacon number 0. Happy birthday, Kevin.</p>
        <TrailBreadcrumb trail={trail} />
        <div className="btw-result-ctas">
          <button type="button" className="btw-btn primary" onClick={onPlayAgain}>
            Play again
          </button>
          <a className="btw-btn ghost" href={ctaUrl}>
            {ctaLabel}
          </a>
        </div>
      </div>
    );
  }

  // The starting actor is always trail[0]; filmCount is the path's length.
  const start = trail[0]?.kind === 'actor' ? trail[0].actor : null;
  const line = start
    ? displayBaconNumber({ stored: start.baconNumber, won: found, steps: filmCount })
    : { baconNumber: null, shortestRoute: false };

  return (
    <div className={`btw-result ${found ? 'is-found' : 'is-miss'}`} role="status" aria-live="polite">
      {found ? (
        <CheckCircle2 size={42} strokeWidth={1.5} className="btw-result-icon found" aria-hidden="true" />
      ) : (
        <Clock size={42} strokeWidth={1.5} className="btw-result-icon miss" aria-hidden="true" />
      )}

      {found ? (
        <h3 className="btw-result-headline">
          You found Bacon in <span className="count">{filmCount}</span> film{filmCount === 1 ? '' : 's'}.
        </h3>
      ) : (
        <h3 className="btw-result-headline">Didn't find Bacon in 6 films. Try a different starting actor?</h3>
      )}

      {start && line.baconNumber !== null && (
        <p className="btw-result-sub" data-testid="bacon-number-line">
          {start.name} has a Bacon number of {line.baconNumber}.
          {line.shortestRoute && <span className="btw-result-shortest"> That's the shortest route.</span>}
        </p>
      )}

      <TrailBreadcrumb trail={trail} />

      <div className="btw-result-ctas">
        <button type="button" className="btw-btn primary" onClick={onPlayAgain}>
          Play again
        </button>
        <a className="btw-btn ghost" href={ctaUrl}>
          {ctaLabel}
        </a>
      </div>
    </div>
  );
}
