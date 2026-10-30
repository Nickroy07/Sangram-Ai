import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useToast } from '../../context/ToastContext';
import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';
import { userApi } from '../../services/api';

export const PreferencesSettings = () => {
  const [theme, setTheme] = useState('obsidian');
  const [motion, setMotion] = useState('full'); // full, reduced
  const [autoSave, setAutoSave] = useState(true);
  const [showTopology, setShowTopology] = useState(true);
  const { showToast } = useToast();

  const [loading, setLoading] = useState(false);
  useEffect(() => { userApi.preferences().then((preferences) => { setTheme(preferences.theme || 'obsidian'); setMotion(preferences.motion || 'full'); }).catch((err) => showToast(err.message, 'error')); }, []);

  const handleSave = async () => {
    setLoading(true);
    try {
      await userApi.updatePreferences({ theme, motion });
      localStorage.setItem('sangram_ui_preferences', JSON.stringify({ autoSave, showTopology }));
      showToast('Preferences saved.', 'success');
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

      <Card className="settings-panel-card mt-6">
        <h3 className="panel-title">Interface & Dialectic Preferences</h3>
        <p className="panel-desc text-muted">Customize your war room visual tone and animation density.</p>

        <div className="pref-sections-stack mt-6">
          {/* Theme selection */}
          <div className="pref-group">
            <label className="pref-label">Color Theme</label>
            <div className="theme-options-row">
              <button
                type="button"
                className={`theme-chip-btn ${theme === 'obsidian' ? 'active' : ''}`}
                onClick={() => setTheme('obsidian')}
              >
                <span>Obsidian Precision (Default)</span>
              </button>
              <button
                type="button"
                className={`theme-chip-btn ${theme === 'deep-navy' ? 'active' : ''}`}
                onClick={() => setTheme('navy')}
              >
                <span>Deep Navy Atmosphere</span>
              </button>
            </div>
          </div>

          {/* Motion preferences */}
          <div className="pref-group mt-6">
            <label className="pref-label">Motion & Animation</label>
            <div className="theme-options-row">
              <button
                type="button"
                className={`theme-chip-btn ${motion === 'full' ? 'active' : ''}`}
                onClick={() => setMotion('full')}
              >
                <span>Full Cinematic Motion</span>
              </button>
              <button
                type="button"
                className={`theme-chip-btn ${motion === 'reduced' ? 'active' : ''}`}
                onClick={() => setMotion('reduced')}
              >
                <span>Reduced Motion</span>
              </button>
            </div>
          </div>

          {/* Toggle Switches */}
          <div className="pref-group mt-6">
            <label className="pref-label">Chamber Defaults</label>
            <div className="toggle-setting-row">
              <div>
                <span className="setting-name">Render Active Topology Graph</span>
                <span className="setting-desc text-muted text-xs block">
                  Displays interactive SVG attack vectors between combatants during battle.
                </span>
              </div>
              <input
                type="checkbox"
                checked={showTopology}
                onChange={(e) => setShowTopology(e.target.checked)}
                className="checkbox-toggle"
              />
            </div>

            <div className="toggle-setting-row mt-4">
              <div>
                <span className="setting-name">Auto-save completed debates to history</span>
                <span className="setting-desc text-muted text-xs block">
                  Keep this interface preference on this device.
                </span>
              </div>
              <input
                type="checkbox"
                checked={autoSave}
                onChange={(e) => setAutoSave(e.target.checked)}
                className="checkbox-toggle"
              />
            </div>
          </div>

          <div className="mt-8">
            <Button variant="primary" loading={loading} onClick={handleSave}>
              Save Preferences
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};
