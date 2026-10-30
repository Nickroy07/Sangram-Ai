import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useToast } from '../../context/ToastContext';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Logo } from '../../components/common/Logo';
import { authApi } from '../../services/api';

export const ResetPasswordPage = () => {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();
  const navigate = useNavigate();

  const handleReset = async (e) => {
    e.preventDefault();
    setError('');

    if (!newPassword || newPassword.length < 8) {
      setError('Password must contain at least 8 characters.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    const token = new URLSearchParams(window.location.search).get('token');
    if (!token) { setError('The password reset link is invalid or expired. Request a new one.'); setLoading(false); return; }
    try { await authApi.resetPassword(token, newPassword); showToast('Password updated. You can now sign in.', 'success'); navigate('/auth/login'); }
    catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="auth-box animate-scale-in">
      <div className="auth-box-header">
        <div className="flex justify-center mb-3">
          <Logo size="md" showWordmark={true} href="/home" />
        </div>
        <h2 className="auth-title">Set new password</h2>
        <p className="auth-sub">Choose a secure password for your Sangram AI workspace account.</p>
      </div>

      {error && (
        <div className="auth-alert error-alert" role="alert">
          <span>⚠ {error}</span>
        </div>
      )}

      <form onSubmit={handleReset} className="auth-form" noValidate>
        <Input
          label="New Password"
          type="password"
          placeholder="At least 8 characters"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          required
        />

        <Input
          label="Confirm New Password"
          type="password"
          placeholder="Repeat new password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
        />

        <Button
          type="submit"
          variant="primary"
          size="lg"
          className="w-full mt-2"
          loading={loading}
        >
          Update Password & Log In
        </Button>
      </form>

      <div className="auth-box-footer text-center">
        <Link to="/auth/login" className="back-link">
          ← Cancel and Return to Sign In
        </Link>
      </div>
    </div>
  );
};
