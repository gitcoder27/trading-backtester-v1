import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import PlotlyChart from '../charts/PlotlyChart';

describe('PlotlyChart', () => {
  it('renders loading state', () => {
    render(<PlotlyChart data={[]} loading className="cls" />);
    expect(screen.getByText(/Loading chart/)).toBeInTheDocument();
  });

  it('renders error state', () => {
    render(<PlotlyChart data={[]} error="Oops" />);
    expect(screen.getByText(/Failed to load chart/)).toBeInTheDocument();
    expect(screen.getByText('Oops')).toBeInTheDocument();
  });

  it('renders empty state', () => {
    render(<PlotlyChart data={[]} />);
    expect(screen.getByText(/No data available/)).toBeInTheDocument();
  });

  it('renders with provided data', () => {
    render(<PlotlyChart data={[{ x: [1], y: [2], type: 'scatter' }]} />);
    // react-plotly is mocked -> assert wrapper exists and not empty state
    expect(document.querySelector('.w-full.h-full')).toBeInTheDocument();
    expect(screen.queryByText(/No data available/)).toBeNull();
  });
});
