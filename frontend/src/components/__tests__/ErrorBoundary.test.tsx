import { describe, it, expect, vi, beforeEach, afterAll } from 'vitest';
import { render, screen } from '@testing-library/react';
import ErrorBoundary, { ErrorFallback } from '../ui/ErrorBoundary';

const ProblemChild = () => {
  throw new Error('Boom');
};

describe('ErrorBoundary', () => {
  const originalError = console.error;
  beforeEach(() => {
    // Silence expected error logs
    console.error = vi.fn();
  });

  afterAll(() => {
    console.error = originalError;
  });

  it('renders default fallback UI when child throws', () => {
    render(
      <ErrorBoundary>
        <ProblemChild />
      </ErrorBoundary>
    );
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('supports custom fallback', () => {
    render(
      <ErrorBoundary fallback={<div>Custom</div>}>
        <ProblemChild />
      </ErrorBoundary>
    );
    expect(screen.getByText('Custom')).toBeInTheDocument();
  });
});

describe('ErrorFallback', () => {
  it('renders message and optional error', () => {
    const { rerender } = render(<ErrorFallback message="Oops" />);
    expect(screen.getByText('Oops')).toBeInTheDocument();
    rerender(<ErrorFallback error={new Error('Bad')} />);
    expect(screen.getByText('Bad')).toBeInTheDocument();
  });
});
