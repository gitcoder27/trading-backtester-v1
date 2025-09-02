[Skip to main content](https://tradingview.github.io/lightweight-charts/docs/plugins/custom_series#__docusaurus_skipToContent_fallback)

Version: 5.0

On this page

Custom series allow developers to create new types of series with their own data
structures, and rendering logic (implemented using
[CanvasRenderingContext2D](https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D)
methods). These custom series extend the current capabilities of our built-in
series, providing a consistent API which mirrors the built-in chart types.

note

These series are expected to have a uniform width for each data point, which
ensures that the chart maintains a consistent look and feel across all series
types. The only restriction on the data structure is that it should extend the
[`CustomData`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/CustomData) interface (have a valid time
property for each data point).

## Defining a Custom Series [​](https://tradingview.github.io/lightweight-charts/docs/plugins/custom_series\#defining-a-custom-series "Direct link to Defining a Custom Series")

A custom series should implement the
[`ICustomSeriesPaneView`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ICustomSeriesPaneView) interface.
The interface defines the basic functionality and structure required for
creating a custom series view.

It includes the following methods and properties:

### Renderer [​](https://tradingview.github.io/lightweight-charts/docs/plugins/custom_series\#renderer "Direct link to Renderer")

- ICustomSeriesPaneView property:
[`renderer`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ICustomSeriesPaneView#renderer)

This method should return a renderer which implements the
[`ICustomSeriesPaneRenderer`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ICustomSeriesPaneRenderer)
interface and is used to draw the series data on the main chart pane.

The [`draw`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ICustomSeriesPaneRenderer#draw) method of the
renderer is evoked whenever the chart needs to draw the series.

The [`PriceToCoordinateConverter`](https://tradingview.github.io/lightweight-charts/docs/api/type-aliases/PriceToCoordinateConverter)
provided as the 2nd argument to the draw method is a convenience function for
changing prices into vertical coordinate values. It is provided since the
series' original data will most likely be defined in price values, and the
renderer needs to draw with coordinates. The values returned by the converter
will be defined in mediaSize (unscaled by `devicePixelRatio`).

tip

`CanvasRenderingTarget2D` provided within the `draw` function is explained in
more detail on the [Canvas Rendering Target](https://tradingview.github.io/lightweight-charts/docs/plugins/canvas-rendering-target) page.

### Update [​](https://tradingview.github.io/lightweight-charts/docs/plugins/custom_series\#update "Direct link to Update")

- ICustomSeriesPaneView property:
[`update`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ICustomSeriesPaneView#update)

This method will be called with the latest data for the renderer to use during
the next paint.

The update method is evoked with two parameters: `data` (discussed below), and
`seriesOptions`. seriesOptions is a reference to the currently applied options
for the series

The [`PaneRendererCustomData`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/PaneRendererCustomData)
interface provides the data that can be used within the renderer for drawing the
series data. It includes the following properties:

- `bars`: List of all the series' items and their x coordinates. See
[`CustomBarItemData`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/CustomBarItemData) for more details
- `barSpacing`: Spacing between consecutive bars.
- `visibleRange`: The current visible range of items on the chart.

### Price Value Builder [​](https://tradingview.github.io/lightweight-charts/docs/plugins/custom_series\#price-value-builder "Direct link to Price Value Builder")

- ICustomSeriesPaneView property:
[`priceValueBuilder`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ICustomSeriesPaneView#pricevaluebuilder)

A function for interpreting the custom series data and returning an array of
numbers representing the prices values for the item, specifically the equivalent
highest, lowest, and current price values for the data item.

These price values are used by the chart to determine the auto-scaling (to
ensure the items are in view) and the crosshair and price line positions. The
largest and smallest values in the array will be used to specify the visible
range of the painted item, and the last value will be used for the crosshair and
price line position.

### Whitespace [​](https://tradingview.github.io/lightweight-charts/docs/plugins/custom_series\#whitespace "Direct link to Whitespace")

- ICustomSeriesPaneView property:
[`isWhitespace`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ICustomSeriesPaneView#iswhitespace)

A function used by the library to determine which data points provided by the
user should be considered Whitespace. The method should return `true` when the
data point is Whitespace. Data points which are whitespace data won't be provided to
the renderer, or the `priceValueBuilder`.

### Default Options [​](https://tradingview.github.io/lightweight-charts/docs/plugins/custom_series\#default-options "Direct link to Default Options")

- ICustomSeriesPaneView property:
[`defaultOptions`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ICustomSeriesPaneView#defaultoptions)

The default options to be used for the series. The user can override these
values using the options argument in
[`addCustomSeries`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/IChartApi#addcustomseries), or via the
[`applyOptions`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ISeriesApi#applyoptions) method on the
`ISeriesAPI`.

### Destroy [​](https://tradingview.github.io/lightweight-charts/docs/plugins/custom_series\#destroy "Direct link to Destroy")

- ICustomSeriesPaneView property:
[`destroy`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ICustomSeriesPaneView#destroy)

This method will be evoked when the series has been removed from the chart. This
method should be used to clean up any objects, references, and other items that
could potentially cause memory leaks.

This method should contain all the necessary code to clean up the object before
it is removed from memory. This includes removing any event listeners or timers
that are attached to the object, removing any references to other objects, and
resetting any values or properties that were modified during the lifetime of the
object.
