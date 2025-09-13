import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Modal from '../ui/Modal';

const setup = (props?: Partial<React.ComponentProps<typeof Modal>>) => {
  const onClose = vi.fn();
  render(
    <Modal isOpen onClose={onClose} title="Test Modal" {...props}>
      <div>Body</div>
    </Modal>
  );
  return { onClose };
};

describe('Modal', () => {
  it('renders title and content', () => {
    setup();
    expect(screen.getByText('Test Modal')).toBeInTheDocument();
    expect(screen.getByText('Body')).toBeInTheDocument();
  });

  it('closes on overlay click when enabled', () => {
    const { onClose } = setup();
    // Backdrop has aria-hidden
    const backdrop = document.querySelector('[aria-hidden="true"]') as HTMLElement;
    expect(backdrop).toBeTruthy();
    fireEvent.click(backdrop);
    expect(onClose).toHaveBeenCalled();
  });

  it('closes on Escape when enabled', () => {
    const { onClose } = setup({ closeOnEscape: true });
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onClose).toHaveBeenCalled();
  });

  it('locks body scroll when open', () => {
    // Render open
    setup();
    expect(document.body.style.overflow).toBe('hidden');
  });
});

