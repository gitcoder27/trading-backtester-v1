import { describe, it, expect } from 'vitest';
import { queryClient } from '../queryClient';

describe('queryClient', () => {
  it('has expected default options', () => {
    const opts: any = queryClient.getDefaultOptions();
    expect(opts.queries.staleTime).toBe(1000 * 60 * 5);
    expect(opts.queries.gcTime).toBe(1000 * 60 * 10);
    expect(opts.queries.refetchOnWindowFocus).toBe(false);
    // Retry function retries < 3 and skips 4xx
    const retry = opts.queries.retry as (count: number, err: Error) => boolean;
    expect(retry(0, new Error('HTTP 500'))).toBe(true);
    expect(retry(3, new Error('HTTP 500'))).toBe(false);
    expect(retry(0, new Error('HTTP 404'))).toBe(false);
  });
});

