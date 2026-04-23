import type {
  Actor,
  Movie,
  TMDBMovieCastResponse,
  TMDBPersonCreditsResponse,
} from '../types';

const TMDB_API_KEY = import.meta.env.VITE_TMDB_API_KEY as string | undefined;
const TMDB_BASE_URL = 'https://api.themoviedb.org/3';
const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p';
const DEFAULT_IMAGE_SIZE = 'w185';

// Retry wrapper — 2 attempts with exponential backoff (500ms, 1s), then
// surfaces the error to the caller. Matches spec.md > Data flow > HTTP
// endpoints retry policy.
async function fetchWithRetry(url: string, attempts = 2): Promise<Response> {
  let lastError: unknown;
  for (let attempt = 0; attempt <= attempts; attempt++) {
    try {
      const res = await fetch(url, { headers: { Accept: 'application/json' } });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      return res;
    } catch (err) {
      lastError = err;
      if (attempt < attempts) {
        const delayMs = 500 * Math.pow(2, attempt);
        await new Promise((resolve) => setTimeout(resolve, delayMs));
      }
    }
  }
  throw lastError;
}

function assertKey(): string {
  if (!TMDB_API_KEY) {
    throw new Error(
      '[widget-bacon-trail] VITE_TMDB_API_KEY is missing. Set it in .env.local (dev) or the CI secret (prod).'
    );
  }
  return TMDB_API_KEY;
}

// Fetch an actor's movie credits, return top N sorted by popularity desc.
// Default limit is 45 = 5 pages of 9 in the UI's paginated grid. Kept
// generous because TMDB's `popularity` field can drop classic titles
// (e.g., X-Men: First Class) below newer lesser ones.
// `GET /person/{id}/movie_credits`.
export async function fetchMovieCreditsForActor(
  actorId: number,
  limit = 45
): Promise<Movie[]> {
  const key = assertKey();
  const url = `${TMDB_BASE_URL}/person/${actorId}/movie_credits?api_key=${key}`;
  const res = await fetchWithRetry(url);
  const body = (await res.json()) as TMDBPersonCreditsResponse;

  const movies: Movie[] = body.cast.map((m) => ({
    id: m.id,
    title: m.title,
    posterPath: m.poster_path,
    releaseYear: m.release_date ? Number.parseInt(m.release_date.slice(0, 4), 10) : null,
    popularity: m.popularity,
    voteCount: m.vote_count,
  }));

  // Blend popularity with vote_count so low-vote derivative entries
  // (rereleases, 35mm specials, documentaries) sink below legit titles.
  // Score: popularity × log(voteCount + 1). A film with 0 votes scores 0
  // regardless of TMDB's popularity rating; a popular well-known film
  // with thousands of votes ranks correctly.
  const score = (m: Movie) =>
    (m.popularity ?? 0) * Math.log(1 + Math.max(0, m.voteCount ?? 0));
  movies.sort((a, b) => score(b) - score(a));
  return movies.slice(0, limit);
}

// Fetch a movie's cast, return top N by billing order.
// Default 27 = 3 pages of 9 in the UI's paginated grid.
// `GET /movie/{id}/credits`.
export async function fetchCastForMovie(movieId: number, limit = 27): Promise<Actor[]> {
  const key = assertKey();
  const url = `${TMDB_BASE_URL}/movie/${movieId}/credits?api_key=${key}`;
  const res = await fetchWithRetry(url);
  const body = (await res.json()) as TMDBMovieCastResponse;

  // TMDB returns cast in billing-order already (order field). If `order` is
  // present we trust it; otherwise fall back to input order.
  const sorted = [...body.cast].sort(
    (a, b) => (a.order ?? Number.MAX_SAFE_INTEGER) - (b.order ?? Number.MAX_SAFE_INTEGER)
  );

  return sorted.slice(0, limit).map((a) => ({
    id: a.id,
    name: a.name,
    profilePath: a.profile_path,
    popularity: a.popularity,
  }));
}

// Build a full TMDB image URL from a path. Null-safe — returns null if the
// path was null (caller renders an initials-avatar fallback).
export function tmdbImageUrl(path: string | null, size: string = DEFAULT_IMAGE_SIZE): string | null {
  if (!path) return null;
  return `${TMDB_IMAGE_BASE}/${size}${path}`;
}
