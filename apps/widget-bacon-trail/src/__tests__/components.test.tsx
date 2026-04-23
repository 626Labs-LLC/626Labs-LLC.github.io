import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FilmCounter } from '../components/FilmCounter';
import { SkeletonCard } from '../components/SkeletonCard';
import { ErrorCard } from '../components/ErrorCard';
import { TrailBreadcrumb } from '../components/TrailBreadcrumb';
import { BirthdayActorGrid } from '../components/BirthdayActorGrid';
import { MovieList } from '../components/MovieList';
import { CoActorGrid } from '../components/CoActorGrid';
import { ResultCard } from '../components/ResultCard';
import type { Actor, Movie, TrailStep } from '../types';

const mkActor = (id: number, name = `Actor ${id}`): Actor => ({
  id,
  name,
  profilePath: null,
  birthday: '1960-01-01',
  popularity: 1,
});

const mkMovie = (id: number, title = `Film ${id}`): Movie => ({
  id,
  title,
  posterPath: null,
  releaseYear: 2000,
  popularity: 1,
});

describe('FilmCounter', () => {
  it('renders current film and max', () => {
    render(<FilmCounter filmCount={3} />);
    expect(screen.getByLabelText('Film 3 of 6')).toBeInTheDocument();
  });

  it('clamps negative and over-max values', () => {
    const { rerender } = render(<FilmCounter filmCount={-5} />);
    expect(screen.getByLabelText('Film 0 of 6')).toBeInTheDocument();
    rerender(<FilmCounter filmCount={99} />);
    expect(screen.getByLabelText('Film 6 of 6')).toBeInTheDocument();
  });
});

describe('SkeletonCard', () => {
  it('renders poster variant by default', () => {
    render(<SkeletonCard />);
    expect(screen.getByTestId('skeleton-poster')).toBeInTheDocument();
  });

  it('renders list-row variant when specified', () => {
    render(<SkeletonCard variant="list-row" />);
    expect(screen.getByTestId('skeleton-list-row')).toBeInTheDocument();
  });
});

describe('ErrorCard', () => {
  it('renders message + retry button + fires onRetry on click', () => {
    const onRetry = vi.fn();
    render(<ErrorCard message="Network down" onRetry={onRetry} />);
    expect(screen.getByText('Network down')).toBeInTheDocument();
    const btn = screen.getByRole('button', { name: /try again/i });
    fireEvent.click(btn);
    expect(onRetry).toHaveBeenCalledOnce();
  });
});

describe('TrailBreadcrumb', () => {
  it('renders nothing on empty trail', () => {
    const { container } = render(<TrailBreadcrumb trail={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders actor + movie steps', () => {
    const trail: TrailStep[] = [
      { kind: 'actor', actor: mkActor(1, 'Harvey Keitel') },
      { kind: 'movie', movie: mkMovie(100, 'Pulp Fiction'), baconInCast: false },
      { kind: 'actor', actor: mkActor(2, 'Samuel L. Jackson') },
    ];
    render(<TrailBreadcrumb trail={trail} />);
    expect(screen.getByText('Harvey Keitel')).toBeInTheDocument();
    expect(screen.getByText('Pulp Fiction')).toBeInTheDocument();
    expect(screen.getByText('Samuel L. Jackson')).toBeInTheDocument();
  });

  it('applies is-bacon class to the winning movie step', () => {
    const trail: TrailStep[] = [
      { kind: 'movie', movie: mkMovie(100, 'A Few Good Men'), baconInCast: true },
    ];
    const { container } = render(<TrailBreadcrumb trail={trail} />);
    expect(container.querySelector('.is-bacon')).not.toBeNull();
  });
});

describe('BirthdayActorGrid', () => {
  it('renders N cards and fires onPick on card click', () => {
    const actors = [mkActor(1, 'Harvey'), mkActor(2, 'Meryl'), mkActor(3, 'Samuel')];
    const onPick = vi.fn();
    const onShuffle = vi.fn();
    render(<BirthdayActorGrid actors={actors} shardSize={3} onPick={onPick} onShuffle={onShuffle} />);
    const harveyBtn = screen.getByLabelText(/Pick Harvey/);
    fireEvent.click(harveyBtn);
    expect(onPick).toHaveBeenCalledWith(actors[0]);
  });

  it('shows shuffle button when shard has more than grid size', () => {
    const actors = Array.from({ length: 6 }, (_, i) => mkActor(i + 1));
    render(
      <BirthdayActorGrid actors={actors} shardSize={20} onPick={() => {}} onShuffle={() => {}} />
    );
    expect(screen.getByRole('button', { name: /different actors/i })).toBeInTheDocument();
  });

  it('hides shuffle button when shard size <= grid size', () => {
    const actors = Array.from({ length: 6 }, (_, i) => mkActor(i + 1));
    render(
      <BirthdayActorGrid actors={actors} shardSize={6} onPick={() => {}} onShuffle={() => {}} />
    );
    expect(screen.queryByRole('button', { name: /different actors/i })).not.toBeInTheDocument();
  });

  it('shows empty-state when actors is empty', () => {
    render(<BirthdayActorGrid actors={[]} shardSize={0} onPick={() => {}} onShuffle={() => {}} />);
    expect(screen.getByText(/no birthday actors/i)).toBeInTheDocument();
  });
});

describe('MovieList', () => {
  it('shows skeleton cards when movies is empty (loading)', () => {
    render(<MovieList movies={[]} subjectName="Harvey Keitel" trail={[]} onPick={() => {}} />);
    expect(screen.getAllByTestId('skeleton-poster').length).toBeGreaterThan(0);
  });

  it('renders movie cards and fires onPick', () => {
    const movies = [mkMovie(100, 'Pulp Fiction'), mkMovie(101, 'Reservoir Dogs')];
    const onPick = vi.fn();
    render(<MovieList movies={movies} subjectName="Harvey Keitel" trail={[]} onPick={onPick} />);
    fireEvent.click(screen.getByLabelText(/Pick Pulp Fiction/));
    expect(onPick).toHaveBeenCalledWith(movies[0]);
  });

  it('shortens WWE WrestleMania titles and long colon-split titles', async () => {
    const { shortTitle } = await import('../components/MovieList');
    expect(shortTitle('WWE WrestleMania 42 – Sunday')).toBe('WrestleMania 42 · Sun');
    expect(shortTitle('WWE WrestleMania 42 – Saturday')).toBe('WrestleMania 42 · Sat');
    expect(shortTitle('Star Wars: Episode IV – A New Hope')).toBe('Star Wars');
    expect(shortTitle('Pulp Fiction')).toBe('Pulp Fiction');
    expect(shortTitle('Teenage Mutant Ninja Turtles: Mutant Mayhem')).toBe('Teenage Mutant Ninja Turtles');
  });

  it('paginates at 9 films per page and renders prev/next controls', () => {
    const movies = Array.from({ length: 20 }, (_, i) => mkMovie(i + 1, `Film ${i + 1}`));
    render(<MovieList movies={movies} subjectName="Anyone" trail={[]} onPick={() => {}} />);

    expect(screen.getByLabelText(/Pick Film 1,/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Pick Film 9,/)).toBeInTheDocument();
    expect(screen.queryByLabelText(/Pick Film 10,/)).not.toBeInTheDocument();

    const pager = screen.getByLabelText('Film pagination');
    expect(pager).toHaveTextContent(/Page\s*1\s*\/\s*3/);
    expect(screen.getByLabelText('Previous page')).toBeDisabled();

    fireEvent.click(screen.getByLabelText('Next page'));
    expect(screen.getByLabelText(/Pick Film 10,/)).toBeInTheDocument();
    expect(screen.queryByLabelText(/Pick Film 1,/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByLabelText('Next page'));
    expect(screen.getByLabelText(/Pick Film 19,/)).toBeInTheDocument();
    expect(screen.getByLabelText('Next page')).toBeDisabled();
  });

  it('hides the pager when movies fit on one page', () => {
    const movies = Array.from({ length: 5 }, (_, i) => mkMovie(i + 1));
    render(<MovieList movies={movies} subjectName="Anyone" trail={[]} onPick={() => {}} />);
    expect(screen.queryByLabelText('Next page')).not.toBeInTheDocument();
  });

  it('filters out films already in the trail', () => {
    const barbie = mkMovie(100, 'Barbie');
    const fight = mkMovie(101, 'Fight Club');
    const trail: TrailStep[] = [{ kind: 'movie', movie: barbie, baconInCast: false }];
    render(
      <MovieList movies={[barbie, fight]} subjectName="Someone" trail={trail} onPick={() => {}} />
    );
    expect(screen.queryByLabelText(/Pick Barbie/)).not.toBeInTheDocument();
    expect(screen.getByLabelText(/Pick Fight Club/)).toBeInTheDocument();
  });
});

describe('CoActorGrid', () => {
  it('filters out actors already in the trail (not just disables them)', () => {
    const already = mkActor(42, 'Harvey');
    const next = mkActor(43, 'Sam');
    const trail: TrailStep[] = [{ kind: 'actor', actor: already }];
    render(
      <CoActorGrid cast={[already, next]} movieTitle="Pulp Fiction" trail={trail} onPick={() => {}} />
    );
    expect(screen.queryByLabelText(/Pick Harvey/)).not.toBeInTheDocument();
    expect(screen.getByLabelText(/Pick Sam/)).toBeInTheDocument();
  });

  it('fires onPick when a fresh co-actor is clicked', () => {
    const cast = [mkActor(50, 'Tim'), mkActor(51, 'Quentin')];
    const onPick = vi.fn();
    render(<CoActorGrid cast={cast} movieTitle="Pulp" trail={[]} onPick={onPick} />);
    fireEvent.click(screen.getByLabelText(/Pick Tim/));
    expect(onPick).toHaveBeenCalledWith(cast[0]);
  });

  it('handles cast fully contained in trail with a fallback message', () => {
    const a = mkActor(1, 'A');
    const b = mkActor(2, 'B');
    render(
      <CoActorGrid
        cast={[a, b]}
        movieTitle="X"
        trail={[
          { kind: 'actor', actor: a },
          { kind: 'actor', actor: b },
        ]}
        onPick={() => {}}
      />
    );
    expect(screen.getByText(/already on your trail/i)).toBeInTheDocument();
  });

  it('paginates the cast at 9 per page', () => {
    const cast = Array.from({ length: 20 }, (_, i) => mkActor(i + 1, `Actor ${i + 1}`));
    render(<CoActorGrid cast={cast} movieTitle="X" trail={[]} onPick={() => {}} />);

    expect(screen.getByLabelText(/Pick Actor 1/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Pick Actor 9/)).toBeInTheDocument();
    expect(screen.queryByLabelText(/Pick Actor 10$/)).not.toBeInTheDocument();

    const pager = screen.getByLabelText('Cast pagination');
    expect(pager).toHaveTextContent(/Page\s*1\s*\/\s*3/);

    fireEvent.click(screen.getByLabelText('Next page'));
    expect(screen.getByLabelText(/Pick Actor 10/)).toBeInTheDocument();
  });

  it('hides the pager when available cast fits on one page', () => {
    const cast = Array.from({ length: 5 }, (_, i) => mkActor(i + 1));
    render(<CoActorGrid cast={cast} movieTitle="X" trail={[]} onPick={() => {}} />);
    expect(screen.queryByLabelText('Next page')).not.toBeInTheDocument();
  });
});

describe('ResultCard', () => {
  it('renders the found state with film count', () => {
    render(
      <ResultCard
        outcome="found"
        filmCount={3}
        trail={[]}
        ctaUrl="/x"
        ctaLabel="See the suite"
        onPlayAgain={() => {}}
      />
    );
    expect(screen.getByText(/you found bacon/i)).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('renders the out-of-films state', () => {
    render(
      <ResultCard
        outcome="out-of-films"
        filmCount={6}
        trail={[]}
        ctaUrl="/x"
        ctaLabel="See the suite"
        onPlayAgain={() => {}}
      />
    );
    expect(screen.getByText(/didn't find bacon/i)).toBeInTheDocument();
  });

  it('fires onPlayAgain on Play Again click', () => {
    const onPlay = vi.fn();
    render(
      <ResultCard
        outcome="found"
        filmCount={2}
        trail={[]}
        ctaUrl="/x"
        ctaLabel="See"
        onPlayAgain={onPlay}
      />
    );
    fireEvent.click(screen.getByRole('button', { name: /play again/i }));
    expect(onPlay).toHaveBeenCalledOnce();
  });

  it('renders the CTA link with the right href + label', () => {
    render(
      <ResultCard
        outcome="found"
        filmCount={2}
        trail={[]}
        ctaUrl="https://626labs.dev/#work"
        ctaLabel="See the full suite →"
        onPlayAgain={() => {}}
      />
    );
    const link = screen.getByRole('link', { name: /see the full suite/i });
    expect(link).toHaveAttribute('href', 'https://626labs.dev/#work');
  });
});
