import React, { useState } from 'react';
import './Footer.css';

const Footer = () => {
  const [isOpen, setIsOpen] = useState(false);

  const toggleOpen = () => setIsOpen(!isOpen);

  return (
    <footer className="app-footer">
      <div className="footer-toggle" onClick={toggleOpen}>
        For help, email <a href="mailto:icissna1@jh.edu">icissna1@jh.edu</a>
        <span className={`caret ${isOpen ? 'open' : ''}`}>&#9650;</span>
      </div>
      {isOpen && (
        <div className="footer-content">
          <b>Please reach out for questions, suggestions or bug reports.</b>
          <br />
          <br />
          Also, email me to combine multiple course codes if they all belong to the same course (e.g. in CS, 600 levels always have corresponding 400 levels for undergrads, so if you search EN.601.475, it will show the results for both that and EN.601.675).
          <br />
          I've already combined such CS & cognitive science courses.
        </div>
      )}
    </footer>
  );
};

export default Footer;
