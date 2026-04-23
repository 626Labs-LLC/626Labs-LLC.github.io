import {
  BIRTHDAY_GRID_SIZE,
  KEVIN_BACON_TMDB_ID,
  MAX_FILMS,
  type Actor,
  type Movie,
  type TrailStep,
  type WidgetState,
} from './types';
import { castIncludesBacon } from './services/baconCheck';

// ─── Actions ─────────────────────────────────────────────────────────

export type Action =
  | { type: 'SHARD_LOADED'; actors: Actor[] }
  | { type: 'ACTOR_PICKED'; actor: Actor }
  | { type: 'MOVIES_LOADED'; movies: Movie[] }
  | { type: 'MOVIE_PICKED'; movie: Movie }
  | { type: 'CAST_LOADED'; cast: Actor[] }
  | { type: 'CO_ACTOR_PICKED'; actor: Actor }
  | { type: 'SHUFFLE_ACTORS' }
  | { type: 'PLAY_AGAIN' }
  | { type: 'ERROR'; message: string; retry: () => void };

// ─── Initial state ───────────────────────────────────────────────────

export const initialState: WidgetState = { status: 'loading' };

// ─── Helpers ─────────────────────────────────────────────────────────

function sliceNextPool(
  shard: Actor[],
  poolIndex: number,
  size: number = BIRTHDAY_GRID_SIZE
): { displayed: Actor[]; poolIndex: number } {
  if (shard.length === 0) return { displayed: [], poolIndex: 0 };
  const start = poolIndex % shard.length;
  const end = start + size;
  const displayed = shard.slice(start, end);
  if (displayed.length < size && end > shard.length) {
    // wrap
    displayed.push(...shard.slice(0, end - shard.length));
  }
  return { displayed: displayed.slice(0, size), poolIndex: start };
}

function trailContainsActor(trail: TrailStep[], actorId: number): boolean {
  return trail.some((step) => step.kind === 'actor' && step.actor.id === actorId);
}

// ─── Reducer ─────────────────────────────────────────────────────────

export function reducer(state: WidgetState, action: Action): WidgetState {
  switch (action.type) {
    case 'SHARD_LOADED': {
      const { displayed, poolIndex } = sliceNextPool(action.actors, 0);
      return {
        status: 'pick-actor',
        shard: action.actors,
        displayed,
        poolIndex,
        trail: [],
        filmCount: 0,
      };
    }

    case 'SHUFFLE_ACTORS': {
      if (state.status !== 'pick-actor') return state;
      const { displayed, poolIndex } = sliceNextPool(
        state.shard,
        state.poolIndex + BIRTHDAY_GRID_SIZE
      );
      return { ...state, displayed, poolIndex };
    }

    case 'ACTOR_PICKED': {
      if (state.status !== 'pick-actor' && state.status !== 'pick-co-actor') return state;
      const trail: TrailStep[] = [...state.trail, { kind: 'actor', actor: action.actor }];
      return {
        status: 'pick-movie',
        subject: action.actor,
        movies: [], // filled by MOVIES_LOADED
        trail,
        filmCount: state.filmCount,
      };
    }

    case 'MOVIES_LOADED': {
      if (state.status !== 'pick-movie') return state;
      return { ...state, movies: action.movies };
    }

    case 'MOVIE_PICKED': {
      if (state.status !== 'pick-movie') return state;
      return {
        status: 'fetching-cast',
        subject: state.subject,
        movie: action.movie,
        trail: state.trail,
        filmCount: state.filmCount + 1,
      };
    }

    case 'CAST_LOADED': {
      if (state.status !== 'fetching-cast') return state;
      const baconInCast = castIncludesBacon(action.cast);
      const trail: TrailStep[] = [
        ...state.trail,
        { kind: 'movie', movie: state.movie, baconInCast },
      ];

      if (baconInCast) {
        // Append Kevin Bacon's actor card as the final trail step so the
        // "Your Path" viz ends on his portrait — the reward moment.
        const bacon = action.cast.find((a) => a.id === KEVIN_BACON_TMDB_ID);
        if (bacon) {
          trail.push({ kind: 'actor', actor: bacon });
        }
        return {
          status: 'result',
          outcome: 'found',
          trail,
          filmCount: state.filmCount,
        };
      }

      if (state.filmCount >= MAX_FILMS) {
        return {
          status: 'result',
          outcome: 'out-of-films',
          trail,
          filmCount: state.filmCount,
        };
      }

      return {
        status: 'pick-co-actor',
        subject: state.subject,
        movie: state.movie,
        cast: action.cast,
        trail,
        filmCount: state.filmCount,
      };
    }

    case 'CO_ACTOR_PICKED': {
      if (state.status !== 'pick-co-actor') return state;
      if (trailContainsActor(state.trail, action.actor.id)) return state;
      const trail: TrailStep[] = [...state.trail, { kind: 'actor', actor: action.actor }];
      return {
        status: 'pick-movie',
        subject: action.actor,
        movies: [],
        trail,
        filmCount: state.filmCount,
      };
    }

    case 'PLAY_AGAIN': {
      // Caller will re-fetch a fresh shard; we go back to loading so the
      // widget shows its initial UI during that fetch.
      return { status: 'loading' };
    }

    case 'ERROR': {
      return { status: 'error', message: action.message, retry: action.retry };
    }

    default: {
      // Exhaustiveness guard — TS errors here if a new action type is added
      // but not handled.
      const _exhaustive: never = action;
      void _exhaustive;
      return state;
    }
  }
}
