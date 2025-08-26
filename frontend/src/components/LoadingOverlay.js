import React from 'react';
import ReactDOM from 'react-dom';
import './LoadingOverlay.css';

const LoadingOverlay = ({ message = 'Loading…' }) => {
  return ReactDOM.createPortal(
    <div className="loading-overlay" role="status" aria-live="polite">
      <div className="loading-spinner" />
      <div className="loading-message">{message}</div>
    </div>,
    document.body
  );
};

export default LoadingOverlay;


