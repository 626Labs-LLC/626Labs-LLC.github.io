// Round generator — the widget edition of WSYATM's getTaglineSession.
// The pool is injected (fetched at runtime from pool.json, which carries
// curated classics plus a weekly TMDB sweep); all the variety (round
// pick, decoys, poster order) is local shuffling, as it always was.
import { shuffle, posterUrl, type PoolEntry } from '../shared/data';

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

function toPoster(e: PoolEntry): Poster {
  return { movieId: e.id, title: e.title, posterUrl: posterUrl(e.posterPath) };
}

export function generateRounds(pool: readonly PoolEntry[], totalRounds = 8): Round[] {
  // Curated classics are the spine (~5 of 8 rounds); the TMDB sweep fills
  // the rest so fresh titles keep showing up. Either side backfills the
  // other when short.
  const curated = shuffle(pool.filter((e) => e.source === 'curated'));
  const swept = shuffle(pool.filter((e) => e.source !== 'curated'));
  const curatedShare = Math.min(curated.length, Math.ceil(totalRounds * 0.6));
  const answers = [
    ...curated.slice(0, curatedShare),
    ...swept,
    ...curated.slice(curatedShare),
  ].slice(0, totalRounds);
  const rounds: Round[] = [];

  for (const answer of shuffle(answers)) {
    const decoys = shuffle(
      // A same-franchise decoy would make "With great power…" a coin flip
      // between Spider-Man and Deadpool on text alone — that ambiguity is
      // the fun, so no franchise filtering on purpose.
      pool.filter((e) => e.id !== answer.id)
    ).slice(0, POSTERS_PER_ROUND - 1);
    rounds.push({
      tagline: answer.tagline,
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
