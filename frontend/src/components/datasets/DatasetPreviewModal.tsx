import React from 'react';
import Modal from '../ui/Modal';
import { DatasetService } from '../../services/dataset';
import type { Dataset, DatasetPreview as PreviewType } from '../../types';

interface Props {
  dataset: Dataset | null;
  isOpen: boolean;
  onClose: () => void;
}

const DatasetPreviewModal: React.FC<Props> = ({ dataset, isOpen, onClose }) => {
  const [preview, setPreview] = React.useState<PreviewType | null>(null);
  const [quality, setQuality] = React.useState<any | null>(null);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    let cancelled = false;
    const load = async () => {
      if (!dataset?.id || !isOpen) return;
      setLoading(true);
      try {
        const [p, q] = await Promise.all([
          DatasetService.previewDataset(dataset.id, 10).catch(() => null),
          DatasetService.getDataQuality(dataset.id).catch(() => null),
        ]);
        if (!cancelled) {
          setPreview(p);
          setQuality(q);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
      setPreview(null);
      setQuality(null);
    };
  }, [dataset?.id, isOpen]);

  const columns = React.useMemo(() => {
    if (!preview) return [] as string[];
    if (Array.isArray(preview.columns) && preview.columns.length > 0) {
      return preview.columns;
    }
    if (Array.isArray(preview.data) && preview.data.length > 0) {
      const firstRow = preview.data[0];
      if (firstRow && typeof firstRow === 'object') {
        return Object.keys(firstRow as Record<string, unknown>);
      }
    }
    return [] as string[];
  }, [preview]);

  const rows = React.useMemo(() => {
    if (!preview) return [] as Array<Record<string, unknown>>;
    if (Array.isArray(preview.data)) {
      return preview.data as Array<Record<string, unknown>>;
    }
    return [] as Array<Record<string, unknown>>;
  }, [preview]);

  if (!dataset) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Preview: ${dataset.name}`} size="xl">
      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Symbol & Timeframe</p>
            <p className="font-medium text-gray-900 dark:text-gray-100">{dataset.symbol} • {dataset.timeframe}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Records</p>
            <p className="font-medium text-gray-900 dark:text-gray-100">{new Intl.NumberFormat().format(dataset.record_count)}</p>
          </div>
        </div>

        <div className="space-y-3">
          <h4 className="font-medium text-gray-900 dark:text-gray-100">Data Quality Analysis</h4>
          {!quality ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">{loading ? 'Analyzing...' : 'No quality data available'}</p>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <p className="text-sm text-gray-600 dark:text-gray-400">Missing Data</p>
                <p className="font-medium text-gray-900 dark:text-gray-100">{Number(quality.missing_data_percentage ?? 0).toFixed(2)}%</p>
              </div>
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <p className="text-sm text-gray-600 dark:text-gray-400">Gaps Detected</p>
                <p className="font-medium text-gray-900 dark:text-gray-100">{quality.gaps_detected ?? 0}</p>
              </div>
            </div>
          )}
        </div>

        <div className="space-y-3">
          <h4 className="font-medium text-gray-900 dark:text-gray-100">Data Preview</h4>
          {!preview ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">{loading ? 'Loading preview...' : 'No preview available'}</p>
          ) : columns.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">No preview columns detected</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    {columns.map((col) => (
                      <th key={col} className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                  {rows.length === 0 ? (
                    <tr>
                      <td colSpan={columns.length} className="px-4 py-6 text-center text-sm text-gray-500 dark:text-gray-400">
                        No preview rows available
                      </td>
                    </tr>
                  ) : (
                    rows.map((row, i) => (
                      <tr key={i}>
                        {columns.map((col) => (
                          <td key={col} className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                            {String((row as Record<string, unknown>)[col] ?? '')}
                          </td>
                        ))}
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
};

export default DatasetPreviewModal;
