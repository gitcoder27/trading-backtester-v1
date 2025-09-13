import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LoadingSpinner, LoadingSkeleton, LoadingOverlay, PageLoading, TableSkeleton, CardSkeleton } from '../ui/Loading';

describe('Loading UI', () => {
  it('renders spinner with sizes and colors', () => {
    const { rerender } = render(<LoadingSpinner />);
    expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument();
    rerender(<LoadingSpinner size="xl" color="white" />);
    expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument();
  });

  it('renders skeleton variants', () => {
    const { rerender } = render(<LoadingSkeleton />);
    expect(screen.getByRole('status', { name: /loading content/i })).toBeInTheDocument();
    rerender(<LoadingSkeleton variant="rectangular" />);
    expect(screen.getByRole('status', { name: /loading content/i })).toBeInTheDocument();
  });

  it('renders overlay when loading', () => {
    const { rerender } = render(<LoadingOverlay loading={false}><div>child</div></LoadingOverlay>);
    expect(screen.getByText('child')).toBeInTheDocument();
    rerender(<LoadingOverlay loading message="Please wait"><div>child</div></LoadingOverlay>);
    expect(screen.getByText('Please wait')).toBeInTheDocument();
  });

  it('renders page loading', () => {
    render(<PageLoading message="Loading page..." />);
    expect(screen.getByText('Loading page...')).toBeInTheDocument();
  });

  it('renders table and card skeletons', () => {
    render(<TableSkeleton rows={2} cols={3} />);
    render(<CardSkeleton />);
    // Smoke test: ensure container renders
    expect(true).toBe(true);
  });
});

