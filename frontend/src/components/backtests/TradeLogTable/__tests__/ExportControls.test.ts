import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook } from '@testing-library/react';

import { useExportCSV } from '../ExportControls';

const originalCreate = global.URL.createObjectURL;
const originalRevoke = global.URL.revokeObjectURL;

describe('useExportCSV', () => {
  beforeEach(() => {
    (global.URL as any).createObjectURL = vi.fn(() => 'blob://csv');
    (global.URL as any).revokeObjectURL = vi.fn();
  });

  afterEach(() => {
    (global.URL as any).createObjectURL = originalCreate;
    (global.URL as any).revokeObjectURL = originalRevoke;
    vi.restoreAllMocks();
  });

  it('creates and downloads csv when trades exist', () => {
    const { result } = renderHook(() => useExportCSV());
    const clickMock = vi.fn();
    const anchorMock = {
      href: '',
      download: '',
      click: clickMock,
    } as unknown as HTMLAnchorElement;
    const createElementSpy = vi.spyOn(document, 'createElement').mockReturnValue(anchorMock);

    result.current.exportToCSV([
      {
        entry_time: '2024-01-01T00:00:00Z',
        exit_time: '2024-01-01T01:00:00Z',
        symbol: 'AAPL',
        side: 'buy',
        entry_price: 100,
        exit_price: 110,
        quantity: 10,
        pnl: 100,
        pnl_pct: 10,
        duration: 60,
        fees: 2,
      },
    ] as any, 'bt-1');

    expect(global.URL.createObjectURL).toHaveBeenCalled();
    expect(clickMock).toHaveBeenCalled();
    expect(global.URL.revokeObjectURL).toHaveBeenCalled();
    expect(anchorMock.download).toContain('bt-1');
    createElementSpy.mockRestore();
  });

  it('skips export when no trades provided', () => {
    const { result } = renderHook(() => useExportCSV());
    result.current.exportToCSV([], 'bt-2');
    expect(global.URL.createObjectURL).not.toHaveBeenCalled();
  });
});
