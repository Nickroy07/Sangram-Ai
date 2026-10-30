import React, { useState, useEffect } from 'react';
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom';
import { Button } from '../components/common/Button';
import { Logo } from '../components/common/Logo';

export const PublicLayout = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setMobileMenuOpen(false);
    window.scrollTo(0, 0);
  }, [location.pathname]);

  return (
    <div className="public-layout">
      <div className="public-top-banner">
        <span>✦ Sangram AI — Different Minds. One Arena. Compare models. Make better decisions.</span>
        <Link to="/app/arena/new" className="banner-link">Try Live Arena →</Link>
      </div>

      {/* Main Public Navigation */}
      <header className="public-nav-header">
        <div className="nav-container">
          <Logo size="md" href="/home" />

          {/* Desktop Navigation Links */}
          <nav className="desktop-nav-links" aria-label="Primary navigation">
            <NavLink to="/home" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Home</NavLink>
            <NavLink to="/features" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Features</NavLink>
            <NavLink to="/how-it-works" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>How It Works</NavLink>
            <NavLink to="/models" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Models</NavLink>
            <NavLink to="/pricing" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Pricing</NavLink>
            <NavLink to="/about" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>About</NavLink>
          </nav>

          {/* Action CTAs */}
          <div className="nav-actions">
            <Link to="/auth/login" className="login-link">Log In</Link>
            <Link to="/app/arena/new">
              <Button variant="primary" size="sm">Enter the Arena</Button>
            </Link>
            <button
              className="mobile-toggle-btn"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle navigation menu"
              aria-expanded={mobileMenuOpen}
            >
              <span className={`burger-bar ${mobileMenuOpen ? 'open' : ''}`}></span>
              <span className={`burger-bar ${mobileMenuOpen ? 'open' : ''}`}></span>
              <span className={`burger-bar ${mobileMenuOpen ? 'open' : ''}`}></span>
            </button>
          </div>
        </div>

        {/* Mobile Nav Drawer */}
        {mobileMenuOpen && (
          <div className="mobile-nav-panel animate-fade-in">
            <nav className="mobile-nav-links">
              <Link to="/home" className="mobile-link">Home</Link>
              <Link to="/features" className="mobile-link">Features</Link>
              <Link to="/how-it-works" className="mobile-link">How It Works</Link>
              <Link to="/models" className="mobile-link">Models</Link>
              <Link to="/pricing" className="mobile-link">Pricing</Link>
              <Link to="/about" className="mobile-link">About</Link>
              <Link to="/faq" className="mobile-link">FAQ</Link>
              <Link to="/contact" className="mobile-link">Contact</Link>
              <hr className="mobile-nav-divider" />
              <Link to="/auth/login" className="mobile-link">Log In</Link>
              <Link to="/app/arena/new" className="mobile-cta-wrapper">
                <Button variant="primary" className="w-full">Enter the Arena</Button>
              </Link>
            </nav>
          </div>
        )}
      </header>

      {/* Page Content */}
      <main className="public-content">
        <Outlet />
      </main>

      {/* Comprehensive Public Footer */}
      <footer className="public-footer">
        <div className="footer-container">
          <div className="footer-grid">
            <div className="footer-col brand-col">
              <Logo size="md" href="/home" className="footer-logo" />
              <p className="footer-tagline">Different Minds. One Arena.</p>
              <p className="footer-bio">
                An AI workspace where users select multiple models, compare their reasoning and critiques, and review one consolidated final answer.
              </p>
              <div className="footer-repo-link">
                <a href="https://github.com/Nickroy07/Sangram-Ai.git" target="_blank" rel="noreferrer" className="github-chip">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
                  </svg>
                  <span>GitHub Repository</span>
                </a>
              </div>
            </div>

            <div className="footer-col">
              <h5 className="footer-heading">Product</h5>
              <ul className="footer-links">
                <li><Link to="/app/arena/new">AI Arena</Link></li>
                <li><Link to="/features">Core Features</Link></li>
                <li><Link to="/models">Supported Models</Link></li>
                <li><Link to="/how-it-works">How It Works</Link></li>
                <li><Link to="/pricing">Pricing Plans</Link></li>
              </ul>
            </div>

            <div className="footer-col">
              <h5 className="footer-heading">Workspace</h5>
              <ul className="footer-links">
                <li><Link to="/app">Dashboard</Link></li>
                <li><Link to="/app/history">Battle History</Link></li>
                <li><Link to="/app/saved">Saved Answers</Link></li>
                <li><Link to="/app/usage">Usage Analytics</Link></li>
                <li><Link to="/app/settings/profile">Settings</Link></li>
              </ul>
            </div>

            <div className="footer-col">
              <h5 className="footer-heading">Resources</h5>
              <ul className="footer-links">
                <li><Link to="/about">About Sangram AI</Link></li>
                <li><Link to="/faq">Frequently Asked Questions</Link></li>
                <li><Link to="/contact">Contact Support</Link></li>
                <li><Link to="/features">Product Features</Link></li>
              </ul>
            </div>

            <div className="footer-col">
              <h5 className="footer-heading">Legal</h5>
              <ul className="footer-links">
                <li><Link to="/privacy">Privacy Policy</Link></li>
                <li><Link to="/terms">Terms of Service</Link></li>
                <li><Link to="/refund-policy">Refund Policy</Link></li>
                <li><Link to="/cookie-policy">Cookie Policy</Link></li>
              </ul>
            </div>
          </div>

          <div className="footer-bottom">
            <span className="copyright">© 2026 Sangram AI. All rights reserved.</span>
            <div className="footer-bottom-badges">
              <span className="badge-honest">Different Minds. One Arena.</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};
