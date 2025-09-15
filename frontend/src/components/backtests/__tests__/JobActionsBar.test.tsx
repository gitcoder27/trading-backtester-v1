import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import JobActionsBar from '../../backtests/JobActionsBar';

describe('JobActionsBar', () => {
  it('shows Download button for completed jobs', async () => {
    const user = userEvent.setup();
    const onDownload = vi.fn();
    render(
      <JobActionsBar
        status="completed"
        isPolling={false}
        onCancel={() => {}}
        onDownload={onDownload}
      /> as any
    );
    expect(screen.getByText('Download Results')).toBeInTheDocument();
    expect(screen.queryByText('Cancel')).toBeNull();
    await user.click(screen.getByText('Download Results'));
    expect(onDownload).toHaveBeenCalled();
  });

  it('shows Cancel and Live updates for running jobs', () => {
    render(
      <JobActionsBar
        status="running"
        isPolling={true}
        onCancel={() => {}}
        onDownload={() => {}}
      /> as any
    );
    expect(screen.getByText('Live updates')).toBeInTheDocument();
    expect(screen.getByText('Cancel')).toBeInTheDocument();
    expect(screen.queryByText('Download Results')).toBeNull();
  });
});
