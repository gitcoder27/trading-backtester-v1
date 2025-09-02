[Skip to main content](https://tradingview.github.io/lightweight-charts/docs/time-scale#__docusaurus_skipToContent_fallback)

Version: 5.0

On this page

## Overview [​](https://tradingview.github.io/lightweight-charts/docs/time-scale\#overview "Direct link to Overview")

Time scale (or time axis) is a horizontal scale that displays the time of data points at the bottom of the chart.

![Time scale](<Base64-Image-Removed>)

The horizontal scale can also represent price or other custom values. Refer to the [Chart types](https://tradingview.github.io/lightweight-charts/docs/chart-types) article for more information.

### Time scale appearance [​](https://tradingview.github.io/lightweight-charts/docs/time-scale\#time-scale-appearance "Direct link to Time scale appearance")

Use [`TimeScaleOptions`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/TimeScaleOptions) to adjust the time scale appearance. You can specify these options in two ways:

- On chart initialization. To do this, provide the desired options as a [`timeScale`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ChartOptionsBase#timescale) parameter when calling [`createChart`](https://tradingview.github.io/lightweight-charts/docs/api/functions/createChart).
- On the fly using either the [`ITimeScaleApi.applyOptions`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ITimeScaleApi#applyoptions) or [`IChartApi.applyOptions`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/IChartApi#applyoptions) method. Both methods produce the same result.

### Time scale API [​](https://tradingview.github.io/lightweight-charts/docs/time-scale\#time-scale-api "Direct link to Time scale API")

Call the [`IChartApi.timeScale`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/IChartApi#timescale) method to get an instance of the [`ITimeScaleApi`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ITimeScaleApi) interface. This interface provides an extensive API for controlling the time scale. For example, you can adjust the visible range, convert a time point or [index](https://tradingview.github.io/lightweight-charts/docs/api/type-aliases/Logical) to a coordinate, and subscribe to events.

```codeBlockLines_e6Vv
chart.timeScale().resetTimeScale();

```

## Visible range [​](https://tradingview.github.io/lightweight-charts/docs/time-scale\#visible-range "Direct link to Visible range")

Visible range is a chart area that is currently visible on the canvas. This area can be measured with both [data](https://tradingview.github.io/lightweight-charts/docs/time-scale#data-range) and [logical](https://tradingview.github.io/lightweight-charts/docs/time-scale#logical-range) range.
Data range usually includes bar timestamps, while logical range has bar indices.

You can adjust the visible range using the following methods:

- [`setVisibleRange`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ITimeScaleApi#setvisiblerange)
- [`getVisibleRange`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ITimeScaleApi#getvisiblerange)
- [`setVisibleLogicalRange`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ITimeScaleApi#setvisiblelogicalrange)
- [`getVisibleLogicalRange`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ITimeScaleApi#getvisiblelogicalrange)

### Data range [​](https://tradingview.github.io/lightweight-charts/docs/time-scale\#data-range "Direct link to Data range")

The data range includes only values from the first to the last bar visible on the chart. If the visible area has empty space, this part of the scale is not included in the data range.

Note that you cannot extrapolate time with the [`setVisibleRange`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ITimeScaleApi#setvisiblerange) method. For example, the chart does not have data prior `2018-01-01` date. If you set the visible range from `2016-01-01`, it will be automatically adjusted to `2018-01-01`.

If you want to adjust the visible range more flexible, operate with the [logical range](https://tradingview.github.io/lightweight-charts/docs/time-scale#logical-range) instead.

### Logical range [​](https://tradingview.github.io/lightweight-charts/docs/time-scale\#logical-range "Direct link to Logical range")

The logical range represents a continuous line of values. These values are logical [indices](https://tradingview.github.io/lightweight-charts/docs/api/type-aliases/Logical) on the scale that illustrated as red lines in the image below:

![Logical range](<Base64-Image-Removed>)

The logical range starts from the first data point across all series, with negative indices before it and positive ones after.

The indices can have fractional parts. The integer part represents the fully visible bar, while the fractional part indicates partial visibility. For example, the `5.2` index means that the fifth bar is fully visible, while the sixth bar is 20% visible.
A half-index, such as `3.5`, represents the middle of the bar.

In the library, the logical range is represented with the [`LogicalRange`](https://tradingview.github.io/lightweight-charts/docs/api/type-aliases/LogicalRange) object. This object has the `from` and `to` properties, which are logical indices on the time scale. For example, the visible logical range on the chart above is approximately from `-4.73` to `5.05`.

The [`setVisibleLogicalRange`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ITimeScaleApi#setvisiblelogicalrange) method allows you to specify the visible range beyond the bounds of the available data. This can be useful for setting a [chart margin](https://tradingview.github.io/lightweight-charts/docs/time-scale#chart-margin) or aligning series visually.

## Chart margin [​](https://tradingview.github.io/lightweight-charts/docs/time-scale\#chart-margin "Direct link to Chart margin")

Margin is the space between the chart's borders and the series. It depends on the following time scale options:

- [`barSpacing`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/TimeScaleOptions#barspacing). The default value is `6`.
- [`rightOffset`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/TimeScaleOptions#rightoffset). The default value is `0`.

You can specify these options as described in [above](https://tradingview.github.io/lightweight-charts/docs/time-scale#time-scale-appearance).

Note that if a series contains only a few data points, the chart may have a large margin on the left side.

![A series with a few points](https://tradingview.github.io/lightweight-charts/assets/images/extra-margin-c1f99247fd0192e01717a0e48e073f13.png)

In this case, you can call the [`fitContent`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ITimeScaleApi#fitcontent) method that adjust the view and fits all data within the chart.

```codeBlockLines_e6Vv
chart.timeScale().fitContent();

```

If calling `fitContent` has no effect, it might be due to how the library displays data.

The library allocates specific width for each data point to maintain consistency between different chart types.
For example, for line series, the plot point is placed at the center of this allocated space, while candlestick series use most of the width for the candle body.
The allocated space for each data point is proportional to the chart width.
As a result, series with fewer data points may have a small margin on both sides.

![Margin](https://tradingview.github.io/lightweight-charts/assets/images/margin-ba3ba588b8212ea7b6415220ab39424a.png)

You can specify the [logical range](https://tradingview.github.io/lightweight-charts/docs/time-scale#logical-range) with the [`setVisibleLogicalRange`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ITimeScaleApi#setvisiblelogicalrange) method to display the series exactly to the edges.
For example, the code sample below adjusts the range by half a bar-width on both sides.

```codeBlockLines_e6Vv
const vr = chart.timeScale().getVisibleLogicalRange();
chart.timeScale().setVisibleLogicalRange({ from: vr.from + 0.5, to: vr.to - 0.5 });

```
