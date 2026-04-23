// Domain types + TMDB response types for the Bacon Trail widget.
// Per docs/spec.md > Data flow > State shape, these are the shapes the
// reducer + services + components all speak.

// ─── Domain types (camelCase, internal-facing) ───────────────────────

export interface Actor {
  id: number;
  name: string;
  profilePath: string | null;
  birthday?: string;
  popularity?: number;
  baconNumber?: number;
}

export interface Movie {
  id: number;
  title: string;
  posterPath: string | null;
  releaseYear: number | null;
  popularity?: number;
}

export type TrailStep =
  | { kind: 'actor'; actor: Actor }
  | { kind: 'movie'; movie: Movie; baconInCast: boolean };

export type Outcome = 'found' | 'out-of-films';

export type WidgetState =
  | { status: 'loading' }
  | { status: 'error'; message: string; retry: () => void }
  | {
      status: 'pick-actor';
      shard: Actor[]; // full day pool
      displayed: Actor[]; // current 6 visible
      poolIndex: number;
      trail: TrailStep[];
      filmCount: number;
    }
  | {
      status: 'pick-movie';
      subject: Actor;
      movies: Movie[];
      trail: TrailStep[];
      filmCount: number;
    }
  | {
      status: 'fetching-cast';
      subject: Actor;
      movie: Movie;
      trail: TrailStep[];
      filmCount: number;
    }
  | {
      status: 'pick-co-actor';
      subject: Actor;
      movie: Movie;
      cast: Actor[];
      trail: TrailStep[];
      filmCount: number;
    }
  | {
      status: 'result';
      outcome: Outcome;
      trail: TrailStep[];
      filmCount: number;
    };

// ─── Config (public API) ─────────────────────────────────────────────

export interface BaconTrailWidgetConfig {
  container: HTMLElement;
  theme?: 'dark' | 'light';
  brandColor?: string;
  brandLogo?: string;
  ctaUrl?: string;
  ctaLabel?: string;
  firebaseConfig?: null; // reserved, never used in v1
}

// ─── Shard schema (file on disk, public URL) ─────────────────────────

export interface BirthdayShard {
  date: string; // "MM-DD"
  actors: Actor[];
}

// ─── TMDB raw response types (minimal) ───────────────────────────────
// Only the fields the existing bacon-trail code actually consumes, per the
// Explore agent's audit of apps/bacon-trail/services/tmdbService.ts.

export interface TMDBPersonCreditsResponse {
  cast: Array<{
    id: number;
    title: string;
    poster_path: string | null;
    release_date?: string;
    popularity?: number;
  }>;
}

export interface TMDBMovieCastResponse {
  cast: Array<{
    id: number;
    name: string;
    character?: string;
    profile_path: string | null;
    popularity?: number;
    order?: number;
  }>;
}

// Kevin Bacon's TMDB person id. Used by baconCheck.ts; surfaced as a typed
// constant so tests + components can import the same source of truth.
export const KEVIN_BACON_TMDB_ID = 4724;

// Max films before a round ends without finding Bacon.
export const MAX_FILMS = 6;

// Grid sizing for the birthday actor pick screen.
export const BIRTHDAY_GRID_SIZE = 6;

// Top cast members shown per film.
export const CAST_GRID_SIZE = 15;

// Top movies shown per actor.
export const MOVIE_LIST_SIZE = 20;
