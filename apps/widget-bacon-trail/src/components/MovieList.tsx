import { Film } from 'lucide-react';
import type { Movie } from '../types';
import { tmdbImageUrl } from '../services/tmdbService';
import { SkeletonCard } from './SkeletonCard';

interface Props {
  movies: Movie[];
  subjectName: string;
  onPick: (movie: Movie) => void;
}

// Epic 3 — pick a movie from the current subject's filmography. 3-col grid
// of poster cards. The Bacon win-check fires in the parent after the user
// picks.
export function MovieList({ movies, subjectName, onPick }: Props) {
  const isLoading = movies.length === 0;

  return (
    <div className="btw-screen">
      <div className="btw-screen-header">
        <h3 className="btw-screen-lead">Pick a film for {subjectName}.</h3>
        <p className="btw-screen-sub">If Kevin Bacon's in the cast, you win this round.</p>
      </div>

      <div className="btw-grid cols-3" role="group" aria-label={`Films starring ${subjectName}`}>
        {isLoading
          ? Array.from({ length: 9 }).map((_, i) => <SkeletonCard key={i} />)
          : movies.map((movie) => (
              <MovieCard key={movie.id} movie={movie} onPick={onPick} />
            ))}
      </div>
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
//   a ≥2-word phrase. (e.g., "Teenage Mutant Ninja Turtles: Mutant Mayhem"
//   → "Teenage Mutant Ninja Turtles"; "Star Wars: Episode IV – A New Hope"
//   → "Star Wars".)
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
