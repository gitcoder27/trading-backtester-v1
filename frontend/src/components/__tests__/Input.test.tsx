import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Input, { Textarea, Select } from '../ui/Input';

// Simple stub icon component
const StubIcon = (props: any) => <svg data-testid="icon" {...props} />;

describe('Input', () => {
  it('renders label, helpText and error', () => {
    render(
      <Input label="Name" helpText="Enter name" placeholder="type" />
    );
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Enter name')).toBeInTheDocument();

    // With error overrides helpText
    render(
      <Input label="Email" error="Invalid" />
    );
    expect(screen.getByText('Invalid')).toBeInTheDocument();
  });

  it('supports icons left and right and className', () => {
    const { rerender } = render(
      <Input icon={StubIcon as any} iconPosition="left" className="extra" />
    );
    expect(screen.getAllByTestId('icon')[0]).toBeInTheDocument();

    rerender(<Input icon={StubIcon as any} iconPosition="right" />);
    expect(screen.getAllByTestId('icon')[0]).toBeInTheDocument();
  });
});

describe('Textarea', () => {
  it('renders and supports variants and resize options', () => {
    const { rerender } = render(<Textarea label="Notes" />);
    expect(screen.getByText('Notes')).toBeInTheDocument();

    rerender(<Textarea error="Required" />);
    expect(screen.getByText('Required')).toBeInTheDocument();

    rerender(<Textarea resize="horizontal" />);
    // No visual assertion needed, ensure it renders
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });
});

describe('Select', () => {
  it('renders placeholder and children', () => {
    render(
      <Select label="Opt" placeholder="Pick one">
        <option value="1">One</option>
      </Select>
    );
    expect(screen.getByText('Opt')).toBeInTheDocument();
    expect(screen.getByText('Pick one')).toBeInTheDocument();
    expect(screen.getByText('One')).toBeInTheDocument();
  });
});

