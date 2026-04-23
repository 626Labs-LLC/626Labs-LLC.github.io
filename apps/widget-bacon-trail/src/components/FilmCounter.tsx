import { MAX_FILMS } from '../types';

interface Props {
  filmCount: number;
}

export function FilmCounter({ filmCount }: Props) {
  const current = Math.min(Math.max(filmCount, 0), MAX_FILMS);
  return (
    <div className="btw-film-counter" aria-label={`Film ${current} of ${MAX_FILMS}`}>
      <span>Film</span>
      <span className="btw-film-counter-number">{current}</span>
      <span>/</span>
      <span>{MAX_FILMS}</span>
    </div>
  );
}
