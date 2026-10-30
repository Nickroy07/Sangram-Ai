import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useToast } from '../../context/ToastContext';
import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';
import { Input } from '../../components/common/Input';
import { userApi } from '../../services/api';

export const SecuritySettings = () => {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  useEffect(() => { userApi.sessions().then(setSessions).catch((err) => showToast(err.message, 'error')); }, []);

  const handlePasswordUpdate = async (e) => {
    e.preventDefault();
    if (!newPassword || newPassword.length < 8) {
      showToast('New password must be at least 8 characters.', 'warn');
      return;
    }
    if (newPassword !== confirmPassword) {
      showToast('Passwords do not match.', 'error');
      return;
    }

    setLoading(true);
    try {
      await userApi.changePassword(currentPassword, newPassword);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      showToast('Password updated successfully!', 'success');
    } catch (err) { showToast(err.message, 'error'); }
    finally { setLoading(false); }
  };

  return (
    <div className="settings-page-view">
      <div className="page-header-row">
        <div>
          <h1 className="page-title">Settings & Configuration</h1>
          <p className="page-sub">Manage your account credentials, security parameters, and dialectic preferences.</p>
        </div>
      </div>

      <div className="settings-nav-tabs mt-6">
        <NavLink to="/app/settings/profile" className={({ isActive }) => `tab-link ${isActive ? 'active' : ''}`}>
          Profile
        </NavLink>
        <NavLink to="/app/settings/security" className={({ isActive }) => `tab-link ${isActive ? 'active' : ''}`}>
          Security
        </NavLink>
        <NavLink to="/app/settings/preferences" className={({ isActive }) => `tab-link ${isActive ? 'active' : ''}`}>
          Preferences
        </NavLink>
      </div>

      <div className="security-cards-stack mt-6">
        {/* Password Update Card */}
        <Card className="settings-panel-card">
          <h3 className="panel-title">Change Password</h3>
          <p className="panel-desc text-muted">Ensure your account is using a long, random passphrase.</p>

          <form onSubmit={handlePasswordUpdate} className="mt-6 max-w-lg">
            <Input
              label="Current Password"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />
            <Input
              label="New Password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />
            <Input
              label="Confirm New Password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />

            <Button type="submit" variant="primary" loading={loading} className="mt-2">
              Update Password
            </Button>
          </form>
        </Card>

        {/* Two-Factor Authentication Card */}
        <Card className="settings-panel-card mt-6">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="panel-title">Two-Factor Authentication (2FA)</h3>
              <p className="panel-desc text-muted">
                Add an extra layer of security using an authenticator app (TOTP).
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              disabled
            >
              Not available yet
            </Button>
          </div>
        </Card>

        {/* Active Sessions */}
        <Card className="settings-panel-card mt-6">
          <h3 className="panel-title">Active Sessions</h3>
          <p className="panel-desc text-muted">Devices logged into your Sangram AI workspace account.</p>

          <div className="sessions-list mt-4">
            <div className="session-item">
              <span className="session-icon">💻</span>
              <div className="session-info">
                <span className="device-name">{sessions[0]?.user_agent || 'Signed-in session'}</span>
                <span className="device-loc">{sessions[0]?.ip_address || 'Location unavailable'}</span>
              </div>
              <span className="active-pill">{sessions[0]?.is_current ? 'Current' : 'Active'}</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

