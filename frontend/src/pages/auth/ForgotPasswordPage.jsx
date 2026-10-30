import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useToast } from '../../context/ToastContext';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Logo } from '../../components/common/Logo';
import { authApi } from '../../services/api';

export const ForgotPasswordPage = () => {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { showToast } = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email) {
      setError('Please provide your account email.');
      return;
    }

    setLoading(true);
    try {
      await authApi.forgotPassword(email);
      setSubmitted(true);
      showToast('If the account exists, reset instructions have been sent.', 'success');
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="auth-box animate-scale-in">
      <div className="auth-box-header">
        <div className="flex justify-center mb-3">
          <Logo size="md" showWordmark={true} href="/home" />
        </div>
        <h2 className="auth-title">Reset your password</h2>
        <p className="auth-sub">
          Enter your registered email address and we will send you instructions to recover your arena account.
        </p>
      </div>

      {submitted ? (
        <div className="success-state-box animate-fade-in">
          <div className="success-icon-badge">✓</div>
          <h4 className="success-title">Check your inbox</h4>
          <p className="success-text">
            We have sent password recovery instructions to <strong>{email}</strong>. Please check your spam folder if it doesn't appear in 2 minutes.
          </p>
          <div className="mt-4 flex flex-col gap-2">
            <p className="text-muted">Use the secure link sent to your email to choose a new password.</p>\r\n            <Link to="/auth/login" className="back-link block text-center mt-2">
              ← Return to Login
            </Link>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="auth-form" noValidate>
          {error && <div className="auth-alert error-alert" role="alert">{error}</div>}
          {error && (
            <div className="auth-alert error-alert" role="alert">
              <span>⚠ {error}</span>
            </div>
          )}

          <Input
            label="Account Email"
            type="email"
            placeholder="name@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <Button
            type="submit"
            variant="primary"
            size="lg"
            className="w-full mt-2"
            loading={loading}
          >
            Send Reset Instructions
          </Button>

          <div className="auth-box-footer text-center">
            <Link to="/auth/login" className="back-link">
              ← Back to Sign In
            </Link>
          </div>
        </form>
      )}
    </div>
  );
};

