declare module 'react-plotly.js' {
  import type { CSSProperties, ComponentType } from 'react';
  import type Plotly from 'plotly.js';

  export interface PlotProps {
    data?: Partial<Plotly.PlotData>[] | any[];
    layout?: Partial<Plotly.Layout> | Record<string, unknown>;
    config?: Partial<Plotly.Config> | Record<string, unknown>;
    style?: CSSProperties;
    className?: string;
    useResizeHandler?: boolean;
    onInitialized?: (figure: Plotly.Figure, graphDiv: Plotly.PlotlyHTMLElement) => void;
    onUpdate?: (figure: Plotly.Figure, graphDiv: Plotly.PlotlyHTMLElement) => void;
  }

  const Plot: ComponentType<PlotProps>;
  export default Plot;
}
