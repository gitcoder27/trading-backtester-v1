import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { useInView } from '../useInView';

// Mock IntersectionObserver
class IO {
  callback: IntersectionObserverCallback;
  constructor(cb: IntersectionObserverCallback) {
    this.callback = cb;
  }
  observe = (el: Element) => {
    // Immediately call as visible
    this.callback([{ isIntersecting: true, target: el } as any], this as any);
  };
  unobserve = () => {};
  disconnect = () => {};
}
// @ts-expect-error override global
global.IntersectionObserver = IO;

const Demo = () => {
  const { ref, inView } = useInView({ once: true });
  return (
    <div>
      <div ref={ref}>target</div>
      <span data-testid="state">{String(inView)}</span>
    </div>
  );
};

describe('useInView', () => {
  it('sets inView true when intersecting', () => {
    render(<Demo />);
    expect(screen.getByTestId('state').textContent).toBe('true');
  });
});

