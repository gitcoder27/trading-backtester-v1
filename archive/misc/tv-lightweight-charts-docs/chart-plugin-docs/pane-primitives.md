[Skip to main content](https://tradingview.github.io/lightweight-charts/docs/plugins/pane-primitives#__docusaurus_skipToContent_fallback)

Version: 5.0

On this page

In addition to Series Primitives, the library now supports Pane Primitives. These are essentially the same as Series Primitives but are designed to draw on the pane of a chart rather than being associated with a specific series. Pane Primitives can be used for features like watermarks or other chart-wide annotations.

## Key Differences from Series Primitives [​](https://tradingview.github.io/lightweight-charts/docs/plugins/pane-primitives\#key-differences-from-series-primitives "Direct link to Key Differences from Series Primitives")

1. Pane Primitives are attached to the chart pane rather than a specific series.
2. They cannot draw on the price and time scales.
3. They are ideal for chart-wide features that are not tied to a particular series.

## Adding a Pane Primitive [​](https://tradingview.github.io/lightweight-charts/docs/plugins/pane-primitives\#adding-a-pane-primitive "Direct link to Adding a Pane Primitive")

Pane Primitives can be added to a chart using the `attachPrimitive` method on the [`IPaneApi`](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/IPaneApi) interface. Here's an example:

```codeBlockLines_e6Vv
const chart = createChart(document.getElementById('container'));
const pane = chart.panes()[0]; // Get the first (main) pane

const myPanePrimitive = new MyCustomPanePrimitive();
pane.attachPrimitive(myPanePrimitive);

```

## Implementing a Pane Primitive [​](https://tradingview.github.io/lightweight-charts/docs/plugins/pane-primitives\#implementing-a-pane-primitive "Direct link to Implementing a Pane Primitive")

To create a Pane Primitive, you should implement the [`IPanePrimitive`](https://tradingview.github.io/lightweight-charts/docs/api/type-aliases/IPanePrimitive) interface. This interface is similar to [`ISeriesPrimitive`](https://tradingview.github.io/lightweight-charts/docs/api/type-aliases/ISeriesPrimitive), but with some key differences:

- It doesn't include methods for drawing on price and time scales.
- The `paneViews` method is used to define what will be drawn on the chart pane.

Here's a basic example of a Pane Primitive implementation:

```codeBlockLines_e6Vv
class MyCustomPanePrimitive {
    paneViews() {
        return [\
            {\
                renderer: {\
                    draw: target => {\
                        // Custom drawing logic here\
                    },\
                },\
            },\
        ];
    }

    // Other methods as needed...
}

```

For more details on implementing Pane Primitives, refer to the [`IPanePrimitive`](https://tradingview.github.io/lightweight-charts/docs/api/type-aliases/IPanePrimitive) interface documentation.
