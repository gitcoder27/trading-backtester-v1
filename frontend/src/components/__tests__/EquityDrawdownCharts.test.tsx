import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import EquityChart from '../charts/EquityChart';
import DrawdownChart from '../charts/DrawdownChart';

describe('Equity/Drawdown charts (data mode)', () => {
  it('renders equity with provided data without API calls', () => {
    const data = [
      { timestamp: String(1700000000), equity: 100 },
      { timestamp: String(1700000600), equity: 110 }
    ];
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <EquityChart data={data} />
      </QueryClientProvider>
    );
    expect(document.querySelector('.w-full.h-full')).toBeInTheDocument();
  });

  it('renders drawdown with provided data without API calls', () => {
    const data = [
      { timestamp: String(1700000000), equity: 100 },
      { timestamp: String(1700000600), equity: 90 }
    ];
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <DrawdownChart data={data} />
      </QueryClientProvider>
    );
    expect(document.querySelector('.w-full.h-full')).toBeInTheDocument();
  });
});
