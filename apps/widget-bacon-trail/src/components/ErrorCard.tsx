import { AlertTriangle } from 'lucide-react';

interface Props {
  message: string;
  onRetry: () => void;
}

export function ErrorCard({ message, onRetry }: Props) {
  return (
    <div className="btw-error" role="alert">
      <AlertTriangle size={28} strokeWidth={1.75} className="btw-error-icon" aria-hidden="true" />
      <p className="btw-error-message">{message}</p>
      <button type="button" className="btw-btn secondary" onClick={onRetry}>
        Try again
      </button>
    </div>
  );
}
