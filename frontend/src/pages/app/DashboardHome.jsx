import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { battlesApi, savedApi } from '../../services/api';
import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';

export const DashboardHome = () => {
  const { user } = useAuth();
  const { showToast } = useToast();

  const [recentBattles, setRecentBattles] = useState([]);
  const [totalBattles, setTotalBattles] = useState(0);
  const [savedAnswers, setSavedAnswers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    const loadData = async () => {
      try {
        const [battles, saved] = await Promise.all([
          battlesApi.history(1, 4),
          savedApi.list()
        ]);
        setRecentBattles(battles.items || []);
        setTotalBattles(battles.total || 0);
        setSavedAnswers(saved.slice(0, 3));
      } catch (e) {
        setLoadError(e.message);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const handleCopy = (text) => {
    navigator.clipboard?.writeText(text);
    showToast('Copied synthesis verdict to clipboard!', 'success');
  };

  return (
    <div className="dashboard-home-view">
      {/* 1. Header & Primary Action */}
      <div className="dashboard-header-block">
        <div>
          <h1 className="dash-heading">Welcome back, {user?.name || 'Explorer'}</h1>
          <p className="dash-sub">
            Your multi-model arena is primed. Compare reasoning, expose blind spots, and synthesize unified truth.
          </p>
        </div>
        <div className="dash-cta-actions">
          <Link to="/app/war-room">
            <Button variant="outline" size="md" icon="⚡">
              War Room
            </Button>
          </Link>
          <Link to="/app/arena">
            <Button variant="primary" size="md" icon="⚔">
              Start New Battle
            </Button>
          </Link>
        </div>
      </div>

      {/* 2. Three Clean Summary Cards (No Clutter) */}
      <div className="dashboard-metrics-row">
        <div className="metric-box">
          <span className="metric-box-label">Battles Conducted</span>
          <div className="metric-box-val">{totalBattles}</div>
          <span className="metric-box-sub">Total battles in your account</span>
        </div>

        <div className="metric-box">
          <span className="metric-box-label">Average Consensus</span>
          <div className="metric-box-val text-cyan">—</div>
          <span className="metric-box-sub">Agreement is not calculated yet</span>
        </div>

        <div className="metric-box">
          <span className="metric-box-label">Monthly Credits</span>
          <div className="metric-box-val">{user?.tier || 'free'}</div>
          <span className="metric-box-sub">Current account plan</span>
        </div>
      </div>

      {/* 3. Main Workspace: Recent Activity & Saved ADRs */}
      <div className="dashboard-split-grid mt-6">
        {/* Left Column: Recent Dialectic Battles */}
        <div className="dash-column">
          <div className="column-title-bar">
            <h3 className="column-title">Recent Dialectic Battles</h3>
            <Link to="/app/history" className="text-link-sm">View All ({totalBattles}) →</Link>
          </div>

          <div className="battles-clean-list">
            {loadError && <p className="auth-alert error-alert" role="alert">{loadError}</p>}
            {loading && <p className="text-muted">Loading account activity…</p>}
            {recentBattles.length === 0 ? (
              <Card className="empty-panel text-center py-6">
                <p className="text-muted">No battles recorded yet.</p>
                <Link to="/app/arena" className="mt-3 inline-block">
                  <Button variant="primary" size="sm">Start Battle</Button>
                </Link>
              </Card>
            ) : (
              recentBattles.map((b) => (
                <div key={b.id} className="battle-clean-row">
                  <div className="battle-info-main">
                    <div className="battle-tag-date">
                      <span className="clean-topic-badge">{b.topic || 'Architecture'}</span>
                      <span className="clean-date-text">
                        {new Date(b.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                      </span>
                    </div>
                    <h4 className="battle-row-title">
                      <Link to={`/app/arena/${b.id}`}>{b.title}</Link>
                    </h4>
                    <p className="battle-row-summary">{b.summary}</p>
                  </div>

                  <div className="battle-row-side">
                    {b.consensusScore && (
                      <span className="consensus-pill">★ {b.consensusScore}%</span>
                    )}
                    <Link to={`/app/arena/${b.id}`}>
                      <Button variant="outline" size="sm">Review →</Button>
                    </Link>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Saved Consensus Answers */}
        <div className="dash-column">
          <div className="column-title-bar">
            <h3 className="column-title">Saved Consensus ADRs</h3>
            <Link to="/app/saved" className="text-link-sm">All Records ({savedAnswers.length}) →</Link>
          </div>

          <div className="saved-clean-list">
            {savedAnswers.length === 0 ? (
              <Card className="empty-panel text-center py-6">
                <p className="text-muted">No saved answers yet. In any debate, click "Save to ADR".</p>
              </Card>
            ) : (
              savedAnswers.map((s) => (
                <div key={s.id} className="saved-clean-row">
                  <div className="saved-row-header">
                      <h4 className="saved-row-title">{s.question}</h4>
                    <button
                      type="button"
                      className="copy-mini-btn"
                      onClick={() => handleCopy(s.finalAnswer)}
                      title="Copy Verdict"
                    >
                      📋 Copy
                    </button>
                  </div>
                  <p className="saved-row-verdict">{s.finalAnswer}</p>
                  <div className="saved-row-footer">
                    <span className="models-mini-tag">
                      Models: {s.fighters?.join(', ')}
                    </span>
                    <Link to={`/app/arena/${s.battleId}`} className="text-link-xs">
                      Open Debate →
                    </Link>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
