import { useCallback, useEffect, useReducer, useRef } from 'react';
import { BirthdayActorGrid } from './components/BirthdayActorGrid';
import { CoActorGrid } from './components/CoActorGrid';
import { ErrorCard } from './components/ErrorCard';
import { FilmCounter } from './components/FilmCounter';
import { MovieList } from './components/MovieList';
import { ResultBanner } from './components/ResultBanner';
import { ResultCard } from './components/ResultCard';
import { SkeletonCard } from './components/SkeletonCard';
import { TrailBreadcrumb } from './components/TrailBreadcrumb';
import { initialState, reducer, type Action } from './state';
import { fetchCastForMovie, fetchMovieCreditsForActor } from './services/tmdbService';
import { fetchTodayShard } from './services/shardService';
import { logPlay } from './services/statsService';
import type { BaconTrailWidgetConfig, WidgetState } from './types';

type Props = Pick<BaconTrailWidgetConfig, 'theme' | 'brandColor' | 'brandLogo' | 'ctaUrl' | 'ctaLabel'>;

const DEFAULT_CTA_URL = '/#work';
const DEFAULT_CTA_LABEL = 'See the full suite →';

function errorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  return 'Something went wrong.';
}

export function Widget({ ctaUrl = DEFAULT_CTA_URL, ctaLabel = DEFAULT_CTA_LABEL, theme = 'dark' }: Props) {
  const [state, dispatch] = useReducer(reducer, initialState);

  // Used to generate a unique key per "round" so effects retrigger cleanly
  // after Play Again (the state goes back to 'loading' and this increments).
  const roundRef = useRef(0);

  // Effect: on loading, fetch today's shard
  useEffect(() => {
    if (state.status !== 'loading') return;
    const thisRound = ++roundRef.current;

    let cancelled = false;
    const run = async () => {
      try {
        const actors = await fetchTodayShard();
        if (cancelled || thisRound !== roundRef.current) return;
        dispatch({ type: 'SHARD_LOADED', actors });
      } catch (err) {
        if (cancelled) return;
        dispatch({
          type: 'ERROR',
          message: `Couldn't load today's Kevin Bacon lineup. ${errorMessage(err)}`,
          retry: () => dispatch({ type: 'PLAY_AGAIN' }),
        });
      }
    };
    void run();
    return () => {
      cancelled = true;
    };
  }, [state.status]);

  // Effect: on pick-movie with no movies loaded yet, fetch the credits
  useEffect(() => {
    if (state.status !== 'pick-movie' || state.movies.length > 0) return;
    const subjectId = state.subject.id;

    let cancelled = false;
    const run = async () => {
      try {
        const movies = await fetchMovieCreditsForActor(subjectId);
        if (cancelled) return;
        dispatch({ type: 'MOVIES_LOADED', movies });
      } catch (err) {
        if (cancelled) return;
        dispatch({
          type: 'ERROR',
          message: `Couldn't load movies for ${state.subject.name}. ${errorMessage(err)}`,
          retry: () => dispatch({ type: 'PLAY_AGAIN' }),
        });
      }
    };
    void run();
    return () => {
      cancelled = true;
    };
    // Safe: pick-movie status + subjectId is the unique key.
  }, [state.status, state.status === 'pick-movie' ? state.subject.id : null]);

  // Effect: on fetching-cast, fetch the cast
  useEffect(() => {
    if (state.status !== 'fetching-cast') return;
    const movieId = state.movie.id;

    let cancelled = false;
    const run = async () => {
      try {
        const cast = await fetchCastForMovie(movieId);
        if (cancelled) return;
        dispatch({ type: 'CAST_LOADED', cast });
      } catch (err) {
        if (cancelled) return;
        dispatch({
          type: 'ERROR',
          message: `Couldn't load cast. ${errorMessage(err)}`,
          retry: () => dispatch({ type: 'PLAY_AGAIN' }),
        });
      }
    };
    void run();
    return () => {
      cancelled = true;
    };
  }, [state.status, state.status === 'fetching-cast' ? state.movie.id : null]);

  const onPlayAgain = useCallback(() => dispatch({ type: 'PLAY_AGAIN' }), []);

  const celebrating = state.status === 'result' && state.outcome === 'found';

  // Fire the anonymous play-logger exactly once per reached `result` state.
  // Fire-and-forget; service swallows its own errors so this never blocks.
  // Guard via a ref so React's strict-mode double-effect doesn't double-log.
  const loggedRoundRef = useRef<number>(-1);
  useEffect(() => {
    if (state.status !== 'result') return;
    if (loggedRoundRef.current === roundRef.current) return;
    loggedRoundRef.current = roundRef.current;
    logPlay(state.outcome, state.filmCount);
  }, [state.status]);

  return (
    <div className={`bacon-trail-widget${celebrating ? ' is-celebrating' : ''}`} data-theme={theme}>
      <Header state={state} />
      <ScreenRouter state={state} dispatch={dispatch} onPlayAgain={onPlayAgain} ctaUrl={ctaUrl} ctaLabel={ctaLabel} />
      <LiveRegion state={state} />
    </div>
  );
}

function Header({ state }: { state: WidgetState }) {
  const filmCount = 'filmCount' in state ? state.filmCount : 0;
  const trail = 'trail' in state ? state.trail : [];

  return (
    <>
      <div className="btw-header">
        <h2 className="btw-title">Birthday Bacon Trail</h2>
        <FilmCounter filmCount={filmCount} />
      </div>
      {state.status === 'result' ? (
        <ResultBanner outcome={state.outcome} filmCount={state.filmCount} />
      ) : (
        <TrailBreadcrumb trail={trail} />
      )}
    </>
  );
}

function ScreenRouter({
  state,
  dispatch,
  onPlayAgain,
  ctaUrl,
  ctaLabel,
}: {
  state: WidgetState;
  dispatch: React.Dispatch<Action>;
  onPlayAgain: () => void;
  ctaUrl: string;
  ctaLabel: string;
}) {
  switch (state.status) {
    case 'loading':
      return (
        <div className="btw-screen">
          <div className="btw-screen-header">
            <h3 className="btw-screen-lead">Loading today's birthdays…</h3>
          </div>
          <div className="btw-grid cols-3" aria-hidden="true">
            {Array.from({ length: 6 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        </div>
      );

    case 'error':
      return <ErrorCard message={state.message} onRetry={state.retry} />;

    case 'pick-actor':
      return (
        <BirthdayActorGrid
          actors={state.displayed}
          shardSize={state.shard.length}
          onPick={(actor) => dispatch({ type: 'ACTOR_PICKED', actor })}
          onShuffle={() => dispatch({ type: 'SHUFFLE_ACTORS' })}
        />
      );

    case 'pick-movie':
      return (
        <MovieList
          movies={state.movies}
          subjectName={state.subject.name}
          trail={state.trail}
          onPick={(movie) => dispatch({ type: 'MOVIE_PICKED', movie })}
        />
      );

    case 'fetching-cast':
      return (
        <div className="btw-screen">
          <div className="btw-screen-header">
            <h3 className="btw-screen-lead">Checking the cast…</h3>
            <p className="btw-screen-sub">Seeing if Kevin Bacon's in {state.movie.title}.</p>
          </div>
          <div className="btw-grid cols-3" aria-hidden="true">
            {Array.from({ length: 6 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        </div>
      );

    case 'pick-co-actor':
      return (
        <CoActorGrid
          cast={state.cast}
          movieTitle={state.movie.title}
          trail={state.trail}
          onPick={(actor) => dispatch({ type: 'CO_ACTOR_PICKED', actor })}
        />
      );

    case 'result':
      return (
        <ResultCard
          outcome={state.outcome}
          filmCount={state.filmCount}
          trail={state.trail}
          ctaUrl={ctaUrl}
          ctaLabel={ctaLabel}
          onPlayAgain={onPlayAgain}
        />
      );
  }
}

// Screen-reader live region — announces key events so assistive tech users
// know what happened after each pick. Per PRD Accessibility block.
function LiveRegion({ state }: { state: WidgetState }) {
  let message = '';
  switch (state.status) {
    case 'loading':
      message = 'Loading today\'s Kevin Bacon birthdays.';
      break;
    case 'pick-movie':
      message = `Film ${state.filmCount} of 6. Pick a film starring ${state.subject.name}.`;
      break;
    case 'fetching-cast':
      message = `Checking cast of ${state.movie.title} for Kevin Bacon.`;
      break;
    case 'pick-co-actor':
      message = `Kevin Bacon not in ${state.movie.title}. Pick a co-actor to continue.`;
      break;
    case 'result':
      message =
        state.outcome === 'found'
          ? `Found Kevin Bacon in ${state.filmCount} film${state.filmCount === 1 ? '' : 's'}.`
          : `Didn't find Kevin Bacon in 6 films.`;
      break;
  }
  return (
    <div className="btw-sr-only" role="status" aria-live="polite">
      {message}
    </div>
  );
}
