import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { battlesApi } from '../../services/api';
import { Button } from '../../components/common/Button';

export const HistoryPage = () => {
  const [battles, setBattles] = useState([]);
  const [search, setSearch] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('All');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await battlesApi.history();
        setBattles(response.items || []);
      } catch (err) { setError(err.message); }
      finally { setLoading(false); }
    };
    fetchHistory();
  }, []);

  const statuses = [
    { id: 'All', label: 'All battles' },
    { id: 'pending', label: 'Pending' },
    { id: 'running', label: 'Running' },
    { id: 'completed', label: 'Completed' },
    { id: 'failed', label: 'Failed' }
  ];

  const filtered = battles.filter(b => {
    const matchesSearch = `${b.title || ''} ${b.summary || ''} ${(b.models || []).join(' ')}`.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = selectedStatus === 'All' || b.status === selectedStatus;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="history-page-view">
      <div className="page-header-row">
        <div>
          <h1 className="page-title">Battle History & Logs</h1>
          <p className="page-sub">Review past multi-model dialectic sessions and synthesis records.</p>
        </div>
        <Link to="/app/arena">
          <Button variant="primary" icon="⚔">New Battle</Button>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="filter-search-bar mt-6">
        <div className="search-box-wrap">
          <input
            type="text"
            className="clean-input"
            placeholder="Search battles by dilemma topic, model, or keyword..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="tag-filter-pills">
          {statuses.map(({ id, label }) => (
            <button
              key={id}
              type="button"
              className={`tag-pill-btn ${selectedStatus === id ? 'active' : ''}`}
              onClick={() => setSelectedStatus(id)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Clean History List */}
      <div className="history-clean-list mt-6">
        {loading ? <p className="text-muted">Loading your battle history…</p> : error ? <p className="auth-alert error-alert" role="alert">{error}</p> : filtered.length === 0 ? (
          <div className="empty-panel text-center py-8">
            <p className="text-muted">No battle logs match your search.</p>
          </div>
        ) : (
          filtered.map((b) => (
            <div key={b.id} className="history-row-item">
              <div className="history-row-main">
                <div className="history-meta-bar">
                  <span className="clean-topic-badge">{b.topic || 'General'}</span>
                  <span className="clean-date-text">
                    {new Date(b.date).toLocaleDateString(undefined, {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric'
                    })}
                  </span>
                  {b.consensusScore && (
                    <span className="consensus-pill">★ {b.consensusScore}% Consensus</span>
                  )}
                </div>

                <h3 className="history-item-title">
                  <Link to={`/app/arena/${b.id}`}>{b.title}</Link>
                </h3>
                <p className="history-item-summary">{b.summary}</p>
              </div>

              <div className="history-row-actions">
                <Link to={`/app/arena/${b.id}`}>
                  <Button variant="outline" size="sm">
                    Open Battle →
                  </Button>
                </Link>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
