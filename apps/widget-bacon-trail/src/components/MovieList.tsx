import { ChevronLeft, ChevronRight, Film } from 'lucide-react';
import { useEffect, useState } from 'react';
import type { Movie } from '../types';
import { MOVIES_PER_PAGE } from '../types';
import { tmdbImageUrl } from '../services/tmdbService';
import { SkeletonCard } from './SkeletonCard';

interface Props {
  movies: Movie[];
  subjectName: string;
  onPick: (movie: Movie) => void;
}

// Epic 3 — pick a movie from the current subject's filmography. 3×3 grid of
// poster cards, paginated. 9 movies per page × up to 3 pages = 27 top films
// sorted by popularity. Bacon win-check fires in the parent after pick.
export function MovieList({ movies, subjectName, onPick }: Props) {
  const [page, setPage] = useState(0);
  const isLoading = movies.length === 0;
  const totalPages = Math.max(1, Math.ceil(movies.length / MOVIES_PER_PAGE));

  // Reset to page 0 when the subject (and therefore the movies prop) changes.
  useEffect(() => {
    setPage(0);
  }, [movies]);

  const start = page * MOVIES_PER_PAGE;
  const pageMovies = movies.slice(start, start + MOVIES_PER_PAGE);

  return (
    <div className="btw-screen">
      <div className="btw-screen-header">
        <h3 className="btw-screen-lead">Pick a film for {subjectName}.</h3>
        <p className="btw-screen-sub">If Kevin Bacon's in the cast, you win this round.</p>
      </div>

      <div className="btw-grid cols-3" role="group" aria-label={`Films starring ${subjectName}`}>
        {isLoading
          ? Array.from({ length: MOVIES_PER_PAGE }).map((_, i) => <SkeletonCard key={i} />)
          : pageMovies.map((movie) => (
              <MovieCard key={movie.id} movie={movie} onPick={onPick} />
            ))}
      </div>

      {!isLoading && totalPages > 1 && (
        <Pager page={page} totalPages={totalPages} onChange={setPage} />
      )}
    </div>
  );
}

function Pager({
  page,
  totalPages,
  onChange,
}: {
  page: number;
  totalPages: number;
  onChange: (p: number) => void;
}) {
  const canPrev = page > 0;
  const canNext = page < totalPages - 1;

  return (
    <div className="btw-pager" role="group" aria-label="Film pagination">
      <button
        type="button"
        className="btw-pager-btn"
        onClick={() => onChange(page - 1)}
        disabled={!canPrev}
        aria-label="Previous page"
      >
        <ChevronLeft size={16} strokeWidth={2} aria-hidden="true" />
      </button>
      <span className="btw-pager-label" aria-live="polite">
        Page <strong>{page + 1}</strong> / {totalPages}
      </span>
      <button
        type="button"
        className="btw-pager-btn"
        onClick={() => onChange(page + 1)}
        disabled={!canNext}
        aria-label="Next page"
      >
        <ChevronRight size={16} strokeWidth={2} aria-hidden="true" />
      </button>
    </div>
  );
}

function MovieCard({ movie, onPick }: { movie: Movie; onPick: (m: Movie) => void }) {
  const imageUrl = tmdbImageUrl(movie.posterPath, 'w185');
  const short = shortTitle(movie.title);

  return (
    <button
      type="button"
      className="btw-card"
      onClick={() => onPick(movie)}
      aria-label={`Pick ${movie.title}${movie.releaseYear ? `, ${movie.releaseYear}` : ''}`}
      title={movie.title}
    >
      <div className="btw-card-image-wrap">
        {imageUrl ? (
          <img src={imageUrl} alt="" loading="lazy" onError={hideOnError} />
        ) : (
          <Film size={24} strokeWidth={1.75} aria-hidden="true" />
        )}
      </div>
      <div className="btw-card-meta">
        <span className="btw-card-title">{short}</span>
        {movie.releaseYear && <span className="btw-card-sub">{movie.releaseYear}</span>}
      </div>
    </button>
  );
}

// Best-effort shortener for TMDB titles without a compact variant.
// - WWE WrestleMania X – Day → "WrestleMania X · Sun/Sat/Etc".
// - Long titles containing ":" / "–" / "—" → keep just the head if it's
//   a ≥2-word phrase.
// - Otherwise pass through; the card's `title` attribute surfaces the
//   full name on hover.
export function shortTitle(title: string): string {
  const wwe = title.match(/^WWE\s+(WrestleMania\s+\S+)\s*[–—-]\s*(\S+)/i);
  if (wwe) {
    const event = wwe[1];
    const dayFull = wwe[2];
    if (event && dayFull) {
      const dayShort = dayFull.length > 4 ? dayFull.slice(0, 3) : dayFull;
      return `${event} · ${dayShort}`;
    }
  }

  if (title.length > 24) {
    const sepMatch = title.match(/^(.+?)[:–—]/);
    if (sepMatch && sepMatch[1]) {
      const head = sepMatch[1].trim();
      if (head.split(/\s+/).length >= 2) {
        return head;
      }
    }
  }

  return title;
}

function hideOnError(e: React.SyntheticEvent<HTMLImageElement>) {
  e.currentTarget.style.display = 'none';
}
