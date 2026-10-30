import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Logo } from '../../components/common/Logo';
import { GoogleSignInButton } from '../../components/common/GoogleSignInButton';

export const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError('Please provide both your email and password.');
      return;
    }

    try {
      setLoading(true);
      await login({ email, password });
      showToast('Successfully signed in.', 'success');
      navigate('/app');
    } catch (err) {
      setError(err.message || 'Login failed.');
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
        <h2 className="auth-title">Welcome back</h2>
        <p className="auth-sub">Enter your credentials to access the Sangram AI arena.</p>
      </div>

      {error && (
        <div className="auth-alert error-alert" role="alert">
          <span>⚠ {error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="auth-form" noValidate>
        <Input
          label="Email Address"
          type="email"
          placeholder="name@company.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <div className="password-wrapper">
          <Input
            label="Password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <div className="text-right">
            <Link to="/auth/forgot-password" className="text-link-sm">
              Forgot password?
            </Link>
          </div>
        </div>

        <Button
          type="submit"
          variant="primary"
          size="lg"
          className="w-full mt-2"
          loading={loading}
        >
          Sign In
        </Button>
      </form>

      <div className="auth-divider">
        <span>OR</span>
      </div>

      <GoogleSignInButton text="Sign In with Google" />

      <div className="auth-box-footer">
        <span>Need an account? </span>
        <Link to="/auth/signup" className="auth-action-link">
          Create one now
        </Link>
      </div>
    </div>
  );
};

