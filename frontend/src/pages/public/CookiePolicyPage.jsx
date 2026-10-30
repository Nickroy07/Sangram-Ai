import React from 'react';
import { Link } from 'react-router-dom';

export const CookiePolicyPage = () => {
  return (
    <div className="legal-page-view">
      <div className="page-hero-banner">
        <div className="section-container text-center">
          <span className="section-tag">LEGAL COMPLIANCE</span>
          <h1 className="page-hero-title">Cookie Policy</h1>
          <p className="page-hero-sub">Effective Date: October 20, 2026</p>
        </div>
      </div>

      <div className="section-container py-12 max-w-3xl mx-auto legal-prose">
        <section className="legal-section">
          <h2>1. Introduction</h2>
          <p>
            This Cookie Policy explains how Sangram AI ("we", "us", or "our") uses cookies and similar storage technologies when you access our website and web application at <a href="https://sangramai.tech">sangramai.tech</a>.
          </p>
        </section>

        <section className="legal-section">
          <h2>2. Essential Security & Session Cookies</h2>
          <p>
            Sangram AI utilizes secure, HttpOnly cookies strictly required to authenticate your identity, protect your workspace against cross-site request forgery, and maintain session continuity:
          </p>
          <ul className="mt-3 list-disc pl-6 space-y-2">
            <li>
              <strong>sangram_session:</strong> Short-lived HttpOnly JWT token used to authenticate API requests to backend endpoints. Expirable within 60 minutes.
            </li>
            <li>
              <strong>sangram_refresh:</strong> Secure rotating refresh token restricted to the <code>/api/auth</code> endpoint to seamlessly renew your access session without exposing secrets to client-side scripts.
            </li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>3. Client-Side Preferences Storage</h2>
          <p>
            We use your browser's local storage (LocalStorage) solely to remember your chosen user interface preferences (such as Obsidian theme, reduced motion accessibility settings, and display modes). These entries contain no personally identifiable information and never leave your browser.
          </p>
        </section>

        <section className="legal-section">
          <h2>4. Third-Party Cookies & Tracking</h2>
          <p>
            Sangram AI does not employ invasive third-party cross-site advertising cookies or behavioral tracking networks. If you choose to authenticate via "Continue with Google", Google Identity Services temporarily initializes authentication frames in accordance with Google's Privacy Policy.
          </p>
        </section>

        <section className="legal-section">
          <h2>5. Managing Your Cookies</h2>
          <p>
            You can configure your browser to block or delete cookies at any time. However, because our session cookies are essential for security and account authentication, disabling cookies will prevent you from signing in to the Sangram AI arena workspace.
          </p>
        </section>

        <section className="legal-section">
          <h2>6. Contact Us</h2>
          <p>
            If you have questions regarding our use of cookies, please reach out via our <Link to="/contact">Contact Page</Link> or email us at <code>privacy@sangram.ai</code>.
          </p>
        </section>
      </div>
    </div>
  );
};
