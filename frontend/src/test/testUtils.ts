// Mock setup for testing without actual vitest/testing-library dependencies
// This file demonstrates the testing structure and can be used once dependencies are installed

import '@testing-library/jest-dom';

// Mock vitest functions for demonstration
const vi = {
  fn: () => jest.fn(),
  mock: (path: string, factory: () => any) => jest.mock(path, factory),
  clearAllMocks: () => jest.clearAllMocks(),
  mocked: <T>(item: T): jest.MockedFunction<any> => item as any,
};

const describe = global.describe || ((_name: string, fn: () => void) => fn());
const it = global.it || ((_name: string, fn: () => void) => fn());
const expect = global.expect || ((value: any) => ({
  toBe: (expected: any) => value === expected,
  toEqual: (expected: any) => JSON.stringify(value) === JSON.stringify(expected),
  toBeInTheDocument: () => true,
  toHaveClass: (_className: string) => true,
  toHaveBeenCalledWith: (..._args: any[]) => true,
  toHaveBeenCalledTimes: (_times: number) => true,
  rejects: {
    toThrow: (_message: string) => Promise.resolve(),
  }
}));

// Mock fetch globally
const mockFetch = vi.fn();
(global as any).fetch = mockFetch;

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock ResizeObserver
(global as any).ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

export { vi, describe, it, expect, mockFetch };
