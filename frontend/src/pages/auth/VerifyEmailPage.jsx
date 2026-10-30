import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useToast } from '../../context/ToastContext';
import { Button } from '../../components/common/Button';
import { Logo } from '../../components/common/Logo';
import { authApi } from '../../services/api';

export const VerifyEmailPage = () => {
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { showToast } = useToast();
  const navigate = useNavigate();

  const handleDigitChange = (index, val) => {
    if (!/^\d*$/.test(val)) return;
    const newCode = [...code];
    newCode[index] = val.slice(-1);
    setCode(newCode);

    // Auto-focus next input
    if (val && index < 5) {
      const nextInput = document.getElementById(`digit-${index + 1}`);
      if (nextInput) nextInput.focus();
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try { await authApi.verifyEmail(code.join('')); showToast('Email verified successfully.', 'success'); navigate('/onboarding'); }
    catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const handleResend = async () => {
    try { await authApi.resendVerification(); showToast('A new verification code was sent.', 'success'); }
    catch (err) { setError(err.message); }
  };

  return (
    <div className="auth-box animate-scale-in">
      <div className="auth-box-header text-center">
        <div className="flex justify-center mb-3">
          <Logo size="md" showWordmark={true} href="/home" />
        </div>
        <h2 className="auth-title">Verify your email</h2>
        <p className="auth-sub">
          We sent a 6-digit confirmation code to your email. Enter it below to activate your account.
        </p>
      </div>

      <form onSubmit={handleVerify} className="verify-form">
        {error && <div className="auth-alert error-alert" role="alert">{error}</div>}
        <div className="digit-inputs-row">
          {code.map((digit, idx) => (
            <input
              key={idx}
              id={`digit-${idx}`}
              type="text"
              maxLength={1}
              value={digit}
              onChange={(e) => handleDigitChange(idx, e.target.value)}
              className="digit-box"
              autoFocus={idx === 0}
            />
          ))}
        </div>

        <Button
          type="submit"
          variant="primary"
          size="lg"
          className="w-full mt-4"
          loading={loading}
        >
          Confirm & Continue
        </Button>
      </form>

      <div className="resend-row text-center mt-4">
        <span>Didn't receive the email? </span>
        <button type="button" onClick={handleResend} className="text-link-button">
          Resend code
        </button>
      </div>

      <div className="auth-box-footer text-center">
        <Link to="/auth/login" className="back-link">
          ← Back to Sign In
        </Link>
      </div>
    </div>
  );
};
