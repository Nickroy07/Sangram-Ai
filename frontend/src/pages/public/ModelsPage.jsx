import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { catalogApi } from '../../services/api';
import { models as modelStyles } from '../../data/models';
import { Button } from '../../components/common/Button';

export const ModelsPage = () => {
  const [models, setModels] = useState([]);
  const [loadError, setLoadError] = useState('');
  useEffect(() => { catalogApi.models().then(setModels).catch((error) => setLoadError(error.message)); }, []);
  const [selectedModels, setSelectedModels] = useState(['chatgpt', 'claude']);
  const [activeFilter, setActiveFilter] = useState('all');

  const toggleSelect = (id) => {
    if (selectedModels.includes(id)) {
      if (selectedModels.length > 2) {
        setSelectedModels(selectedModels.filter(m => m !== id));
      }
    } else {
      setSelectedModels([...selectedModels, id]);
    }
  };

  const modelSpecs = {
    chatgpt: {
      traits: ['First-Principles Reasoning', 'Structured Proofs', 'Broad Generalization'],
      strengths: 'System architecture, API design, structured decomposition',
      style: 'Confident, comprehensive, deductive'
    },
    gemini: {
      traits: ['Massive Context Synthesis', 'Multimodal Correlation', 'Cross-Domain Reference'],
      strengths: 'Large codebase analysis, paper syntheses, documentation cross-referencing',
      style: 'Expansive, associative, research-grounded'
    },
    claude: {
      traits: ['Nuance & Epistemic Caution', 'Operational Risk Auditing', 'Edge-Case Sensitivity'],
      strengths: 'Refactoring risks, dependency vulnerability, organizational friction',
      style: 'Methodical, questioning, boundary-conscious'
    },
    llama: {
      traits: ['Open-Weights Flagship', 'Systems-Level Logic', 'Concise Code Constructs'],
      strengths: 'Kernel performance, local deployment economics, low-level data flows',
      style: 'Direct, technical, unvarnished'
    },
    mistral: {
      traits: ['Code-Forward Precision', 'High Efficiency', 'Minimalist Rhetoric'],
      strengths: 'Algorithmic density, clean functional patterns, token economy',
      style: 'Terse, high-information-density, pragmatic'
    },
    grok: {
      traits: ['Contrarian Stress-Testing', 'Consensus Skepticism', 'Unconventional Scenarios'],
      strengths: 'Challenging industry groupthink, stress-testing black swan conditions',
      style: 'Bold, provocative, boundary-testing'
    }
  };

  return (
    <div className="models-page-view">
      <div className="page-hero-banner">
        <div className="section-container text-center">
          <span className="section-tag">CATALOG & PROFILES</span>
          <h1 className="page-hero-title">The Six Combatants of Sangram AI</h1>
          <p className="page-hero-sub">
            Compare the models enabled for Sangram AI battles. Availability depends on the provider integrations configured for the service.
          </p>
        </div>
      </div>

      <div className="section-container py-12">
        {/* Model Matchup Selection Bar */}
        <div className="matchup-bar">
          <div className="matchup-info">
            <span className="matchup-label">Active Matchup Selection:</span>
            <span className="matchup-models">
              {selectedModels.map(id => {
                const m = models.find(mod => mod.id === id);
                return m ? m.name : id;
              }).join(' vs ')}
            </span>
          </div>
          <Link to={`/app/arena/new?m1=${selectedModels[0] || 'chatgpt'}&m2=${selectedModels[1] || 'claude'}`}>
            <Button variant="primary" size="sm" icon="⚔">
              Enter Arena with this Matchup →
            </Button>
          </Link>
        </div>

        {/* Models Grid */}
        {loadError && <p className="auth-alert error-alert" role="alert">{loadError}</p>}
        <div className="models-full-grid">
          {models.map((m) => {
            const isSelected = selectedModels.includes(m.id);
            const extra = modelSpecs[m.id] || {};

            return (
              <div
                key={m.id}
                className={`model-detail-card ${isSelected ? 'is-selected' : ''}`}
                style={{ '--accent-color': modelStyles.find((item) => item.id === m.id)?.accent.color || '#5B9DFF' }}
              >
                <div className="card-top-row">
                  <div className="model-brand-group">
                    <span className="color-indicator" style={{ backgroundColor: modelStyles.find((item) => item.id === m.id)?.accent.color || '#5B9DFF' }}></span>
                    <div>
                      <h3 className="model-title-text">{m.name}</h3>
                      <span className="provider-name">{m.provider} · {m.modelLabel}</span>
                    </div>
                  </div>
                  <button
                    type="button"
                    className={`select-chip-btn ${isSelected ? 'active' : ''}`}
                    onClick={() => toggleSelect(m.id)}
                  >
                    {isSelected ? '✓ In Matchup' : '+ Add to Matchup'}
                  </button>
                </div>

                <p className="model-core-desc">{m.desc}</p>

                <div className="traits-section">
                  <span className="traits-heading">Cognitive Traits:</span>
                  <div className="traits-chips-row">
                    {extra.traits?.map((trait, idx) => (
                      <span key={idx} className="trait-tag">{trait}</span>
                    ))}
                  </div>
                </div>

                <div className="spec-meta-list">
                  <div className="meta-item">
                    <span className="meta-key">Arena Strengths:</span>
                    <span className="meta-val">{extra.strengths}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-key">Debate Style:</span>
                    <span className="meta-val">{extra.style}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-key">Availability:</span>
                    <span className="meta-status">{m.is_available ? 'Available' : 'Provider key required'}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

