/**
 * Tests for useTradingViewChart hook
 *
 * Framework/Libraries:
 * - Expecting Jest or Vitest
 * - @testing-library/react for renderHook
 *
 * These tests mock 'lightweight-charts' and polyfill ResizeObserver for jsdom.
 */
import { renderHook, act } from '@testing-library/react'
import React, { createRef } from 'react'

// Adjust import path if needed depending on repository structure
import { useTradingViewChart } from '../useTradingViewChart'

// Polyfill ResizeObserver if not provided by test environment
class MockResizeObserver {
  private cb: ResizeObserverCallback
  constructor(cb: ResizeObserverCallback) { this.cb = cb }
  observe() { /* noop */ }
  unobserve() { /* noop */ }
  disconnect() { /* noop */ }
}
if (!(global as any).ResizeObserver) {
  (global as any).ResizeObserver = MockResizeObserver as any
}

// Mocks for lightweight-charts
const applyOptionsMock = jest.fn()
const addSeriesMock = jest.fn()
const removeMock = jest.fn()
const mockChartInstance = {
  applyOptions: applyOptionsMock,
  addSeries: addSeriesMock,
  remove: removeMock,
}

jest.mock('lightweight-charts', () => {
  return {
    // Types are erased at runtime; we only need the runtime shape
    createChart: jest.fn(() => mockChartInstance),
    // CandlestickSeries is passed as a "series type" token; any value works
    CandlestickSeries: 'CandlestickSeries',
    // Re-exported types are not needed at runtime
  }
})

// Mock utils returning deterministic options
jest.mock('../../utils/chartOptions', () => ({
  getChartOptions: jest.fn(() => ({ layout: { textColor: 'black' } })),
  getCandlestickOptions: jest.fn(() => ({ upColor: 'green', downColor: 'red' })),
}))

// Utility to build a container with controllable clientWidth
function createContainer(width = 640): HTMLDivElement {
  const el = document.createElement('div') as HTMLDivElement
  Object.defineProperty(el, 'clientWidth', { value: width, configurable: true })
  document.body.appendChild(el)
  return el
}

describe('useTradingViewChart', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  afterEach(() => {
    document.body.replaceChildren()
  })

  test('does nothing when params.enabled is falsy', () => {
    const container = createContainer(800)
    const ref = createRef<HTMLDivElement>()
    ref.current = container

    const { result } = renderHook(() =>
      useTradingViewChart(ref, {
        height: 300,
        theme: 'light',
        enabled: false,
        withCandles: true,
      })
    )

    expect(result.current.ready).toBe(false)
    expect((require('lightweight-charts') as any).createChart).not.toHaveBeenCalled()
  })

  test('creates chart with provided dimensions and theme when enabled', () => {
    const container = createContainer(900)
    const ref = createRef<HTMLDivElement>()
    ref.current = container

    const { result } = renderHook(() =>
      useTradingViewChart(ref, {
        height: 420,
        theme: 'dark',
        timeZone: 'UTC',
        enabled: true,
        withCandles: true,
      })
    )

    const { createChart } = require('lightweight-charts') as any
    expect(createChart).toHaveBeenCalledTimes(1)
    const callArgs = (createChart as jest.Mock).mock.calls[0]
    expect(callArgs[0]).toBe(container)
    expect(callArgs[1]).toMatchObject({
      width: 900,
      height: 420,
      layout: { textColor: 'black' }, // from mocked getChartOptions
    })
    expect(result.current.ready).toBe(true)
    expect(result.current.chartRef.current).toBe(mockChartInstance)
  })

  test('adds candlestick series when withCandles is not false', () => {
    const container = createContainer(700)
    const ref = createRef<HTMLDivElement>()
    ref.current = container

    renderHook(() =>
      useTradingViewChart(ref, {
        height: 360,
        theme: 'light',
        enabled: true,
        withCandles: true,
      })
    )

    expect(addSeriesMock).toHaveBeenCalledTimes(1)
    const [seriesType, options] = addSeriesMock.mock.calls[0]
    expect(seriesType).toBe('CandlestickSeries')
    expect(options).toEqual({ upColor: 'green', downColor: 'red' })
  })

  test('does not add candlestick series when withCandles is false', () => {
    const container = createContainer(700)
    const ref = createRef<HTMLDivElement>()
    ref.current = container

    renderHook(() =>
      useTradingViewChart(ref, {
        height: 360,
        theme: 'light',
        enabled: true,
        withCandles: false,
      })
    )

    expect(addSeriesMock).not.toHaveBeenCalled()
  })

  test('applies resize options on ResizeObserver callback (normal mode)', () => {
    const container = createContainer(500)
    const ref = createRef<HTMLDivElement>()
    ref.current = container

    // Track the latest observer instance to trigger its callback
    const observed: any[] = []
    const RO = (global as any).ResizeObserver
    ;(global as any).ResizeObserver = class extends RO {
      constructor(cb: ResizeObserverCallback) {
        super(cb)
        // Hijack observe to immediately invoke callback with fake entry
        ;(this as any)._cb = cb
      }
      observe(target: Element) {
        observed.push(this)
        // Simulate resize
        ;(this as any)._cb([{ target } as any], this as any)
      }
    }

    renderHook(() =>
      useTradingViewChart(ref, {
        height: 300,
        theme: 'light',
        enabled: true,
        isFullscreen: false,
      })
    )

    expect(applyOptionsMock).toHaveBeenCalled()
    const lastCall = applyOptionsMock.mock.calls.pop()[0]
    expect(lastCall).toMatchObject({ width: 500, height: 300 })
  })

  test('applies fullscreen height on resize when isFullscreen=true', () => {
    const container = createContainer(640)
    const ref = createRef<HTMLDivElement>()
    ref.current = container

    const originalInnerHeight = window.innerHeight
    Object.defineProperty(window, 'innerHeight', { value: 900, configurable: true })

    const RO = (global as any).ResizeObserver
    ;(global as any).ResizeObserver = class extends RO {
      constructor(cb: ResizeObserverCallback) { super(cb); (this as any)._cb = cb }
      observe(target: Element) { (this as any)._cb([{ target } as any], this as any) }
    }

    renderHook(() =>
      useTradingViewChart(ref, {
        height: 250,
        theme: 'dark',
        enabled: true,
        isFullscreen: true,
      })
    )

    const lastCall = applyOptionsMock.mock.calls.pop()[0]
    expect(lastCall).toMatchObject({ width: 640, height: 800 }) // 900 - 100

    // restore
    Object.defineProperty(window, 'innerHeight', { value: originalInnerHeight, configurable: true })
  })

  test('cleans up on unmount: removes chart, clears refs, and resets ready', () => {
    const container = createContainer(800)
    const ref = createRef<HTMLDivElement>()
    ref.current = container

    const { result, unmount } = renderHook(() =>
      useTradingViewChart(ref, {
        height: 320,
        theme: 'light',
        enabled: true,
      })
    )

    expect(result.current.ready).toBe(true)
    unmount()
    expect(removeMock).toHaveBeenCalledTimes(1)
    expect(result.current.chartRef.current).toBeNull()
    expect(result.current.candleSeriesRef.current).toBeNull()
    // ready is internal state; after unmount it's not observable, but we validated cleanup through refs/remove
  })
})