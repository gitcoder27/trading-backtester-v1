[Skip to main content](https://tradingview.github.io/lightweight-charts/docs/price-scale#__docusaurus_skipToContent_fallback)

Version: 5.0

On this page

Price Scale (or price axis) is a vertical scale that mostly maps prices to coordinates and vice versa.
The rules of converting depend on a price scale mode, a height of the chart and visible part of the data.

![Price scales](https://tradingview.github.io/lightweight-charts/assets/images/price-scales-5ff372fd08578f74710940c724ad5df4.png)

By default, chart has 2 predefined price scales: `left` and `right`, and an unlimited number of overlay scales.

Only `left` and `right` price scales could be displayed on the chart, all overlay scales are hidden.

If you want to change `left` price scale, you need to use [`leftPriceScale`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ChartOptionsBase#leftpricescale) option, to change `right` price scale use [`rightPriceScale`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ChartOptionsBase#rightpricescale), to change default options for an overlay price scale use [`overlayPriceScales`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ChartOptionsBase#overlaypricescales) option.

Alternatively, you can use [`IChartApi.priceScale`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/IChartApi#pricescale) method to get an API object of any price scale or [`ISeriesApi.priceScale`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ISeriesApi#pricescale) to get an API object of series' price scale (the price scale that the series is attached to).

## Creating a price scale [​](https://tradingview.github.io/lightweight-charts/docs/price-scale\#creating-a-price-scale "Direct link to Creating a price scale")

By default a chart has only 2 price scales: `left` and `right`.

If you want to create an overlay price scale, you can simply assign [`priceScaleId`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/SeriesOptionsCommon#pricescaleid) option to a series (note that a value should be differ from `left` and `right`) and a chart will automatically create an overlay price scale with provided ID.
If a price scale with such ID already exists then a series will be attached to this existing price scale.
Further you can use provided price scale ID to get its corresponding API object via [`IChartApi.priceScale`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/IChartApi#pricescale) method.

## Removing a price scale [​](https://tradingview.github.io/lightweight-charts/docs/price-scale\#removing-a-price-scale "Direct link to Removing a price scale")

The default price scales ( `left` and `right`) cannot be removed, you can only hide them by setting [`visible`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/PriceScaleOptions#visible) option to `false`.

An overlay price scale exists while there is at least 1 series attached to this price scale.
Thus, to remove an overlay price scale remove all series attached to this price scale.
