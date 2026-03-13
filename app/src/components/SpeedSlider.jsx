import React from 'react';

function SpeedSlider({ value, onChange, disabled }) {
  return (
    <div className="flex items-center gap-3">
      <label className="text-sm text-gray-400 w-16">Speed:</label>
      <input
        type="range"
        min="0"
        max="100"
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value))}
        disabled={disabled}
        className="flex-1 h-2 bg-btbg-accent rounded-lg appearance-none cursor-pointer
                   disabled:opacity-50 disabled:cursor-not-allowed"
      />
      <span className="text-sm w-12 text-right">{value}%</span>
    </div>
  );
}

export default SpeedSlider;
