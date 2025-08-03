import React from 'react';
import { Link } from 'react-router-dom';
import './Navbar.css';

const Navbar = () => {
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-brand">
          <span className="brand-icon">📚</span>
          PlaybookOS
        </Link>
        
        <div className="navbar-menu">
          <Link to="/" className="navbar-link">Dashboard</Link>
          <Link to="/upload" className="navbar-link">Import</Link>
          <button className="btn btn-primary">Sign In</button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
