import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import FileUpload from '../ui/FileUpload';

// Mock FileReader to immediately return CSV content
class MockFileReader {
  public onload: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  readAsText() {
    setTimeout(() => {
      const ev = { target: { result: 'timestamp,open,high,low,close\n2024-01-01,1,1,1,1' } } as any;
      this.onload?.call(this as any, ev);
    }, 0);
  }
}

describe('FileUpload', () => {
  const orig = global.FileReader;
  beforeEach(() => {
    // @ts-expect-error override
    global.FileReader = MockFileReader as any;
  });
  afterAll(() => {
    // @ts-expect-error restore
    global.FileReader = orig as any;
  });

  it('validates and selects CSV file', async () => {
    const onSelect = vi.fn();
    render(<FileUpload onFileSelect={onSelect} />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['a,b'], 'data.csv', { type: 'text/csv' });
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => expect(onSelect).toHaveBeenCalled());
    expect(screen.getByText('data.csv')).toBeInTheDocument();
  });

  it('shows error for wrong type', async () => {
    const onSelect = vi.fn();
    render(<FileUpload onFileSelect={onSelect} acceptedTypes={[".csv"]} />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['data'], 'file.txt', { type: 'text/plain' });
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText(/not supported/i)).toBeInTheDocument();
    });
    expect(onSelect).not.toHaveBeenCalled();
  });
});

