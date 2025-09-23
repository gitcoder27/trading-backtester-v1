import React from 'react';
import { Maximize2, Download, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

interface IndicatorToggle {
  name: string;
  color: string;
}

interface Props {
  show: boolean;
  indicators: IndicatorToggle[];
  visible: Set<string>;
  onToggleIndicator: (name: string) => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onReset: () => void;
  onDownload: () => void;
  onFullscreen: () => void;
  isFullscreen: boolean;
}

const ChartControls: React.FC<Props> = ({
  show,
  indicators,
  visible,
  onToggleIndicator,
  onZoomIn,
  onZoomOut,
  onReset,
  onDownload,
  onFullscreen,
  isFullscreen,
}) => {
  if (!show) return null;

  return (
    <div className="flex items-center space-x-2">
      {indicators.length > 0 && (
        <div className="flex items-center space-x-2 mr-4">
          {indicators.map((ind) => (
            <button
              key={ind.name}
              onClick={() => onToggleIndicator(ind.name)}
              className={`px-2 py-1 text-xs rounded ${
                visible.has(ind.name) ? 'bg-blue-600 text-white' : 'bg-gray-600 text-gray-300'
              }`}
              style={{ borderLeft: `3px solid ${ind.color}` }}
            >
              {ind.name}
            </button>
          ))}
        </div>
      )}

      <button onClick={onZoomIn} className="p-2 text-gray-400 hover:text-white" title="Zoom In">
        <ZoomIn className="w-4 h-4" />
      </button>
      <button onClick={onZoomOut} className="p-2 text-gray-400 hover:text-white" title="Zoom Out">
        <ZoomOut className="w-4 h-4" />
      </button>
      <button onClick={onReset} className="p-2 text-gray-400 hover:text-white" title="Fit Content">
        <RotateCcw className="w-4 h-4" />
      </button>
      <button onClick={onDownload} className="p-2 text-gray-400 hover:text-white" title="Download PNG">
        <Download className="w-4 h-4" />
      </button>
      <button onClick={onFullscreen} className="p-2 text-gray-400 hover:text-white" title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}>
        <Maximize2 className="w-4 h-4" />
      </button>
    </div>
  );
};

export default ChartControls;

