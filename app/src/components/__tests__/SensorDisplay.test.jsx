import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import SensorDisplay from '../SensorDisplay';

describe('SensorDisplay', () => {
  const defaultProps = {
    ultrasonic: 45.3,
    battery: 7.42,
    batteryWarning: false,
    patrolState: 'idle',
    isPatrolMode: false,
  };

  it('displays ultrasonic distance with unit', () => {
    render(<SensorDisplay {...defaultProps} />);
    expect(screen.getByText('45.3 cm')).toBeInTheDocument();
  });

  it('red color when distance < 20cm', () => {
    render(<SensorDisplay {...defaultProps} ultrasonic={15} />);
    const el = screen.getByText('15.0 cm');
    expect(el).toHaveClass('text-red-500');
  });

  it('yellow color when distance < 40cm', () => {
    render(<SensorDisplay {...defaultProps} ultrasonic={30} />);
    const el = screen.getByText('30.0 cm');
    expect(el).toHaveClass('text-yellow-500');
  });

  it('green color when distance >= 40cm', () => {
    render(<SensorDisplay {...defaultProps} ultrasonic={50} />);
    const el = screen.getByText('50.0 cm');
    expect(el).toHaveClass('text-green-500');
  });

  it('displays battery voltage', () => {
    render(<SensorDisplay {...defaultProps} />);
    expect(screen.getByText('7.42V')).toBeInTheDocument();
  });

  it('shows LOW warning when batteryWarning=true', () => {
    render(<SensorDisplay {...defaultProps} batteryWarning={true} />);
    expect(screen.getByText('LOW!')).toBeInTheDocument();
  });

  it('does not show LOW warning when batteryWarning=false', () => {
    render(<SensorDisplay {...defaultProps} batteryWarning={false} />);
    expect(screen.queryByText('LOW!')).not.toBeInTheDocument();
  });

  it('shows patrol state badge in patrol mode', () => {
    render(<SensorDisplay {...defaultProps} isPatrolMode={true} patrolState="forward" />);
    expect(screen.getByText('forward')).toBeInTheDocument();
  });

  it('does not show patrol state in manual mode', () => {
    render(<SensorDisplay {...defaultProps} isPatrolMode={false} patrolState="forward" />);
    expect(screen.queryByText('Patrol State')).not.toBeInTheDocument();
  });
});
