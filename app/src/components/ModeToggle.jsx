import React from 'react';

function ModeToggle({ mode, onChange, disabled }) {
  const isPatrol = mode === 'patrol';

  return (
    <div
      className={`mode-toggle ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      onClick={() => {
        if (!disabled) {
          onChange(isPatrol ? 'manual' : 'patrol');
        }
      }}
    >
      <div className={`mode-toggle-slider ${isPatrol ? 'patrol' : ''}`}></div>
      <span className="mode-toggle-label">MANUAL</span>
      <span className="mode-toggle-label">PATROL</span>
    </div>
  );
}

export default ModeToggle;
