import { describe, it, expect, vi, beforeEach } from 'vitest';

const mockApi = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
}));

vi.mock('../api', () => ({
  apiClient: mockApi,
}));

import { StrategyService } from '../strategyService';

describe('StrategyService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('discovers strategies', async () => {
    mockApi.get.mockResolvedValue({ strategies: [{ id: '1' }] });
    const result = await StrategyService.discoverStrategies();
    expect(mockApi.get).toHaveBeenCalledWith('/strategies/discover');
    expect(result).toEqual([{ id: '1' }]);
  });

  it('registers strategies', async () => {
    mockApi.post.mockResolvedValue({ success: true, registered: 1, updated: 0, errors: [] });
    const response = await StrategyService.registerStrategies(['1']);
    expect(mockApi.post).toHaveBeenCalledWith('/strategies/register', { strategy_ids: ['1'] });
    expect(response.registered).toBe(1);
  });

  it('retrieves strategies list', async () => {
    mockApi.get.mockResolvedValueOnce({ strategies: [{ id: '1' }], total: 1, success: true });
    const strategies = await StrategyService.getStrategies();
    expect(mockApi.get).toHaveBeenCalledWith('/strategies/');
    expect(strategies).toHaveLength(1);
  });

  it('gets strategy details and schema', async () => {
    mockApi.get.mockResolvedValueOnce({ id: '1' });
    await StrategyService.getStrategy('1');
    expect(mockApi.get).toHaveBeenCalledWith('/strategies/1');

    mockApi.get.mockResolvedValueOnce([{ name: 'lookback' }]);
    await StrategyService.getStrategySchema('1');
    expect(mockApi.get).toHaveBeenCalledWith('/strategies/1/schema');
  });

  it('validates strategies', async () => {
    mockApi.post.mockResolvedValue({ is_valid: true, errors: [], warnings: [], parameter_schema: [] });
    await StrategyService.validateStrategy('1', { lookback: 10 });
    expect(mockApi.post).toHaveBeenCalledWith('/strategies/1/validate', { parameters: { lookback: 10 } });

    await StrategyService.validateStrategyByPath({ module_path: 'strategies.test' });
    expect(mockApi.post).toHaveBeenCalledWith('/strategies/validate-by-path', { module_path: 'strategies.test' });
  });

  it('updates and deletes strategies', async () => {
    mockApi.put.mockResolvedValue({ id: '1' });
    await StrategyService.updateStrategy('1', { name: 'Updated' });
    expect(mockApi.put).toHaveBeenCalledWith('/strategies/1', { name: 'Updated' });

    mockApi.delete.mockResolvedValue({ success: true });
    await StrategyService.deleteStrategy('1');
    expect(mockApi.delete).toHaveBeenCalledWith('/strategies/1');
  });

  it('fetches stats and toggles strategy', async () => {
    mockApi.get.mockResolvedValueOnce({ total_strategies: 5 });
    await StrategyService.getStrategyStats();
    expect(mockApi.get).toHaveBeenCalledWith('/strategies/stats/summary');

    mockApi.put.mockResolvedValue({ id: '1', is_active: false });
    await StrategyService.toggleStrategy('1', false);
    expect(mockApi.put).toHaveBeenCalledWith('/strategies/1', { is_active: false });
  });

  it('handles strategy source code flows', async () => {
    mockApi.get.mockResolvedValue({
      strategy_id: 1,
      module_path: 'strategies.sample',
      file_path: '/strategies/sample.py',
      content: 'print()',
    });
    const code = await StrategyService.getStrategyCode('1');
    expect(code.content).toBe('print()');

    mockApi.put.mockResolvedValue({
      strategy_id: 1,
      module_path: 'strategies.sample',
      file_path: '/strategies/sample.py',
      updated: true,
    });
    const update = await StrategyService.updateStrategyCode('1', 'print("hi")');
    expect(update.updated).toBe(true);

    mockApi.post.mockResolvedValue({
      module_path: 'strategies.new',
      file_path: '/strategies/new.py',
      created: true,
      registration: { success: true, registered: 1, updated: 0 },
    });
    const created = await StrategyService.createStrategyFile({ file_name: 'new.py', content: 'print()' });
    expect(mockApi.post).toHaveBeenCalledWith('/strategies/code', { file_name: 'new.py', content: 'print()' });
    expect(created.created).toBe(true);
  });
});
