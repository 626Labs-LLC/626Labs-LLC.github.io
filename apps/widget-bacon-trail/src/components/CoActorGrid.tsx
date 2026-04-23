import { Users } from 'lucide-react';
import type { Actor, TrailStep } from '../types';
import { tmdbImageUrl } from '../services/tmdbService';

interface Props {
  cast: Actor[];
  movieTitle: string;
  trail: TrailStep[];
  onPick: (actor: Actor) => void;
}

// Epic 4 — pick a co-actor from the movie's cast to continue the chain.
// Bacon is already known not to be in this cast (Epic 3 would've fired the
// win), so no Bacon marker is shown. Actors already in the trail are
// disabled so the player can't walk in a loop.
export function CoActorGrid({ cast, movieTitle, trail, onPick }: Props) {
  const trailIds = new Set(
    trail.filter((s): s is TrailStep & { kind: 'actor' } => s.kind === 'actor').map((s) => s.actor.id)
  );

  const available = cast.filter((a) => !trailIds.has(a.id));

  if (available.length === 0) {
    return (
      <div className="btw-screen">
        <div className="btw-screen-header">
          <h3 className="btw-screen-lead">Everyone in this cast is already on your trail.</h3>
          <p className="btw-screen-sub">Go back and pick a different film.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="btw-screen">
      <div className="btw-screen-header">
        <h3 className="btw-screen-lead">Pick a co-actor from {movieTitle}.</h3>
        <p className="btw-screen-sub">Kevin Bacon's not in this one. Find him in one of their films instead.</p>
      </div>

      <div className="btw-grid cols-3" role="group" aria-label={`Cast of ${movieTitle}`}>
        {cast.map((actor) => {
          const inTrail = trailIds.has(actor.id);
          return <CoActorCard key={actor.id} actor={actor} disabled={inTrail} onPick={onPick} />;
        })}
      </div>
    </div>
  );
}

function CoActorCard({
  actor,
  disabled,
  onPick,
}: {
  actor: Actor;
  disabled: boolean;
  onPick: (a: Actor) => void;
}) {
  const imageUrl = tmdbImageUrl(actor.profilePath, 'w185');

  return (
    <button
      type="button"
      className="btw-card"
      disabled={disabled}
      onClick={() => onPick(actor)}
      aria-label={disabled ? `${actor.name} (already on trail)` : `Pick ${actor.name}`}
    >
      <div className="btw-card-image-wrap">
        {imageUrl ? (
          <img src={imageUrl} alt="" loading="lazy" onError={hideOnError} />
        ) : (
          <Users size={28} strokeWidth={1.75} aria-hidden="true" />
        )}
      </div>
      <div className="btw-card-meta">
        <span className="btw-card-title">{actor.name}</span>
      </div>
    </button>
  );
}

function hideOnError(e: React.SyntheticEvent<HTMLImageElement>) {
  e.currentTarget.style.display = 'none';
}
