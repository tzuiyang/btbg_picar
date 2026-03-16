import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ConnectionStatus from '../ConnectionStatus';

describe('ConnectionStatus', () => {
  it('shows "Connected" when isConnected=true', () => {
    render(<ConnectionStatus isConnected={true} isConnecting={false} />);
    expect(screen.getByText('Connected')).toBeInTheDocument();
  });

  it('shows green dot class when connected', () => {
    const { container } = render(<ConnectionStatus isConnected={true} isConnecting={false} />);
    expect(container.querySelector('.status-dot.connected')).toBeInTheDocument();
  });

  it('shows "Connecting..." when isConnecting=true', () => {
    render(<ConnectionStatus isConnected={false} isConnecting={true} />);
    expect(screen.getByText('Connecting...')).toBeInTheDocument();
  });

  it('shows yellow dot class when connecting', () => {
    const { container } = render(<ConnectionStatus isConnected={false} isConnecting={true} />);
    expect(container.querySelector('.status-dot.connecting')).toBeInTheDocument();
  });

  it('shows "Disconnected" when both false', () => {
    render(<ConnectionStatus isConnected={false} isConnecting={false} />);
    expect(screen.getByText('Disconnected')).toBeInTheDocument();
  });

  it('shows red dot class when disconnected', () => {
    const { container } = render(<ConnectionStatus isConnected={false} isConnecting={false} />);
    expect(container.querySelector('.status-dot.disconnected')).toBeInTheDocument();
  });
});
