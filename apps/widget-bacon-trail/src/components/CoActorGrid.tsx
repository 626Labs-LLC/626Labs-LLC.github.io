import { Users } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import type { Actor, TrailStep } from '../types';
import { ITEMS_PER_PAGE } from '../types';
import { tmdbImageUrl } from '../services/tmdbService';
import { Pager } from './Pager';

interface Props {
  cast: Actor[];
  movieTitle: string;
  trail: TrailStep[];
  onPick: (actor: Actor) => void;
}

// Epic 4 — pick a co-actor from the film's cast to continue the chain. 3×3
// grid, paginated. Bacon is guaranteed not in this cast (Epic 3 already
// fired the win check if he was). Actors already in the trail are filtered
// out (not just disabled) so they don't take grid slots away from real
// next-step candidates.
export function CoActorGrid({ cast, movieTitle, trail, onPick }: Props) {
  const [page, setPage] = useState(0);

  const trailActorIds = useMemo(
    () => new Set(trail.filter((s): s is TrailStep & { kind: 'actor' } => s.kind === 'actor').map((s) => s.actor.id)),
    [trail]
  );

  const available = useMemo(() => cast.filter((a) => !trailActorIds.has(a.id)), [cast, trailActorIds]);

  const totalPages = Math.max(1, Math.ceil(available.length / ITEMS_PER_PAGE));

  // Reset page when the underlying cast prop changes (new movie).
  useEffect(() => {
    setPage(0);
  }, [cast]);

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

  const start = page * ITEMS_PER_PAGE;
  const pageItems = available.slice(start, start + ITEMS_PER_PAGE);

  return (
    <div className="btw-screen">
      <div className="btw-screen-header">
        <h3 className="btw-screen-lead">Pick a co-actor from {movieTitle}.</h3>
        <p className="btw-screen-sub">Kevin Bacon's not in this one. Find him in one of their films instead.</p>
      </div>

      <div className="btw-grid cols-3" role="group" aria-label={`Cast of ${movieTitle}`}>
        {pageItems.map((actor) => (
          <CoActorCard key={actor.id} actor={actor} onPick={onPick} />
        ))}
      </div>

      {totalPages > 1 && (
        <Pager page={page} totalPages={totalPages} onChange={setPage} ariaLabel="Cast pagination" />
      )}
    </div>
  );
}

function CoActorCard({ actor, onPick }: { actor: Actor; onPick: (a: Actor) => void }) {
  const imageUrl = tmdbImageUrl(actor.profilePath, 'w185');

  return (
    <button
      type="button"
      className="btw-card"
      onClick={() => onPick(actor)}
      aria-label={`Pick ${actor.name}`}
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
