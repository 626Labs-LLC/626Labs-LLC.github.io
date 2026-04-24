import { Users, Shuffle } from 'lucide-react';
import type { Actor } from '../types';
import { BIRTHDAY_GRID_SIZE } from '../types';
import { tmdbImageUrl } from '../services/tmdbService';
import { StatsLine } from './StatsLine';

interface Props {
  actors: Actor[];
  shardSize: number;
  onPick: (actor: Actor) => void;
  onShuffle: () => void;
}

// Epic 2 — pick starting birthday actor. Renders BIRTHDAY_GRID_SIZE cards
// (6 in a 3×2 layout). Shuffle button visible when the pool has > grid size.
export function BirthdayActorGrid({ actors, shardSize, onPick, onShuffle }: Props) {
  const canShuffle = shardSize > BIRTHDAY_GRID_SIZE;

  if (actors.length === 0) {
    return (
      <div className="btw-screen">
        <div className="btw-screen-header">
          <h3 className="btw-screen-lead">No birthday actors for today.</h3>
          <p className="btw-screen-sub">We'll have fresh ones tomorrow.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="btw-screen">
      <div className="btw-screen-header">
        <h3 className="btw-screen-lead">Who's born today?</h3>
        <p className="btw-screen-sub">Pick a starting actor. Find Kevin Bacon within six films.</p>
      </div>

      <div className="btw-grid cols-3" role="group" aria-label="Birthday actors">
        {actors.map((actor) => (
          <ActorCard key={actor.id} actor={actor} onPick={onPick} />
        ))}
      </div>

      {canShuffle && (
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <button type="button" className="btw-btn ghost" onClick={onShuffle}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <Shuffle size={14} aria-hidden="true" />
              <span>Different actors</span>
            </span>
          </button>
        </div>
      )}

      <StatsLine />
    </div>
  );
}

function ActorCard({ actor, onPick }: { actor: Actor; onPick: (a: Actor) => void }) {
  const imageUrl = tmdbImageUrl(actor.profilePath, 'w185');
  const year = actor.birthday ? actor.birthday.slice(0, 4) : null;

  return (
    <button
      type="button"
      className="btw-card"
      onClick={() => onPick(actor)}
      aria-label={`Pick ${actor.name}${year ? `, born ${year}` : ''}`}
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
        {year && <span className="btw-card-sub">Born {year}</span>}
      </div>
    </button>
  );
}

function hideOnError(e: React.SyntheticEvent<HTMLImageElement>) {
  e.currentTarget.style.display = 'none';
}
