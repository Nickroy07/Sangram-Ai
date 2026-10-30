import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { savedApi } from '../../services/api';
import { useToast } from '../../context/ToastContext';
import { Button } from '../../components/common/Button';

export const SavedAnswersPage = () => {
  const [savedItems, setSavedItems] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { showToast } = useToast();

  useEffect(() => {
    const fetchSaved = async () => {
      try { setSavedItems(await savedApi.list()); }
      catch (err) { setError(err.message); }
      finally { setLoading(false); }
    };
    fetchSaved();
  }, []);

  const handleCopy = (verdict) => {
    navigator.clipboard?.writeText(verdict);
    showToast('ADR verdict copied to clipboard!', 'success');
  };

  const handleRemove = async (id) => {
    try {
      await savedApi.remove(id);
      setSavedItems(prev => prev.filter(i => i.id !== id));
      showToast('Removed from saved answers.', 'info');
    } catch (err) { showToast(err.message, 'error'); }
  };

  const filtered = savedItems.filter(item =>
    (item.question || '').toLowerCase().includes(search.toLowerCase()) ||
    (item.finalAnswer || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="saved-answers-view">
      <div className="page-header-row">
        <div>
          <h1 className="page-title">Saved Answers & ADRs</h1>
          <p className="page-sub">
            Your repository of synthesized architectural decisions, verified trade-offs, and consensus answers.
          </p>
        </div>
      </div>

      <div className="search-bar-wrap mt-6">
        <input
          type="text"
          className="clean-input"
          placeholder="Filter saved ADR records by keyword or topic..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="saved-clean-list mt-6">
        {loading ? <p className="text-muted">Loading saved answers…</p> : error ? <p className="auth-alert error-alert" role="alert">{error}</p> : filtered.length === 0 ? (
          <div className="empty-panel text-center py-8">
            <p className="text-muted">No saved answers yet. In any arena debate, click 'Save as ADR Record'.</p>
          </div>
        ) : (
          filtered.map((item) => (
            <div key={item.id} className="saved-item-box">
              <div className="saved-box-header">
                <div>
                  <h3 className="saved-item-title">{item.question}</h3>
                  <p className="saved-item-q">"{item.question}"</p>
                </div>
                <button
                  type="button"
                  className="remove-cross-btn"
                  onClick={() => handleRemove(item.id)}
                  title="Remove from saved"
                  aria-label="Remove from saved"
                >
                  ✕
                </button>
              </div>

              <div className="saved-box-verdict">
                <p>{item.finalAnswer}</p>
              </div>

              <div className="saved-box-footer">
                <span className="models-mini-tag">
                  Models: {item.fighters?.join(', ')}
                </span>
                <div className="saved-footer-actions">
                  <Button variant="outline" size="sm" onClick={() => handleCopy(item.finalAnswer)}>
                    📋 Copy Text
                  </Button>
                  <Link to={`/app/arena/${item.battleId}`}>
                    <Button variant="secondary" size="sm">
                      View Debate →
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
