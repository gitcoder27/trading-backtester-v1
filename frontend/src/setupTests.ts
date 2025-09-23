// Global test setup (Jest/Vitest)
// Polyfill ResizeObserver for jsdom where missing

if (!(globalThis as any).ResizeObserver) {
  class ResizeObserver {
    private cb: ResizeObserverCallback
    constructor(cb: ResizeObserverCallback) { this.cb = cb }
    observe(target: Element) { this.cb([{ target } as any], this as any) }
    unobserve() {}
    disconnect() {}
  }
  (globalThis as any).ResizeObserver = ResizeObserver as any
}