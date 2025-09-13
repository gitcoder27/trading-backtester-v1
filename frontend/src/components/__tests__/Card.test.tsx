import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Card from '../ui/Card';

describe('Card', () => {
  it('renders children and supports padding/shadow variants', () => {
    const { rerender } = render(
      <Card padding="sm" shadow="sm">content</Card>
    );
    expect(screen.getByText('content')).toBeInTheDocument();

    // Change variants
    rerender(
      <Card padding="lg" shadow="lg">content</Card>
    );
    expect(screen.getByText('content')).toBeInTheDocument();
  });

  it('handles onClick', () => {
    const onClick = vi.fn();
    render(<Card onClick={onClick}>click me</Card>);
    fireEvent.click(screen.getByText('click me'));
    expect(onClick).toHaveBeenCalled();
  });
});

