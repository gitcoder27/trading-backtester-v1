/**
 * Tests for useTradingViewChart hook
 */
import { renderHook, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach, type Mock } from 'vitest'
import React, { createRef } from 'react'

import { useTradingViewChart } from '../useTradingViewChart'
import { createChart } from 'lightweight-charts'
import { getCandlestickOptions } from '../../../utils/chartOptions'

let resizeCallback: ResizeObserverCallback | null = null

class StubResizeObserver {
  constructor(cb: ResizeObserverCallback) {
    resizeCallback = cb
  }
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}

;(global as any).ResizeObserver = StubResizeObserver as any

const applyOptionsMock = vi.fn()
const addSeriesMock = vi.fn()
const removeMock = vi.fn()
const mockChartInstance = {
  applyOptions: applyOptionsMock,
  addSeries: addSeriesMock,
  remove: removeMock,
}

vi.mock('lightweight-charts', () => ({
  createChart: vi.fn(() => mockChartInstance),
  CandlestickSeries: 'CandlestickSeries',
  ColorType: { Solid: 'solid' },
}))

function createContainer(width = 640): HTMLDivElement {
  const el = document.createElement('div') as HTMLDivElement
  Object.defineProperty(el, 'clientWidth', { value: width, configurable: true })
  document.body.appendChild(el)
  return el
}

describe('useTradingViewChart', () => {
  beforeEach(() => {
    resizeCallback = null
    vi.clearAllMocks()
  })

  afterEach(() => {
    document.body.replaceChildren()
  })

  it('does nothing when params.enabled is falsy', () => {
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
    expect(createChart).not.toHaveBeenCalled()
  })

  it('creates chart with provided dimensions when enabled', () => {
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

    expect(createChart).toHaveBeenCalledTimes(1)
    const [[target, options]] = (createChart as Mock).mock.calls
    expect(target).toBe(container)
    expect(options).toMatchObject({ width: 900, height: 420 })
    expect(result.current.ready).toBe(true)
    expect(result.current.chartRef.current).toBe(mockChartInstance as any)
  })

  it('adds candlestick series when withCandles is not false', () => {
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
    expect(options).toMatchObject(getCandlestickOptions())
  })

  it('does not add candlestick series when withCandles is false', () => {
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

  it('applies resize options on ResizeObserver callback', async () => {
    const container = createContainer(500)
    const ref = createRef<HTMLDivElement>()
    ref.current = container

    renderHook(() =>
      useTradingViewChart(ref, {
        height: 300,
        theme: 'light',
        enabled: true,
        isFullscreen: false,
      })
    )

    await waitFor(() => expect(resizeCallback).not.toBeNull())
    resizeCallback?.([{ target: container } as any], {} as any)

    expect(applyOptionsMock).toHaveBeenCalled()
    const call = applyOptionsMock.mock.calls[applyOptionsMock.mock.calls.length - 1][0]
    expect(call).toMatchObject({ width: 500, height: 300 })
  })

  it('uses fullscreen height when enabled during resize', async () => {
    const container = createContainer(640)
    const ref = createRef<HTMLDivElement>()
    ref.current = container

    const originalInnerHeight = window.innerHeight
    Object.defineProperty(window, 'innerHeight', { value: 900, configurable: true })

    renderHook(() =>
      useTradingViewChart(ref, {
        height: 250,
        theme: 'dark',
        enabled: true,
        isFullscreen: true,
      })
    )

    await waitFor(() => expect(resizeCallback).not.toBeNull())
    resizeCallback?.([{ target: container } as any], {} as any)

    const call = applyOptionsMock.mock.calls[applyOptionsMock.mock.calls.length - 1][0]
    expect(call).toMatchObject({ width: 640, height: 800 })

    Object.defineProperty(window, 'innerHeight', { value: originalInnerHeight, configurable: true })
  })

  it('cleans up on unmount', () => {
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
  })
})