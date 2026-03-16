import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import SpeedSlider from '../SpeedSlider';

describe('SpeedSlider', () => {
  it('renders slider with current value', () => {
    render(<SpeedSlider value={75} onChange={() => {}} disabled={false} />);
    const slider = screen.getByRole('slider');
    expect(slider.value).toBe('75');
  });

  it('displays percentage label', () => {
    render(<SpeedSlider value={50} onChange={() => {}} disabled={false} />);
    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  it('calls onChange when slider moves', () => {
    const onChange = vi.fn();
    render(<SpeedSlider value={50} onChange={onChange} disabled={false} />);
    fireEvent.change(screen.getByRole('slider'), { target: { value: '80' } });
    expect(onChange).toHaveBeenCalledWith(80);
  });

  it('slider is disabled when disabled=true', () => {
    render(<SpeedSlider value={50} onChange={() => {}} disabled={true} />);
    expect(screen.getByRole('slider')).toBeDisabled();
  });
});
