import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Plus, Download } from 'lucide-react';
import Button from '../ui/Button';

describe('Button Component', () => {
  it('should render button with default props', () => {
    render(<Button>Click me</Button>);
    
    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('btn', 'btn-primary', 'btn-md');
  });

  it('should render different button variants', () => {
    const { rerender } = render(<Button variant="secondary">Secondary</Button>);
    expect(screen.getByRole('button')).toHaveClass('btn-secondary');

    rerender(<Button variant="danger">Danger</Button>);
    expect(screen.getByRole('button')).toHaveClass('btn-danger');

    rerender(<Button variant="outline">Outline</Button>);
    expect(screen.getByRole('button')).toHaveClass('btn-outline');
  });

  it('should render different button sizes', () => {
    const { rerender } = render(<Button size="xs">Extra Small</Button>);
    expect(screen.getByRole('button')).toHaveClass('btn-xs');

    rerender(<Button size="lg">Large</Button>);
    expect(screen.getByRole('button')).toHaveClass('btn-lg');

    rerender(<Button size="xl">Extra Large</Button>);
    expect(screen.getByRole('button')).toHaveClass('btn-xl');
  });

  it('should render full width button', () => {
    render(<Button fullWidth>Full Width</Button>);
    
    const button = screen.getByRole('button');
    expect(button).toHaveClass('w-full');
  });

  it('should render button with left icon', () => {
    render(
      <Button icon={Plus} iconPosition="left">
        Add Item
      </Button>
    );
    
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
    
    // Check if Plus icon is rendered (would need to mock lucide-react for proper testing)
    const svg = button.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  it('should render button with right icon', () => {
    render(
      <Button icon={Download} iconPosition="right">
        Download
      </Button>
    );
    
    const button = screen.getByRole('button');
    const svg = button.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  it('should handle button click events', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('should be disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled Button</Button>);
    
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  it('should be disabled when loading is true', () => {
    render(<Button loading>Loading Button</Button>);
    
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  it('should show loading spinner when loading', () => {
    render(<Button loading>Loading</Button>);
    
    const button = screen.getByRole('button');
    const spinner = button.querySelector('.spinner-md');
    expect(spinner).toBeInTheDocument();
  });

  it('should hide icon when loading', () => {
    render(
      <Button icon={Plus} loading>
        Loading with Icon
      </Button>
    );
    
    const button = screen.getByRole('button');
    // When loading, icon should be hidden and only spinner shown
    const icons = button.querySelectorAll('svg');
    expect(icons.length).toBeLessThanOrEqual(1); // Only spinner, no Plus icon
  });

  it('should apply custom className', () => {
    render(<Button className="custom-class">Custom</Button>);
    
    const button = screen.getByRole('button');
    expect(button).toHaveClass('custom-class');
  });

  it('should pass through other HTML button props', () => {
    render(<Button type="submit" id="submit-btn">Submit</Button>);
    
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('type', 'submit');
    expect(button).toHaveAttribute('id', 'submit-btn');
  });

  it('should render without children (icon-only button)', () => {
    render(<Button icon={Plus} aria-label="Add item" />);
    
    const button = screen.getByRole('button', { name: /add item/i });
    expect(button).toBeInTheDocument();
    
    const svg = button.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  it('should handle different loading spinner sizes', () => {
    const { rerender } = render(<Button loading size="xs">Loading XS</Button>);
    expect(screen.getByRole('button').querySelector('.spinner-sm')).toBeInTheDocument();

    rerender(<Button loading size="sm">Loading SM</Button>);
    expect(screen.getByRole('button').querySelector('.spinner-sm')).toBeInTheDocument();

    rerender(<Button loading size="lg">Loading LG</Button>);
    expect(screen.getByRole('button').querySelector('.spinner-md')).toBeInTheDocument();
  });

  describe('Accessibility', () => {
    it('should be focusable', () => {
      render(<Button>Focusable</Button>);
      
      const button = screen.getByRole('button');
      button.focus();
      expect(button).toHaveFocus();
    });

    it('should support keyboard navigation', () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick}>Keyboard Test</Button>);
      
      const button = screen.getByRole('button');
      button.focus();
      
      fireEvent.keyDown(button, { key: 'Enter' });
      expect(handleClick).toHaveBeenCalledTimes(1);
      
      fireEvent.keyDown(button, { key: ' ' });
      expect(handleClick).toHaveBeenCalledTimes(2);
    });

    it('should have proper ARIA attributes when disabled', () => {
      render(<Button disabled>Disabled</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('disabled');
    });
  });

  describe('Edge cases', () => {
    it('should handle undefined children gracefully', () => {
      render(<Button>{undefined}</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('should handle empty string children', () => {
      render(<Button>{''}</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('should handle multiple children types', () => {
      render(
        <Button>
          <span>Text</span>
          <strong>Bold</strong>
        </Button>
      );
      
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('TextBold');
    });
  });
});
