import React, { useState } from 'react';
import { NavLink, Link, Outlet, useLocation, useNavigate, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common/Button';
import { Logo } from '../components/common/Logo';

export const DashboardLayout = () => {
  const { user, logout, loading } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try { await logout(); } finally { navigate('/auth/login'); }
  };

  if (loading) return <div className="arena-loading-screen py-16 text-center"><div className="btn-spinner mx-auto mb-4" /><p className="text-muted">Loading your workspace…</p></div>;
  if (!user) return <Navigate to="/auth/login" replace state={{ from: location.pathname }} />;

  const getBreadcrumb = () => {
    const parts = location.pathname.split('/').filter(Boolean);
    if (parts.length <= 1) return 'Workspace / Dashboard';
    const sub = parts[1];
    switch (sub) {
      case 'arena':
        return 'Chamber / AI Arena';
      case 'war-room':
        return 'Chamber / War Room';
      case 'history':
        return 'Workspace / Battle History';
      case 'saved':
        return 'Workspace / Saved Answers';
      case 'models':
        return 'Library / Model Matrix';
      case 'usage':
        return 'Telemetry / Token Usage';
      case 'billing':
        return 'Account / Billing & Plans';
      case 'settings':
        return 'Account / Settings';
      default:
        return 'Workspace / Dashboard';
    }
  };

  const navItems = [
    { label: 'AI Arena', path: '/app/arena', icon: '⚔' },
    { label: 'War Room', path: '/app/war-room', icon: '⚡' },
    { label: 'Dashboard', path: '/app', icon: '⊞', end: true },
    { label: 'Battle History', path: '/app/history', icon: '📜' },
    { label: 'Saved Answers', path: '/app/saved', icon: '💾' },
    { label: 'Model Library', path: '/app/models', icon: '🧠' },
    { label: 'Token Usage', path: '/app/usage', icon: '📊' },
    { label: 'Billing & Plans', path: '/app/billing', icon: '💳' },
    { label: 'Settings', path: '/app/settings/profile', icon: '⚙' }
  ];

  return (
    <div className="dashboard-shell">
      {/* Mobile Backdrop */}
      {sidebarOpen && (
        <div
          className="dashboard-mobile-backdrop"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Modern Compact Sidebar */}
      <aside className={`dashboard-sidebar ${sidebarOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-inner">
          {/* Header Brand */}
          <div className="sidebar-brand">
            <Logo size="sm" href="/app" />
            <button
              type="button"
              className="sidebar-close-btn"
              onClick={() => setSidebarOpen(false)}
              aria-label="Close sidebar"
            >
              ×
            </button>
          </div>

          {/* Primary Action */}
          <div className="sidebar-cta-block">
            <Link to="/app/arena" onClick={() => setSidebarOpen(false)} className="w-full">
              <Button variant="primary" className="new-battle-btn w-full" icon="⚔">
                New Battle
              </Button>
            </Link>
          </div>

          {/* Navigation Links */}
          <div className="sidebar-scrollable">
            <nav className="sidebar-nav" aria-label="Application navigation">
              {navItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  end={item.end}
                  onClick={() => setSidebarOpen(false)}
                  className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
                >
                  <span className="sidebar-nav-icon" aria-hidden="true">{item.icon}</span>
                  <span className="sidebar-nav-label">{item.label}</span>
                </NavLink>
              ))}
            </nav>

            <div className="sidebar-marketing-link">
              <Link to="/home" className="external-portal-btn">
                <span>← Public Website</span>
                <span className="portal-arrow">↗</span>
              </Link>
            </div>
          </div>

          {/* User Profile Bar */}
          <div className="sidebar-user-card">
            <div className="user-info-row">
              <div className="user-avatar-circle">
                {user?.name ? user.name.charAt(0).toUpperCase() : 'A'}
              </div>
              <div className="user-meta">
                <span className="user-name">{user.name}</span>
                <span className="user-tier">{user.tier || 'Free'} plan</span>
              </div>
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="logout-btn"
              title="Sign Out"
              aria-label="Sign Out"
            >
              ⎋
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Viewport */}
      <div className="dashboard-main-wrapper">
        {/* Sticky Top Bar */}
        <header className="dashboard-topbar">
          <div className="topbar-left">
            <button
              type="button"
              className="topbar-hamburger"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open navigation menu"
            >
              ☰
            </button>
            <span className="crumb-segment">{getBreadcrumb()}</span>
          </div>

          <div className="topbar-right">
            <div className="dialectic-status-pill">
              <span className="status-live-dot"></span>
              <span>Sangram AI Workspace</span>
            </div>
            <Link to="/app/billing" className="upgrade-pill-btn">
              {user.tier?.toLowerCase() === 'free' ? 'View Plans' : (user.tier || 'Free') + ' Plan'}
            </Link>
            <Link to="/app/settings/profile" className="topbar-avatar" title="Settings">
              <div className="avatar-img-circle">
                {user?.name ? user.name.charAt(0).toUpperCase() : 'A'}
              </div>
            </Link>
          </div>
        </header>

        {/* Dynamic Route Content */}
        <main className="dashboard-content-area">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
