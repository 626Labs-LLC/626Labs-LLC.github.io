interface Props {
  variant?: 'poster' | 'list-row';
}

// Shimmering placeholder card for the moment between a fetch starting and
// the data arriving. PRD mandates skeleton UI, never a spinner.
export function SkeletonCard({ variant = 'poster' }: Props) {
  if (variant === 'list-row') {
    return (
      <div className="btw-list-item" aria-hidden="true" data-testid="skeleton-list-row">
        <div className="btw-list-thumb" />
        <div className="btw-list-body">
          <div className="btw-skeleton-line" />
          <div className="btw-skeleton-line short" />
        </div>
      </div>
    );
  }

  return (
    <div className="btw-skeleton" aria-hidden="true" data-testid="skeleton-poster">
      <div className="btw-skeleton-image" />
      <div className="btw-skeleton-line" />
      <div className="btw-skeleton-line short" />
    </div>
  );
}
