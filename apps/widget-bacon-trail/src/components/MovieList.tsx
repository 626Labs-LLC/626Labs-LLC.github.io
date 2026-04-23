import { Film } from 'lucide-react';
import type { Movie } from '../types';
import { tmdbImageUrl } from '../services/tmdbService';
import { SkeletonCard } from './SkeletonCard';

interface Props {
  movies: Movie[];
  subjectName: string;
  onPick: (movie: Movie) => void;
}

// Epic 3 — pick a movie from the current subject's filmography. Scrollable
// list (not a grid — spec says list). The Bacon-win check fires in the
// parent after the user picks, not here.
export function MovieList({ movies, subjectName, onPick }: Props) {
  const isLoading = movies.length === 0;

  return (
    <div className="btw-screen">
      <div className="btw-screen-header">
        <h3 className="btw-screen-lead">Pick a film for {subjectName}.</h3>
        <p className="btw-screen-sub">If Kevin Bacon's in the cast, you win this round.</p>
      </div>

      <div className="btw-list" role="list" aria-label={`Films starring ${subjectName}`}>
        {isLoading
          ? Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} variant="list-row" />)
          : movies.map((movie) => (
              <MovieRow key={movie.id} movie={movie} onPick={onPick} />
            ))}
      </div>
    </div>
  );
}

function MovieRow({ movie, onPick }: { movie: Movie; onPick: (m: Movie) => void }) {
  const imageUrl = tmdbImageUrl(movie.posterPath, 'w92');

  return (
    <button
      type="button"
      className="btw-list-item"
      role="listitem"
      onClick={() => onPick(movie)}
      aria-label={`Pick ${movie.title}${movie.releaseYear ? `, ${movie.releaseYear}` : ''}`}
    >
      <div className="btw-list-thumb">
        {imageUrl ? (
          <img src={imageUrl} alt="" loading="lazy" onError={hideOnError} />
        ) : (
          <Film size={24} strokeWidth={1.75} aria-hidden="true" />
        )}
      </div>
      <div className="btw-list-body">
        <span className="btw-card-title">{movie.title}</span>
        {movie.releaseYear && <span className="btw-card-sub">{movie.releaseYear}</span>}
      </div>
    </button>
  );
}

function hideOnError(e: React.SyntheticEvent<HTMLImageElement>) {
  e.currentTarget.style.display = 'none';
}
