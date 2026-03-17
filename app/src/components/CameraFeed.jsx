import React, { useState } from 'react';

function CameraFeed({ host, port, available }) {
  const [hasError, setHasError] = useState(false);

  if (available === false) {
    return (
      <div className="bg-btbg-darker rounded-lg flex items-center justify-center aspect-[4/3]">
        <span className="text-gray-500">Camera unavailable</span>
      </div>
    );
  }

  if (hasError) {
    return (
      <div className="bg-btbg-darker rounded-lg flex items-center justify-center aspect-[4/3]">
        <span className="text-gray-500">Stream error — waiting for camera</span>
      </div>
    );
  }

  const streamUrl = `http://${host}:${port}/stream`;

  return (
    <div className="bg-btbg-darker rounded-lg overflow-hidden">
      <img
        src={streamUrl}
        alt="Camera feed"
        className="w-full aspect-[4/3] object-cover"
        onError={() => setHasError(true)}
      />
    </div>
  );
}

export default CameraFeed;
