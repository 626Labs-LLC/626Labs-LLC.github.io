import { Film, Users } from 'lucide-react';
import { KEVIN_BACON_TMDB_ID, type TrailStep } from '../types';
import { tmdbImageUrl } from '../services/tmdbService';

interface Props {
  trail: TrailStep[];
}

// Two-row "Your Path" layout. Films live on the top row, actors on the
// bottom row, each placed in a grid column per step so the chain reads
// left-to-right with a dashed connector between them.
//
// Shape:
//   row 1 (top):    [     ][  F1  ][      ][  F2  ][      ][  F3  ]
//   row 2 (bottom): [  A0 ][      ][  A1  ][      ][  A2  ][      ]
export function TrailBreadcrumb({ trail }: Props) {
  if (trail.length === 0) return null;

  return (
    <section className="btw-trail" aria-label="Your path">
      <div className="btw-trail-head">
        <span className="btw-trail-label">Your Path</span>
      </div>
      <div
        className="btw-trail-grid"
        style={{ gridTemplateColumns: `repeat(${trail.length}, minmax(56px, 1fr))` }}
      >
        {trail.map((step, i) => (
          <StepCell key={`${step.kind}-${stepId(step)}-${i}`} step={step} column={i + 1} />
        ))}
        {/* Dashed connector behind the cells */}
        <span className="btw-trail-connector" aria-hidden="true" />
      </div>
    </section>
  );
}

function stepId(step: TrailStep): number {
  return step.kind === 'actor' ? step.actor.id : step.movie.id;
}

function StepCell({ step, column }: { step: TrailStep; column: number }) {
  const isActor = step.kind === 'actor';
  const isBaconFilm = !isActor && step.baconInCast;
  const isBaconActor = isActor && step.actor.id === KEVIN_BACON_TMDB_ID;
  const isBacon = isBaconFilm || isBaconActor;

  const imageUrl = isActor
    ? tmdbImageUrl(step.actor.profilePath, 'w92')
    : tmdbImageUrl(step.movie.posterPath, 'w92');
  const label = isActor ? step.actor.name : step.movie.title;

  return (
    <div
      className={`btw-trail-cell ${isActor ? 'actor' : 'movie'}${isBacon ? ' is-bacon' : ''}`}
      style={{ gridColumn: column, gridRow: isActor ? 2 : 1 }}
    >
      <div className={`btw-trail-thumb ${isActor ? 'actor' : 'movie'}`}>
        {imageUrl ? (
          <img src={imageUrl} alt="" loading="lazy" onError={hideOnError} />
        ) : isActor ? (
          <Users size={14} aria-hidden="true" />
        ) : (
          <Film size={14} aria-hidden="true" />
        )}
      </div>
      <span className="btw-trail-label-text" title={label}>
        {truncate(label, 12)}
      </span>
    </div>
  );
}

function hideOnError(e: React.SyntheticEvent<HTMLImageElement>) {
  e.currentTarget.style.display = 'none';
}

function truncate(s: string, n: number): string {
  return s.length > n ? `${s.slice(0, n - 1)}…` : s;
}
