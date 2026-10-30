import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { userApi } from '../../services/api';
import { useToast } from '../../context/ToastContext';
import { Button } from '../../components/common/Button';

export const ProfileSettings = () => {
  const { user, setUser } = useAuth();
  const { showToast } = useToast();

  const [name, setName] = useState(user?.name || '');
  const [email] = useState(user?.email || '');
  const [role, setRole] = useState(user?.occupation || '');
  const [loading, setLoading] = useState(false);

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    try { const updated = await userApi.updateProfile({ name, occupation: role }); setUser(updated); showToast('Profile updated.', 'success'); }
    catch (err) { showToast(err.message, 'error'); }
    finally { setLoading(false); }
  };

  return (
    <div className="settings-page-view">
      <div className="page-header-row">
        <div>
          <h1 className="page-title">Settings & Preferences</h1>
          <p className="page-sub">Manage your account profile, dialectic defaults, and security credentials.</p>
        </div>
      </div>

      {/* Clean Tabs */}
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

      <div className="clean-card-box mt-6">
        <h3 className="box-title">Account Profile</h3>
        <p className="box-sub">This profile information identifies your contributions in shared team chambers.</p>

        <form onSubmit={handleSave} className="clean-settings-form mt-6">
          <div className="avatar-row">
            <div className="avatar-circle-lg">
              {name ? name.charAt(0).toUpperCase() : 'A'}
            </div>
            <div>
              <span className="text-muted text-xs block mt-1">Avatar upload is not available yet.</span>
            </div>
          </div>

          <div className="form-grid-two mt-6">
            <div className="input-group">
              <label className="field-label">Full Name</label>
              <input
                type="text"
                className="clean-input mt-1"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>

            <div className="input-group">
              <label className="field-label">Work Email</label>
              <input
                type="email"
                className="clean-input mt-1"
                value={email}
                readOnly
                required
              />
            </div>

            <div className="input-group">
              <label className="field-label">Role / Focus</label>
              <input
                type="text"
                className="clean-input mt-1"
                value={role}
                onChange={(e) => setRole(e.target.value)}
              />
            </div>
          </div>

          <div className="form-save-row mt-6">
            <Button type="submit" variant="primary" loading={loading}>
              Save Profile Changes
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
