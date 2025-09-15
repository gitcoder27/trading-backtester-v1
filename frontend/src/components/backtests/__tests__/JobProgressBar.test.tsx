import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import JobProgressBar from '../../backtests/JobProgressBar';

describe('JobProgressBar', () => {
  it('renders nothing when status is completed', () => {
    const { container } = render(<JobProgressBar status="completed" progress={100} /> as any);
    expect(container.innerHTML).toBe('');
  });

  it('renders progress and ETA for running status (md)', () => {
    render(<JobProgressBar status="running" progress={40} estimatedTime="~10s remaining" /> as any);
    expect(screen.getByText('Progress')).toBeInTheDocument();
    expect(screen.getByText(/40%/)).toBeInTheDocument();
    expect(screen.getByText('~10s remaining')).toBeInTheDocument();
  });

  it('does not render labels for small size', () => {
    render(<JobProgressBar status="running" progress={25} size="sm" /> as any);
    expect(screen.queryByText('Progress')).toBeNull();
  });
});

