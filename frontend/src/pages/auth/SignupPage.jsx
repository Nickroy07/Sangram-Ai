import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Logo } from '../../components/common/Logo';
import { GoogleSignInButton } from '../../components/common/GoogleSignInButton';

export const SignupPage = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { signup } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const handleSignup = async (e) => {
    e.preventDefault();
    setError('');

    if (!name.trim()) {
      setError('Please provide your full name.');
      return;
    }
    if (!email.trim()) {
      setError('Please enter a valid email address.');
      return;
    }
    if (!password) {
      setError('Please enter a secure password.');
      return;
    }
    if (password.length < 8) {
      setError('Password must contain at least 8 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    if (!termsAccepted) {
      setError('Please agree to the Terms of Service and Privacy Policy.');
      return;
    }

    try {
      setLoading(true);
      await signup({ name, email, password });
      showToast('Account created! Welcome to Sangram AI.', 'success');
      navigate('/onboarding');
    } catch (err) {
      setError(err.message || 'Signup failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-box animate-scale-in">
      <div className="auth-box-header">
        <div className="flex justify-center mb-3">
          <Logo size="md" showWordmark={true} href="/home" />
        </div>
        <h2 className="auth-title">Create your workspace</h2>
        <p className="auth-sub">Bring different minds into your arena. Free tier included.</p>
      </div>

      {error && (
        <div className="auth-alert error-alert" role="alert">
          <span>⚠ {error}</span>
        </div>
      )}

      <form onSubmit={handleSignup} className="auth-form" noValidate>
        <Input
          label="Full Name"
          type="text"
          placeholder="Alex Vance"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />

        <Input
          label="Work Email"
          type="email"
          placeholder="alex@company.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <Input
          label="Password"
          type="password"
          placeholder="At least 8 characters"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <Input
          label="Confirm Password"
          type="password"
          placeholder="Repeat password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
        />

        <div className="terms-checkbox-row">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={termsAccepted}
              onChange={(e) => setTermsAccepted(e.target.checked)}
            />
            <span>
              I agree to the <Link to="/terms" target="_blank">Terms of Service</Link> and{' '}
              <Link to="/privacy" target="_blank">Privacy Policy</Link>
            </span>
          </label>
        </div>

        <Button
          type="submit"
          variant="primary"
          size="lg"
          className="w-full mt-2"
          loading={loading}
        >
          Create Free Account
        </Button>
      </form>

      <div className="auth-divider">
        <span>OR</span>
      </div>

      <GoogleSignInButton text="Sign Up with Google" />

      <div className="auth-box-footer">
        <span>Already have an account? </span>
        <Link to="/auth/login" className="auth-action-link">
          Sign In
        </Link>
      </div>
    </div>
  );
};
