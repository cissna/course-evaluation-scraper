import React, { useId } from 'react';

export default function InfoTooltip({ label, children }) {
  const tooltipId = useId();
  return <span className="info-tip">
    <button type="button" className="info-button" aria-label={label} aria-describedby={tooltipId}>
      <svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true" focusable="false">
        <circle cx="10" cy="10" r="8" />
        <path d="M10 9.5v5" strokeLinecap="round" />
        <circle cx="10" cy="6" r="1" fill="currentColor" stroke="none" />
      </svg>
    </button>
    <span id={tooltipId} role="tooltip" className="info-popup">{children}</span>
  </span>;
}
