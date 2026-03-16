import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import CalibrationPanel from '../CalibrationPanel';

vi.mock('../../ros/rosClient', () => ({
  btbgClient: {
    send: vi.fn(),
    onMessage: vi.fn(),
  },
}));

import { btbgClient } from '../../ros/rosClient';

describe('CalibrationPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders Left and Right nudge buttons', () => {
    render(<CalibrationPanel disabled={false} onClose={() => {}} />);
    expect(screen.getByText(/Left/)).toBeInTheDocument();
    expect(screen.getByText(/Right/)).toBeInTheDocument();
  });

  it('clicking Right increments angle by 1 and sends calibrate_steer', () => {
    render(<CalibrationPanel disabled={false} onClose={() => {}} />);
    fireEvent.click(screen.getByText(/Right/));
    expect(btbgClient.send).toHaveBeenCalledWith('calibrate_steer', { angle: 1 });
    expect(screen.getByText('1°')).toBeInTheDocument();
  });

  it('clicking Left decrements angle by 1 and sends calibrate_steer', () => {
    render(<CalibrationPanel disabled={false} onClose={() => {}} />);
    fireEvent.click(screen.getByText(/Left/));
    expect(btbgClient.send).toHaveBeenCalledWith('calibrate_steer', { angle: -1 });
    expect(screen.getByText('-1°')).toBeInTheDocument();
  });

  it('angle is clamped at +20', () => {
    render(<CalibrationPanel disabled={false} onClose={() => {}} />);
    // Click Right 21 times
    for (let i = 0; i < 21; i++) {
      const btn = screen.getByText(/Right/);
      if (!btn.disabled) fireEvent.click(btn);
    }
    expect(screen.getByText('20°')).toBeInTheDocument();
  });

  it('angle is clamped at -20', () => {
    render(<CalibrationPanel disabled={false} onClose={() => {}} />);
    for (let i = 0; i < 21; i++) {
      const btn = screen.getByText(/Left/);
      if (!btn.disabled) fireEvent.click(btn);
    }
    expect(screen.getByText('-20°')).toBeInTheDocument();
  });

  it('displays current angle between buttons', () => {
    render(<CalibrationPanel disabled={false} onClose={() => {}} />);
    // Both current angle and saved offset show "0°"
    const matches = screen.getAllByText('0°');
    expect(matches.length).toBe(2);
  });

  it('displays saved offset value', () => {
    render(<CalibrationPanel disabled={false} onClose={() => {}} />);
    expect(screen.getByText(/Saved offset:/)).toBeInTheDocument();
  });

  it('"Set as Center" sends save_calibration with current angle', () => {
    render(<CalibrationPanel disabled={false} onClose={() => {}} />);
    // Nudge right 3 times
    fireEvent.click(screen.getByText(/Right/));
    fireEvent.click(screen.getByText(/Right/));
    fireEvent.click(screen.getByText(/Right/));
    fireEvent.click(screen.getByText('Set as Center'));
    expect(btbgClient.send).toHaveBeenCalledWith('save_calibration', { steering_offset: 3 });
  });

  it('"Reset to 0" sends calibrate_steer and save_calibration with 0', () => {
    render(<CalibrationPanel disabled={false} onClose={() => {}} />);
    fireEvent.click(screen.getByText('Reset to 0'));
    expect(btbgClient.send).toHaveBeenCalledWith('calibrate_steer', { angle: 0 });
    expect(btbgClient.send).toHaveBeenCalledWith('save_calibration', { steering_offset: 0 });
  });

  it('sends get_calibration on mount', () => {
    render(<CalibrationPanel disabled={false} onClose={() => {}} />);
    expect(btbgClient.send).toHaveBeenCalledWith('get_calibration');
  });

  it('buttons are disabled when disabled=true', () => {
    render(<CalibrationPanel disabled={true} onClose={() => {}} />);
    expect(screen.getByText('Set as Center')).toBeDisabled();
    expect(screen.getByText('Reset to 0')).toBeDisabled();
  });

  it('on unmount sends drive with speed 0 steering 0 (not calibrate_steer)', () => {
    const { unmount } = render(<CalibrationPanel disabled={false} onClose={() => {}} />);
    vi.clearAllMocks();
    unmount();
    expect(btbgClient.send).toHaveBeenCalledWith('drive', { speed: 0, steering: 0 });
    expect(btbgClient.send).not.toHaveBeenCalledWith('calibrate_steer', expect.anything());
  });

  it('calls onClose when X button clicked', () => {
    const onClose = vi.fn();
    render(<CalibrationPanel disabled={false} onClose={onClose} />);
    fireEvent.click(screen.getByText('×'));
    expect(onClose).toHaveBeenCalledOnce();
  });
});
