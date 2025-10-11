import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import PlotlyChart from '../charts/PlotlyChart';

describe('PlotlyChart', () => {
  it('renders with provided data', () => {
    const { container } = render(
      <PlotlyChart data={[{ x: [1], y: [2], type: 'scatter' }]} />
    );
    const chart = container.firstElementChild as HTMLElement;
    expect(chart).toBeInTheDocument();
    expect(chart).toHaveClass('w-full');
    expect(chart).toHaveClass('min-h-[200px]');
  });

  it('applies custom class', () => {
    const { container } = render(<PlotlyChart className="custom-class" />);
    const chart = container.firstElementChild as HTMLElement;
    expect(chart).toBeInTheDocument();
    expect(chart).toHaveClass('custom-class');
  });
});
