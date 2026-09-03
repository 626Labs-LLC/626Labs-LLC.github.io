// Round generator — the widget edition of WSYATM's getTaglineSession.
// The server built its pool from TMDB popular movies daily; the hub embed
// draws from the shared roster's curated classic taglines instead, so it
// needs no backend, no key, and no cache. All the variety (round pick,
// decoys, poster order) was always local shuffling — preserved here.
import { MOVIES, shuffle, type Movie } from '../shared/movies';

export type Poster = {
  movieId: string;
  title: string;
  posterUrl: string;
};

export type Round = {
  tagline: string;
  correctMovieId: string;
  posters: Poster[];
};

const POSTERS_PER_ROUND = 4;

function toPoster(mv: Movie): Poster {
  return { movieId: mv.id, title: mv.title, posterUrl: mv.posterUrl };
}

export function generateRounds(totalRounds = 8): Round[] {
  const eligible = shuffle(
    MOVIES.filter((mv) => mv.tagline && mv.posterUrl)
  );
  const decoyStock = MOVIES.filter((mv) => mv.posterUrl);
  const rounds: Round[] = [];

  for (const answer of eligible.slice(0, totalRounds)) {
    const decoys = shuffle(
      // A same-franchise decoy would make "With great power…" a coin
      // flip between Spider-Man and Deadpool on text alone — that
      // ambiguity is the fun, so no franchise filtering on purpose.
      decoyStock.filter((mv) => mv.id !== answer.id)
    ).slice(0, POSTERS_PER_ROUND - 1);
    rounds.push({
      tagline: answer.tagline!,
      correctMovieId: answer.id,
      posters: shuffle([toPoster(answer), ...decoys.map(toPoster)]),
    });
  }

  return rounds;
}

/** Points by wrong taps this round — same ladder the WSYATM server used. */
export function pointsFor(wrongTaps: number): number {
  return wrongTaps === 0 ? 10 : wrongTaps === 1 ? 5 : 2;
}
