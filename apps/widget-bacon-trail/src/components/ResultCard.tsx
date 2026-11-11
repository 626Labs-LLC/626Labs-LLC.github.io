import { CheckCircle2, Clock } from 'lucide-react';
import type { Outcome, TrailStep } from '../types';
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
