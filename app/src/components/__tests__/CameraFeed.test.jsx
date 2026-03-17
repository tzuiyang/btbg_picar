import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import CameraFeed from '../CameraFeed';

describe('CameraFeed', () => {
  it('renders img element with correct stream URL', () => {
    render(<CameraFeed host="10.42.0.1" port={8080} available={true} />);
    const img = screen.getByAltText('Camera feed');
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute('src', 'http://10.42.0.1:8080/stream');
  });

  it('constructs URL from host and port props', () => {
    render(<CameraFeed host="192.168.1.50" port={9999} available={true} />);
    const img = screen.getByAltText('Camera feed');
    expect(img).toHaveAttribute('src', 'http://192.168.1.50:9999/stream');
  });

  it('shows "Camera unavailable" when available=false', () => {
    render(<CameraFeed host="10.42.0.1" port={8080} available={false} />);
    expect(screen.getByText('Camera unavailable')).toBeInTheDocument();
    expect(screen.queryByAltText('Camera feed')).not.toBeInTheDocument();
  });

  it('has correct aspect ratio class', () => {
    render(<CameraFeed host="10.42.0.1" port={8080} available={true} />);
    const img = screen.getByAltText('Camera feed');
    expect(img).toHaveClass('aspect-[4/3]');
  });
});
