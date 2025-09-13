import { describe, it, expect, vi, beforeEach } from 'vitest';
import { showToast } from '../ui/Toast';
import { toast } from 'react-hot-toast';

// Mock react-hot-toast APIs
vi.mock('react-hot-toast', () => {
  return {
    __esModule: true,
    toast: {
      custom: vi.fn(),
      loading: vi.fn().mockReturnValue('toast-id'),
      dismiss: vi.fn(),
      promise: vi.fn(),
    },
    Toaster: () => null,
  };
});

describe('showToast', () => {
  
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows success/error/warning/info toasts', () => {
    showToast.success('ok');
    showToast.error('bad');
    showToast.warning('warn');
    showToast.info('info');
    expect(toast.custom).toHaveBeenCalledTimes(4);
  });

  it('shows loading and dismisses', () => {
    const id = showToast.loading('loading');
    expect(id).toBe('toast-id');
    showToast.dismiss(id);
    expect(toast.dismiss).toHaveBeenCalledWith('toast-id');
  });

  it('wraps promise', () => {
    const p = Promise.resolve(1);
    showToast.promise(p, { loading: 'l', success: 's', error: 'e' });
    expect(toast.promise).toHaveBeenCalled();
  });
});
