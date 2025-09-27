import React from 'react';

interface TradeListPaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

const TradeListPagination: React.FC<TradeListPaginationProps> = ({ page, totalPages, onPageChange }) => {
  if (totalPages <= 1) return null;

  const clampPage = (value: number) => Math.min(Math.max(value, 1), totalPages);

  const goTo = (next: number) => {
    const target = clampPage(next);
    if (target !== page) {
      onPageChange(target);
    }
  };

  const buildPageNumbers = (): Array<number | 'ellipsis'> => {
    if (totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, index) => index + 1);
    }

    const pages: Array<number | 'ellipsis'> = [1];
    const start = Math.max(2, page - 1);
    const end = Math.min(totalPages - 1, page + 1);

    if (start > 2) {
      pages.push('ellipsis');
    }

    for (let value = start; value <= end; value += 1) {
      pages.push(value);
    }

    if (end < totalPages - 1) {
      pages.push('ellipsis');
    }

    pages.push(totalPages);
    return pages;
  };

  const items = buildPageNumbers();

  return (
    <div className="flex items-center justify-end gap-2 text-sm text-gray-600 dark:text-gray-300">
      <button
        type="button"
        onClick={() => goTo(page - 1)}
        disabled={page === 1}
        className="px-2 py-1 rounded-md border border-gray-200 dark:border-gray-700 disabled:opacity-50"
      >
        Prev
      </button>
      {items.map((item, index) =>
        item === 'ellipsis' ? (
          <span key={`ellipsis-${index}`} className="px-2 text-gray-400">
            …
          </span>
        ) : (
          <button
            key={item}
            type="button"
            onClick={() => goTo(item)}
            className={`px-3 py-1 rounded-md border ${
              item === page
                ? 'border-primary-500 bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-300'
                : 'border-gray-200 dark:border-gray-700'
            }`}
          >
            {item}
          </button>
        ),
      )}
      <button
        type="button"
        onClick={() => goTo(page + 1)}
        disabled={page === totalPages}
        className="px-2 py-1 rounded-md border border-gray-200 dark:border-gray-700 disabled:opacity-50"
      >
        Next
      </button>
    </div>
  );
};

export default TradeListPagination;
