import { describe, it, expect } from 'vitest';
import { reducer, initialState, type Action } from '../state';
import { BIRTHDAY_GRID_SIZE, KEVIN_BACON_TMDB_ID, MAX_FILMS, type Actor, type Movie, type WidgetState } from '../types';

const mkActor = (id: number, name = `Actor ${id}`): Actor => ({
  id,
  name,
  profilePath: null,
  popularity: 1,
});

const mkMovie = (id: number, title = `Film ${id}`): Movie => ({
  id,
  title,
  posterPath: null,
  releaseYear: 2000,
  popularity: 1,
});

function run(state: WidgetState, actions: Action[]): WidgetState {
  return actions.reduce((s, a) => reducer(s, a), state);
}

describe('reducer', () => {
  describe('initial state', () => {
    it('starts in loading', () => {
      expect(initialState.status).toBe('loading');
    });
  });

  describe('SHARD_LOADED', () => {
    it('transitions loading → pick-actor and slices the pool', () => {
      const actors = Array.from({ length: 10 }, (_, i) => mkActor(i + 1));
      const next = reducer(initialState, { type: 'SHARD_LOADED', actors });
      expect(next.status).toBe('pick-actor');
      if (next.status === 'pick-actor') {
        expect(next.shard).toHaveLength(10);
        expect(next.displayed).toHaveLength(BIRTHDAY_GRID_SIZE);
        expect(next.displayed[0]?.id).toBe(1);
        expect(next.trail).toEqual([]);
        expect(next.filmCount).toBe(0);
      }
    });

    it('handles a shard with fewer actors than grid size', () => {
      const actors = [mkActor(1), mkActor(2), mkActor(3)];
      const next = reducer(initialState, { type: 'SHARD_LOADED', actors });
      if (next.status === 'pick-actor') {
        expect(next.displayed.length).toBeLessThanOrEqual(BIRTHDAY_GRID_SIZE);
      }
    });

    it('handles an empty shard gracefully', () => {
      const next = reducer(initialState, { type: 'SHARD_LOADED', actors: [] });
      if (next.status === 'pick-actor') {
        expect(next.displayed).toEqual([]);
        expect(next.shard).toEqual([]);
      }
    });
  });

  describe('SHUFFLE_ACTORS', () => {
    it('advances poolIndex and shows the next 6', () => {
      const actors = Array.from({ length: 12 }, (_, i) => mkActor(i + 1));
      const loaded = reducer(initialState, { type: 'SHARD_LOADED', actors });
      const shuffled = reducer(loaded, { type: 'SHUFFLE_ACTORS' });
      if (shuffled.status === 'pick-actor') {
        expect(shuffled.displayed[0]?.id).toBe(7); // shifted by 6
      }
    });

    it('wraps when reaching the end of the pool', () => {
      const actors = Array.from({ length: 8 }, (_, i) => mkActor(i + 1));
      const loaded = reducer(initialState, { type: 'SHARD_LOADED', actors });
      // After 2 shuffles (12 total displayed), we should wrap
      const s1 = reducer(loaded, { type: 'SHUFFLE_ACTORS' });
      const s2 = reducer(s1, { type: 'SHUFFLE_ACTORS' });
      if (s2.status === 'pick-actor') {
        expect(s2.displayed.length).toBe(BIRTHDAY_GRID_SIZE);
      }
    });

    it('is a no-op from non-pick-actor states', () => {
      const same = reducer(initialState, { type: 'SHUFFLE_ACTORS' });
      expect(same).toBe(initialState);
    });
  });

  describe('ACTOR_PICKED → pick-movie', () => {
    it('adds actor to trail and transitions', () => {
      const actor = mkActor(42, 'Harvey Keitel');
      const actors = [actor, mkActor(1)];
      const loaded = reducer(initialState, { type: 'SHARD_LOADED', actors });
      const picked = reducer(loaded, { type: 'ACTOR_PICKED', actor });
      expect(picked.status).toBe('pick-movie');
      if (picked.status === 'pick-movie') {
        expect(picked.subject.id).toBe(42);
        expect(picked.trail).toHaveLength(1);
        expect(picked.trail[0]).toEqual({ kind: 'actor', actor });
        expect(picked.filmCount).toBe(0);
        expect(picked.movies).toEqual([]);
      }
    });
  });

  describe('MOVIES_LOADED', () => {
    it('hydrates the movies array', () => {
      const actor = mkActor(42);
      const loaded = run(initialState, [
        { type: 'SHARD_LOADED', actors: [actor] },
        { type: 'ACTOR_PICKED', actor },
      ]);
      const withMovies = reducer(loaded, {
        type: 'MOVIES_LOADED',
        movies: [mkMovie(1), mkMovie(2)],
      });
      if (withMovies.status === 'pick-movie') {
        expect(withMovies.movies).toHaveLength(2);
      }
    });
  });

  describe('MOVIE_PICKED → fetching-cast', () => {
    it('increments filmCount and transitions', () => {
      const actor = mkActor(42);
      const movie = mkMovie(100, 'Pulp Fiction');
      const loaded = run(initialState, [
        { type: 'SHARD_LOADED', actors: [actor] },
        { type: 'ACTOR_PICKED', actor },
        { type: 'MOVIES_LOADED', movies: [movie] },
      ]);
      const fetching = reducer(loaded, { type: 'MOVIE_PICKED', movie });
      expect(fetching.status).toBe('fetching-cast');
      if (fetching.status === 'fetching-cast') {
        expect(fetching.filmCount).toBe(1);
        expect(fetching.movie.id).toBe(100);
      }
    });
  });

  describe('CAST_LOADED — Bacon check', () => {
    const setup = (filmCount = 1) => {
      const actor = mkActor(42);
      const movie = mkMovie(100);
      return run(initialState, [
        { type: 'SHARD_LOADED', actors: [actor] },
        { type: 'ACTOR_PICKED', actor },
        { type: 'MOVIES_LOADED', movies: [movie] },
        ...(filmCount > 1
          ? Array.from({ length: filmCount - 1 }, (_, i) => [
              { type: 'MOVIE_PICKED' as const, movie: mkMovie(200 + i) },
              { type: 'CAST_LOADED' as const, cast: [mkActor(300 + i)] },
              { type: 'CO_ACTOR_PICKED' as const, actor: mkActor(300 + i) },
              { type: 'MOVIES_LOADED' as const, movies: [mkMovie(400 + i)] },
            ]).flat()
          : []),
        { type: 'MOVIE_PICKED', movie },
      ]);
    };

    it('transitions to result=found when Bacon is in cast', () => {
      const state = setup(1);
      const bacon = mkActor(KEVIN_BACON_TMDB_ID, 'Kevin Bacon');
      const next = reducer(state, {
        type: 'CAST_LOADED',
        cast: [mkActor(1), bacon],
      });
      expect(next.status).toBe('result');
      if (next.status === 'result') {
        expect(next.outcome).toBe('found');
        expect(next.filmCount).toBe(1);
        // Trail ends on Kevin Bacon's actor card, not on the winning film.
        const last = next.trail[next.trail.length - 1];
        expect(last?.kind).toBe('actor');
        if (last?.kind === 'actor') {
          expect(last.actor.id).toBe(KEVIN_BACON_TMDB_ID);
        }
      }
    });

    it('transitions to pick-co-actor when no Bacon and films < 6', () => {
      const state = setup(1);
      const next = reducer(state, {
        type: 'CAST_LOADED',
        cast: [mkActor(1), mkActor(2)],
      });
      expect(next.status).toBe('pick-co-actor');
    });

    it('transitions to result=out-of-films when filmCount hits 6 without Bacon', () => {
      // Film counter = 6 before picking; CAST_LOADED checks against MAX_FILMS.
      // Build to filmCount=6 via repeated MOVIE_PICKED actions.
      const actor = mkActor(42);
      let s: WidgetState = run(initialState, [
        { type: 'SHARD_LOADED', actors: [actor] },
        { type: 'ACTOR_PICKED', actor },
        { type: 'MOVIES_LOADED', movies: [mkMovie(1)] },
      ]);
      // Cycle until filmCount reaches MAX_FILMS
      for (let i = 0; i < MAX_FILMS; i++) {
        s = reducer(s, { type: 'MOVIE_PICKED', movie: mkMovie(100 + i) });
        if (s.status === 'fetching-cast' && s.filmCount < MAX_FILMS) {
          s = reducer(s, { type: 'CAST_LOADED', cast: [mkActor(200 + i)] });
          if (s.status === 'pick-co-actor') {
            s = reducer(s, { type: 'CO_ACTOR_PICKED', actor: mkActor(300 + i) });
            s = reducer(s, { type: 'MOVIES_LOADED', movies: [mkMovie(400 + i)] });
          }
        }
      }
      // Now the 6th CAST_LOADED should hit the out-of-films branch if no Bacon
      if (s.status === 'fetching-cast') {
        expect(s.filmCount).toBe(MAX_FILMS);
        const final = reducer(s, { type: 'CAST_LOADED', cast: [mkActor(999)] });
        expect(final.status).toBe('result');
        if (final.status === 'result') {
          expect(final.outcome).toBe('out-of-films');
        }
      }
    });
  });

  describe('CO_ACTOR_PICKED', () => {
    it('adds co-actor to trail and transitions to pick-movie', () => {
      const actor = mkActor(42);
      const coActor = mkActor(50, 'Samuel L. Jackson');
      const state = run(initialState, [
        { type: 'SHARD_LOADED', actors: [actor] },
        { type: 'ACTOR_PICKED', actor },
        { type: 'MOVIES_LOADED', movies: [mkMovie(1)] },
        { type: 'MOVIE_PICKED', movie: mkMovie(1) },
        { type: 'CAST_LOADED', cast: [coActor] },
      ]);
      const picked = reducer(state, { type: 'CO_ACTOR_PICKED', actor: coActor });
      expect(picked.status).toBe('pick-movie');
      if (picked.status === 'pick-movie') {
        expect(picked.subject.id).toBe(50);
        expect(picked.trail).toHaveLength(3); // original actor, movie, co-actor
      }
    });

    it('is a no-op when co-actor already in trail (prevents loops)', () => {
      const actor = mkActor(42);
      const state = run(initialState, [
        { type: 'SHARD_LOADED', actors: [actor] },
        { type: 'ACTOR_PICKED', actor },
        { type: 'MOVIES_LOADED', movies: [mkMovie(1)] },
        { type: 'MOVIE_PICKED', movie: mkMovie(1) },
        { type: 'CAST_LOADED', cast: [actor] }, // trail already contains actor 42
      ]);
      const same = reducer(state, { type: 'CO_ACTOR_PICKED', actor });
      expect(same).toBe(state);
    });
  });

  describe('PLAY_AGAIN', () => {
    it('resets to loading from any state', () => {
      const end: WidgetState = {
        status: 'result',
        outcome: 'found',
        trail: [],
        filmCount: 3,
      };
      const next = reducer(end, { type: 'PLAY_AGAIN' });
      expect(next.status).toBe('loading');
    });
  });

  describe('ERROR', () => {
    it('transitions to error with message + retry closure', () => {
      const retry = () => {};
      const next = reducer(initialState, {
        type: 'ERROR',
        message: 'Network down',
        retry,
      });
      expect(next.status).toBe('error');
      if (next.status === 'error') {
        expect(next.message).toBe('Network down');
        expect(next.retry).toBe(retry);
      }
    });
  });
});
