import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Badge, { StatusBadge, PerformanceBadge } from '../ui/Badge';

describe('Badge', () => {
  it('renders basic badge and supports dot and icon positions', () => {
    const { rerender } = render(<Badge>Label</Badge>);
    expect(screen.getByText('Label')).toBeInTheDocument();

    rerender(<Badge dot>Dot</Badge>);
    expect(screen.getByText('Dot')).toBeInTheDocument();
  });

  it('renders status badge', () => {
    render(<StatusBadge status="completed" />);
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('renders performance badge with formats', () => {
    const { rerender } = render(<PerformanceBadge value={1.234} />);
    expect(screen.getByText('+1.23%')).toBeInTheDocument();

    rerender(<PerformanceBadge value={-1000} format="currency" />);
    expect(screen.getByText('-$1,000.00')).toBeInTheDocument();

    rerender(<PerformanceBadge value={0} format="number" showSign={false} />);
    expect(screen.getByText('0')).toBeInTheDocument();
  });
});

