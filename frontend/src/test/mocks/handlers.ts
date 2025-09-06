import { http, HttpResponse } from 'msw';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Mock response data
const mockBacktestResult = {
  id: '1',
  status: 'completed',
  created_at: '2024-01-01T00:00:00Z',
  completed_at: '2024-01-01T00:01:00Z',
  metrics: {
    total_return: 15.5,
    annual_return: 12.3,
    volatility: 8.7,
    sharpe_ratio: 1.41,
    max_drawdown: -5.2,
    win_rate: 0.65,
    profit_factor: 1.8,
    total_trades: 150
  },
  equity_curve: [
    { date: '2024-01-01', value: 100000 },
    { date: '2024-01-02', value: 101000 },
    { date: '2024-01-03', value: 102000 }
  ],
  trades: [
    {
      id: 1,
      entry_time: '2024-01-01T09:15:00Z',
      exit_time: '2024-01-01T15:30:00Z',
      symbol: 'NIFTY',
      side: 'long',
      quantity: 100,
      entry_price: 18500,
      exit_price: 18600,
      pnl: 10000,
      commission: 50
    }
  ]
};

const mockStrategies = [
  {
    id: '1',
    name: 'EMA Crossover',
    description: 'EMA crossover strategy',
    parameters: {
      fast_ema: 10,
      slow_ema: 20
    }
  }
];

const mockDatasets = [
  {
    id: '1',
    name: 'NIFTY 2024',
    symbol: 'NIFTY',
    timeframe: '1min',
    start_date: '2024-01-01',
    end_date: '2024-12-31',
    records: 100000
  }
];

const mockJobs = [
  {
    id: '1',
    type: 'backtest',
    status: 'completed',
    progress: 100,
    created_at: '2024-01-01T00:00:00Z',
    completed_at: '2024-01-01T00:01:00Z',
    result_id: '1'
  }
];

const mockAnalytics = {
  performance: {
    total_return: 15.5,
    annual_return: 12.3,
    volatility: 8.7,
    sharpe_ratio: 1.41,
    max_drawdown: -5.2,
    win_rate: 0.65,
    profit_factor: 1.8,
    total_trades: 150,
    winning_trades: 98,
    losing_trades: 52,
    avg_win: 1250,
    avg_loss: -680,
    largest_win: 5000,
    largest_loss: -2500
  },
  charts: {
    equity: {
      x: ['2024-01-01', '2024-01-02', '2024-01-03'],
      y: [100000, 101000, 102000],
      type: 'scatter',
      mode: 'lines'
    },
    drawdown: {
      x: ['2024-01-01', '2024-01-02', '2024-01-03'],
      y: [0, -1.2, -0.8],
      type: 'scatter',
      mode: 'lines'
    }
  }
};

export const handlers = [
  // Backtest endpoints
  http.post(`${API_BASE_URL}/backtests`, () => {
    return HttpResponse.json(mockBacktestResult);
  }),

  http.get(`${API_BASE_URL}/backtests/:id/results`, ({ params }) => {
    return HttpResponse.json({
      ...mockBacktestResult,
      id: params.id
    });
  }),

  http.get(`${API_BASE_URL}/backtests/:id`, ({ params }) => {
    return HttpResponse.json({
      ...mockBacktestResult,
      id: params.id
    });
  }),

  http.get(`${API_BASE_URL}/backtests`, () => {
    return HttpResponse.json({
      items: [mockBacktestResult],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1
    });
  }),

  http.delete(`${API_BASE_URL}/backtests/:id`, () => {
    return HttpResponse.json({ message: 'Backtest deleted successfully' });
  }),

  // Job endpoints
  http.post(`${API_BASE_URL}/jobs`, () => {
    return HttpResponse.json(mockJobs[0]);
  }),

  http.get(`${API_BASE_URL}/jobs/:id/status`, ({ params }) => {
    return HttpResponse.json({
      ...mockJobs[0],
      id: params.id
    });
  }),

  http.get(`${API_BASE_URL}/jobs/:id/results`, ({ params }) => {
    return HttpResponse.json({
      ...mockBacktestResult,
      id: params.id
    });
  }),

  http.get(`${API_BASE_URL}/jobs`, () => {
    return HttpResponse.json({
      items: mockJobs,
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1
    });
  }),

  // Strategy endpoints
  http.get(`${API_BASE_URL}/strategies`, () => {
    return HttpResponse.json({
      items: mockStrategies,
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1
    });
  }),

  http.get(`${API_BASE_URL}/strategies/:id`, ({ params }) => {
    return HttpResponse.json({
      ...mockStrategies[0],
      id: params.id
    });
  }),

  // Dataset endpoints
  http.get(`${API_BASE_URL}/datasets`, () => {
    return HttpResponse.json({
      items: mockDatasets,
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1
    });
  }),

  http.get(`${API_BASE_URL}/datasets/:id`, ({ params }) => {
    return HttpResponse.json({
      ...mockDatasets[0],
      id: params.id
    });
  }),

  // Dataset download endpoint (returns CSV blob-like response)
  http.get(`${API_BASE_URL}/datasets/:id/download`, ({ params }) => {
    const csv = 'timestamp,open,high,low,close,volume\n2024-01-01T09:15:00,100,101,99,100.5,1000\n';
    return new HttpResponse(csv, {
      status: 200,
      headers: {
        'Content-Type': 'text/csv',
        'Content-Disposition': `attachment; filename="dataset_${String(params.id)}.csv"`,
      },
    });
  }),

  // Analytics endpoints
  http.get(`${API_BASE_URL}/analytics/performance/:id`, () => {
    return HttpResponse.json(mockAnalytics.performance);
  }),

  http.get(`${API_BASE_URL}/analytics/charts/:id`, () => {
    return HttpResponse.json(mockAnalytics.charts);
  }),

  http.get(`${API_BASE_URL}/analytics/charts/:id/equity`, () => {
    return HttpResponse.json(mockAnalytics.charts.equity);
  }),

  http.get(`${API_BASE_URL}/analytics/charts/:id/drawdown`, () => {
    return HttpResponse.json(mockAnalytics.charts.drawdown);
  }),

  http.get(`${API_BASE_URL}/analytics/charts/:id/returns`, () => {
    return HttpResponse.json({
      x: ['2024-01-01', '2024-01-02', '2024-01-03'],
      y: [0, 1.0, 2.0],
      type: 'scatter',
      mode: 'lines'
    });
  }),

  http.get(`${API_BASE_URL}/analytics/charts/:id/trades`, () => {
    return HttpResponse.json({
      x: ['2024-01-01', '2024-01-02', '2024-01-03'],
      y: [1, 2, 1],
      type: 'bar'
    });
  }),

  http.get(`${API_BASE_URL}/analytics/charts/:id/monthly_returns`, () => {
    return HttpResponse.json({
      x: ['Jan', 'Feb', 'Mar'],
      y: [2.5, 1.8, 3.2],
      type: 'bar'
    });
  }),

  http.post(`${API_BASE_URL}/analytics/compare`, () => {
    return HttpResponse.json({
      strategies: [
        { name: 'Strategy 1', metrics: mockAnalytics.performance },
        { name: 'Strategy 2', metrics: { ...mockAnalytics.performance, total_return: 18.2 } }
      ]
    });
  }),

  // Error responses for testing
  http.get(`${API_BASE_URL}/error`, () => {
    return HttpResponse.json(
      { message: 'Internal server error' },
      { status: 500 }
    );
  }),

  http.get(`${API_BASE_URL}/not-found`, () => {
    return HttpResponse.json(
      { message: 'Not found' },
      { status: 404 }
    );
  })
];
