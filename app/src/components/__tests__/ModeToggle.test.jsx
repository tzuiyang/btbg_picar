import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ModeToggle from '../ModeToggle';

describe('ModeToggle', () => {
  it('renders Manual and Patrol labels', () => {
    render(<ModeToggle mode="manual" onChange={() => {}} disabled={false} />);
    expect(screen.getByText('MANUAL')).toBeInTheDocument();
    expect(screen.getByText('PATROL')).toBeInTheDocument();
  });

  it('calls onChange with "patrol" when in manual mode and clicked', () => {
    const onChange = vi.fn();
    const { container } = render(<ModeToggle mode="manual" onChange={onChange} disabled={false} />);
    fireEvent.click(container.querySelector('.mode-toggle'));
    expect(onChange).toHaveBeenCalledWith('patrol');
  });

  it('calls onChange with "manual" when in patrol mode and clicked', () => {
    const onChange = vi.fn();
    const { container } = render(<ModeToggle mode="patrol" onChange={onChange} disabled={false} />);
    fireEvent.click(container.querySelector('.mode-toggle'));
    expect(onChange).toHaveBeenCalledWith('manual');
  });

  it('does not call onChange when disabled', () => {
    const onChange = vi.fn();
    const { container } = render(<ModeToggle mode="manual" onChange={onChange} disabled={true} />);
    fireEvent.click(container.querySelector('.mode-toggle'));
    expect(onChange).not.toHaveBeenCalled();
  });

  it('has opacity-50 class when disabled', () => {
    const { container } = render(<ModeToggle mode="manual" onChange={() => {}} disabled={true} />);
    expect(container.querySelector('.mode-toggle')).toHaveClass('opacity-50');
  });
});
