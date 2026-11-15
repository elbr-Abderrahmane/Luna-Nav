import { ApiError } from "../api/client";

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const msg =
    error instanceof ApiError ? `${error.message} (${error.code})` : error instanceof Error ? error.message : "Something went wrong.";
  return (
    <div className="error" role="alert">
      <strong>Could not load this.</strong>
      <span>{msg}</span>
      {onRetry && (
        <button className="btn small" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}
