import { ChevronLeft, ChevronRight } from 'lucide-react';

interface Props {
  page: number;
  totalPages: number;
  onChange: (page: number) => void;
  ariaLabel?: string;
}

// Shared prev/next pager used by MovieList + CoActorGrid. Hidden by the
// caller when totalPages <= 1.
export function Pager({ page, totalPages, onChange, ariaLabel = 'Pagination' }: Props) {
  const canPrev = page > 0;
  const canNext = page < totalPages - 1;

  return (
    <div className="btw-pager" role="group" aria-label={ariaLabel}>
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
