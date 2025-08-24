[Skip to main content](https://tradingview.github.io/lightweight-charts/docs/plugins/series-primitives#__docusaurus_skipToContent_fallback)

Version: 5.0

On this page

Primitives are extensions to the series which can define views and renderers to
draw on the chart using
[CanvasRenderingContext2D](https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D).

Primitives are defined by implementing the
[`ISeriesPrimitive`](https://tradingview.github.io/lightweight-charts/docs/api/type-aliases/ISeriesPrimitive) interface. The
interface defines the basic functionality and structure required for creating
custom primitives.

## Views [​](https://tradingview.github.io/lightweight-charts/docs/plugins/series-primitives\#views "Direct link to Views")

The primary purpose of a series primitive is to provide one, or more, views to
the library which contain the state and logic required to draw on the chart
panes.

There are two types of views which are supported within `ISeriesPrimitive` which
are:

- [`IPrimitivePaneView`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/IPrimitivePaneView)
- [`ISeriesPrimitiveAxisView`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ISeriesPrimitiveAxisView)

The library will evoke the following getter functions (if defined) to get
references to the primitive's defined views for the corresponding section of the
chart:

- [`paneViews`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ISeriesPrimitiveBase#paneviews)
- [`priceAxisPaneViews`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ISeriesPrimitiveBase#priceaxispaneviews)
- [`timeAxisPaneViews`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ISeriesPrimitiveBase#timeaxispaneviews)
- [`priceAxisViews`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ISeriesPrimitiveBase#priceaxisviews)
- [`timeAxisViews`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ISeriesPrimitiveBase#timeaxisviews)

The first three views allow drawing on the corresponding panes (main chart pane,
price scale pane, and horizontal time scale pane) using the
[CanvasRenderingContext2D](https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D)
and should implement the `ISeriesPrimitivePaneView` interface.

The views returned by the `priceAxisViews` and `timeAxisViews` getter methods
should implement the `ISeriesPrimitiveAxisView` interface and are used to define
labels to be drawn on the corresponding scales.

Below is a visual example showing the various sections of the chart where a
Primitive can draw.

|     |     |     |
| --- | --- | --- |
|  | [Charting by TradingView](https://www.tradingview.com/?utm_medium=lwc-link&utm_campaign=lwc-chart&utm_source=tradingview.github.io/lightweight-charts/docs/plugins/series-primitives "Charting by TradingView") |  |
|  |  |  |

### IPrimitivePaneView [​](https://tradingview.github.io/lightweight-charts/docs/plugins/series-primitives\#iprimitivepaneview "Direct link to IPrimitivePaneView")

The [`IPrimitivePaneView`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/IPrimitivePaneView)
interface can be used to define a view which provides a renderer (implementing
the
[`IPrimitivePaneRenderer`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/IPrimitivePaneRenderer)
interface) for drawing on the corresponding area of the chart using the
[CanvasRenderingContext2D](https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D)
API. The view can define a
[`zOrder`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/IPrimitivePaneView#zorder) to control where
in the visual stack the drawing will occur (See
[`PrimitivePaneViewZOrder`](https://tradingview.github.io/lightweight-charts/docs/api/type-aliases/PrimitivePaneViewZOrder)
for more information).

Renderers should provide a
[`draw`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/IPrimitivePaneRenderer#draw) method which will
be given a `CanvasRenderingTarget2D` target on which it can draw. Additionally,
a renderer can optionally provide a
[`drawBackground`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/IPrimitivePaneRenderer#drawbackground)
method for drawing beneath other elements on the same zOrder.

tip

`CanvasRenderingTarget2D` is explained in more detail on the [Canvas Rendering Target](https://tradingview.github.io/lightweight-charts/docs/plugins/canvas-rendering-target) page.

#### Interactive Demo of zOrder layers [​](https://tradingview.github.io/lightweight-charts/docs/plugins/series-primitives\#interactive-demo-of-zorder-layers "Direct link to Interactive Demo of zOrder layers")

Below is an interactive demo chart illustrating where each zOrder is drawn
relative to the existing chart elements such as the grid, series, and crosshair.

|     |     |     |
| --- | --- | --- |
|  | [Charting by TradingView](https://www.tradingview.com/?utm_medium=lwc-link&utm_campaign=lwc-chart&utm_source=tradingview.github.io/lightweight-charts/docs/plugins/series-primitives "Charting by TradingView") |  |
|  |  |  |

Allbottomnormal (background)normaltop

### ISeriesPrimitiveAxisView [​](https://tradingview.github.io/lightweight-charts/docs/plugins/series-primitives\#iseriesprimitiveaxisview "Direct link to ISeriesPrimitiveAxisView")

The [`ISeriesPrimitiveAxisView`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ISeriesPrimitiveAxisView)
interface can be used to define a label on the price or time axis.

This interface provides several methods to define the appearance and position of
the label, such as the
[`coordinate`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ISeriesPrimitiveAxisView#coordinate) method,
which should return the desired coordinate for the label on the axis. It also
defines optional methods to set the fixed coordinate, text, text color,
background color, and visibility of the label.

Please see the
[`ISeriesPrimitiveAxisView`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ISeriesPrimitiveAxisView)
interface for more details.

## Lifecycle Methods [​](https://tradingview.github.io/lightweight-charts/docs/plugins/series-primitives\#lifecycle-methods "Direct link to Lifecycle Methods")

Your primitive can use the
[`attached`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ISeriesPrimitiveBase#attached) and
[`detached`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ISeriesPrimitiveBase#detached) lifecycle methods to
manage the lifecycle of the primitive, such as creating or removing external
objects and event handlers.

### attached [​](https://tradingview.github.io/lightweight-charts/docs/plugins/series-primitives\#attached "Direct link to attached")

This method is called when the primitive is attached to a chart. The attached
method is evoked with a
[single argument](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/SeriesAttachedParameter) containing
properties for the chart, series, and a callback to request an update. The
`chart` and `series` properties are references to the chart API and the series
API instances for convenience purposes so that they don't need to be manually
provided within the primitive's constructor (if needed by the primitive).

The `requestUpdate` callback allows the primitive to notify the chart that it
should be updated and redrawn.

### detached [​](https://tradingview.github.io/lightweight-charts/docs/plugins/series-primitives\#detached "Direct link to detached")

This method is called when the primitive is detached from a chart. This can be
used to remove any external objects or event handlers that were created during
the attached lifecycle method.

## Updating Views [​](https://tradingview.github.io/lightweight-charts/docs/plugins/series-primitives\#updating-views "Direct link to Updating Views")

Your primitive should update the views in the
[`updateAllViews()`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ISeriesPrimitiveBase#updateallviews) method
such that when the renderers are evoked, they can draw with the latest
information. The library invokes this method when it wants to update and redraw
the chart. If you would like to notify the library that it should trigger an
update then you can use the `requestUpdate` callback provided by the attached
lifecycle method.

## Extending the Autoscale Info [​](https://tradingview.github.io/lightweight-charts/docs/plugins/series-primitives\#extending-the-autoscale-info "Direct link to Extending the Autoscale Info")

The [`autoscaleInfo()`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ISeriesPrimitiveBase#autoscaleinfo)
method can be provided to extend the base autoScale information of the series.
This can be used to ensure that the chart is automatically scaled correctly to
include all the graphics drawn by the primitive.

Whenever the chart needs to calculate the vertical visible range of the series
within the current time range then it will evoke this method. This method can be
omitted and the library will use the normal autoscale information for the
series. If the method is implemented then the returned values will be merged
with the base autoscale information to define the vertical visible range.

warning

Please note that this method will be evoked very often during
scrolling and zooming of the chart, thus it is recommended that this method is
either simple to execute, or makes use of optimisations such as caching to
ensure that the chart remains responsive.
