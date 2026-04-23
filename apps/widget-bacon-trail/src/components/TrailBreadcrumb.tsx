import { ChevronRight, Film, Users } from 'lucide-react';
import type { TrailStep } from '../types';
import { tmdbImageUrl } from '../services/tmdbService';

interface Props {
  trail: TrailStep[];
}

// Horizontally-scrolling breadcrumb of the walk so far. Each step is a
// chip; the film step that contains Bacon gets the success-color treatment.
export function TrailBreadcrumb({ trail }: Props) {
  if (trail.length === 0) return null;

  return (
    <nav className="btw-trail" aria-label="Bacon trail">
      {trail.map((step, i) => (
        <StepChip key={`${step.kind}-${stepId(step)}-${i}`} step={step} isLast={i === trail.length - 1} />
      ))}
    </nav>
  );
}

function stepId(step: TrailStep): number {
  return step.kind === 'actor' ? step.actor.id : step.movie.id;
}

function StepChip({ step, isLast }: { step: TrailStep; isLast: boolean }) {
  const isBacon = step.kind === 'movie' && step.baconInCast;
  const imageUrl =
    step.kind === 'actor' ? tmdbImageUrl(step.actor.profilePath, 'w92') : tmdbImageUrl(step.movie.posterPath, 'w92');
  const label = step.kind === 'actor' ? step.actor.name : step.movie.title;

  return (
    <>
      <span className={`btw-trail-step${isBacon ? ' is-bacon' : ''}`}>
        {imageUrl ? (
          <img className="btw-trail-thumb" src={imageUrl} alt="" loading="lazy" onError={hideOnError} />
        ) : (
          <span className="btw-trail-thumb" aria-hidden="true" style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
            {step.kind === 'actor' ? <Users size={14} /> : <Film size={14} />}
          </span>
        )}
        <span>{truncate(label, 18)}</span>
      </span>
      {!isLast && <ChevronRight size={14} className="btw-trail-sep" aria-hidden="true" />}
    </>
  );
}

function hideOnError(e: React.SyntheticEvent<HTMLImageElement>) {
  e.currentTarget.style.display = 'none';
}

function truncate(s: string, n: number): string {
  return s.length > n ? `${s.slice(0, n - 1)}…` : s;
}
