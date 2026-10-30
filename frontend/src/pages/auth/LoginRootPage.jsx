import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Logo } from '../../components/common/Logo';
import { GoogleSignInButton } from '../../components/common/GoogleSignInButton';

export const LoginRootPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const handleSignIn = async (e) => {
    e.preventDefault();
    setError('');

    if (!email) {
      setError('Please enter your email address.');
      return;
    }
    if (!password) {
      setError('Please enter your password.');
      return;
    }

    try {
      setLoading(true);
      await login({ email, password });
      showToast('Welcome to Sangram AI Arena!', 'success');
      navigate('/app');
    } catch (err) {
      setError(err.message || 'Failed to sign in.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-root-experience">
      {/* Background Atmosphere: Navy, Cyan-Blue Light Trails, Grid Mesh */}
      <div className="arena-ambient-field">
        <div className="trail trail-left"></div>
        <div className="trail trail-right"></div>
        <div className="radial-core"></div>
        <div className="ambient-particles"></div>
      </div>

      {/* Top Bar with Brand & Public Website Link */}
      <header className="root-header">
        <Logo size="md" href="/home" />

        <div className="root-header-links">
          <Link to="/home" className="public-home-pill">
            <span>Explore Public Website</span>
            <span className="pill-arrow">→</span>
          </Link>
        </div>
      </header>

      {/* Main Container: Split Stage with Animated Model Arena on Left & Form on Right */}
      <main className="root-main-layout">
        {/* Left Col: Cinematic Arena Clash Preview */}
        <section className="root-arena-stage" aria-label="Sangram AI Model Battle Preview">
          <div className="stage-eyebrow">
            <span className="live-pulse"></span>
            <span>ILLUSTRATIVE ARENA PREVIEW</span>
          </div>
          <h1 className="stage-heading">
            Different Minds.<br />
            <span className="stage-gradient-text">One Unified Arena.</span>
          </h1>
          <p className="stage-sub">
            Watch leading AI models challenge each other's reasoning, expose blind spots, and synthesize one consolidated answer.
          </p>

          {/* Animated Model Clash Cards */}
          <div className="clash-visual-container">
            {/* Model Card Left: ChatGPT */}
            <div className="fighter-card fighter-left animate-slide-left">
              <div className="fighter-header">
                <span className="fighter-dot dot-gpt"></span>
                <span className="fighter-title">ChatGPT</span>
              </div>
              <div className="fighter-claim">
                "Monoliths simplify deployment velocity, but microservices provide true domain isolation."
              </div>
              <div className="fighter-tag">Thesis Provider</div>
            </div>

            {/* Central VS Badge */}
            <div className="clash-vs-badge animate-pulse-glow">
              <div className="vs-inner">VS</div>
              <div className="vs-ripple"></div>
            </div>

            {/* Model Card Right: Claude */}
            <div className="fighter-card fighter-right animate-slide-right">
              <div className="fighter-header">
                <span className="fighter-dot dot-claude"></span>
                <span className="fighter-title">Claude</span>
              </div>
              <div className="fighter-claim">
                "Distributed operational tax will derail a 5-person team before domain isolation matters."
              </div>
              <div className="fighter-tag">Counter-Examiner</div>
            </div>
          </div>

          <div className="synthesis-preview-chip">
            <span className="synth-icon">✦</span>
            <span className="synth-text">Example synthesis: <strong>Modular Monolith</strong> recommended for early-stage B2B SaaS.</span>
          </div>
        </section>

        {/* Right Col: Smooth Form Reveal */}
        <section className="root-form-stage">
          <div className="login-card-panel animate-reveal-up">
            <div className="form-header">
              <div className="form-brand-row mb-3">
                <Logo size="sm" showWordmark={true} href="" />
              </div>
              <h2 className="form-title">Enter the Arena</h2>
              <p className="form-subtitle">Sign in to your Sangram AI workspace to initiate multi-model debates.</p>
            </div>

            {error && (
              <div className="auth-alert error-alert" role="alert">
                <span>⚠ {error}</span>
              </div>
            )}

            <form onSubmit={handleSignIn} className="auth-form-fields" noValidate>
              <Input
                label="Work Email"
                type="email"
                placeholder="name@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />

              <div className="password-group">
                <Input
                  label="Password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <div className="forgot-link-row">
                  <Link to="/auth/forgot-password" className="text-link-sm">
                    Forgot password?
                  </Link>
                </div>
              </div>

              <Button
                type="submit"
                variant="primary"
                size="lg"
                className="w-full submit-auth-btn"
                loading={loading}
              >
                Sign In to Workspace
              </Button>
            </form>

            <div className="auth-divider">
              <span>OR</span>
            </div>

            <GoogleSignInButton text="Sign In with Google" />

            <div className="auth-card-footer">
              <span>Don't have an account? </span>
              <Link to="/auth/signup" className="auth-action-link">
                Create free account
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* Root Experience Footer */}
      <footer className="root-footer">
        <span className="prototype-disclaimer">Different Minds. One Arena.</span>
        <div className="root-legal-links">
          <Link to="/privacy">Privacy</Link>
          <Link to="/terms">Terms</Link>
          <Link to="/how-it-works">How It Works</Link>
          <Link to="/contact">Support</Link>
        </div>
      </footer>
    </div>
  );
};

