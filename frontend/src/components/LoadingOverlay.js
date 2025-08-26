import React from 'react';
import './LoadingOverlay.css';

const LoadingOverlay = ({ message = 'Loading…' }) => {
  return (
    <div className="loading-overlay" role="status" aria-live="polite">
      <div className="loading-spinner" />
      <div className="loading-message">{message}</div>
    </div>
  );
};

export default LoadingOverlay;


