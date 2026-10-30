import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../../context/ToastContext';
import { catalogApi, battlesApi } from '../../services/api';
import { Button } from '../../components/common/Button';

export const ArenaNewPage = () => {
  const [models, setModels] = useState([]);
  const [archetypes, setArchetypes] = useState([]);
  const [catalogError, setCatalogError] = useState('');
  const [modelA, setModelA] = useState('');
  const [modelB, setModelB] = useState('');
  const [archetypeA, setArchetypeA] = useState('');
  const [archetypeB, setArchetypeB] = useState('');
  const [prompt, setPrompt] = useState('');
  const [context, setContext] = useState('');
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();
  const { showToast } = useToast();

  useEffect(() => {
    Promise.all([catalogApi.models(), catalogApi.archetypes()]).then(([modelList, archetypeList]) => {
      setModels(modelList);
      setArchetypes(archetypeList);
      const available = modelList.filter((model) => model.is_available);
      setModelA(available[0]?.id || '');
      setModelB(available[1]?.id || '');
      setArchetypeA(archetypeList[0]?.id || '');
      setArchetypeB(archetypeList[1]?.id || archetypeList[0]?.id || '');
    }).catch((error) => setCatalogError(error.message));
  }, []);

  const samplePrompts = [
    {
      label: 'Microservices vs Monolith',
      q: 'Microservices vs Modular Monolith for an early-stage B2B SaaS startup?'
    },
    {
      label: 'PostgreSQL vs Vector DB',
      q: 'Should our startup start with pgvector in Postgres or provision a managed Pinecone cluster?'
    },
    {
      label: 'Python vs Rust for AI',
      q: 'Python vs Rust for high-throughput LLM streaming inference pipelines?'
    }
  ];

  const handleStartBattle = async (e) => {
    e.preventDefault();
    if (!prompt.trim()) {
      showToast('Please enter a question or dilemma for the arena.', 'warn');
      return;
    }
    if (modelA === modelB) {
      showToast('Please choose two different models to debate.', 'warn');
      return;
    }

    try {
      setLoading(true);
      const created = await battlesApi.create({
        question: prompt.trim(),
        modelA,
        modelB,
        archetypeA,
        archetypeB,
        context
      });
      navigate(`/app/arena/${created.battleId}`);
    } catch (err) {
      showToast(err.message || 'Failed to start battle.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="arena-new-page-view">
      <div className="arena-setup-header">
        <h1 className="setup-title">Deploy Dialectic Combatants</h1>
        <p className="setup-sub">
          Select two distinct model architectures, set their cognitive lenses, and pose your technical or strategic dilemma.
        </p>
      </div>

      <form onSubmit={handleStartBattle} className="arena-setup-form mt-6">
        {catalogError && <div className="auth-alert error-alert" role="alert">{catalogError}</div>}
        {!catalogError && models.length > 0 && models.every((model) => !model.is_available) && (
          <div className="auth-alert error-alert" role="status">No AI providers are configured yet. Add a provider key to the backend environment to enable battles.</div>
        )}
        {/* Step 1: The Dilemma Input */}
        <div className="setup-card">
          <label className="field-label" htmlFor="prompt-input">
            1. What question or dilemma should the models debate?
          </label>
          <textarea
            id="prompt-input"
            className="clean-textarea"
            rows="3"
            placeholder="E.g., Microservices vs Modular Monolith for an early-stage startup?"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            required
          />

          <div className="quick-prompts-row mt-2">
            <span className="quick-prompts-label">Try sample:</span>
            {samplePrompts.map((sp) => (
              <button
                key={sp.label}
                type="button"
                className="sample-prompt-chip"
                onClick={() => setPrompt(sp.q)}
              >
                {sp.label}
              </button>
            ))}
          </div>
        </div>

        {/* Step 2: The Two Combatants */}
        <div className="setup-card mt-6">
          <label className="field-label">2. Select Combatants & Perspectives</label>

          <div className="combatants-split-grid mt-3">
            {/* Combatant A */}
            <div className="combatant-box">
              <span className="box-badge-label">Combatant 01 · Thesis</span>
              <div className="input-group mt-2">
                <label className="select-sublabel">Model</label>
                <select
                  className="clean-select"
                  value={modelA}
                  onChange={(e) => setModelA(e.target.value)}
                >
                  {models.map((m) => (
                    <option key={m.id} value={m.id} disabled={!m.is_available || m.id === modelB}>
                      {m.name} ({m.provider})
                    </option>
                  ))}
                </select>
              </div>

              <div className="input-group mt-3">
                <label className="select-sublabel">Cognitive Perspective</label>
                <select
                  className="clean-select"
                  value={archetypeA}
                  onChange={(e) => setArchetypeA(e.target.value)}
                >
                  {archetypes.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.name} — {a.lens}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="combatant-vs-divider">
              <span className="vs-tag">VS</span>
            </div>

            {/* Combatant B */}
            <div className="combatant-box">
              <span className="box-badge-label">Combatant 02 · Counter-Examiner</span>
              <div className="input-group mt-2">
                <label className="select-sublabel">Model</label>
                <select
                  className="clean-select"
                  value={modelB}
                  onChange={(e) => setModelB(e.target.value)}
                >
                  {models.map((m) => (
                    <option key={m.id} value={m.id} disabled={!m.is_available || m.id === modelA}>
                      {m.name} ({m.provider})
                    </option>
                  ))}
                </select>
              </div>

              <div className="input-group mt-3">
                <label className="select-sublabel">Cognitive Perspective</label>
                <select
                  className="clean-select"
                  value={archetypeB}
                  onChange={(e) => setArchetypeB(e.target.value)}
                >
                  {archetypes.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.name} — {a.lens}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Step 3: Optional Constraints */}
        <div className="setup-card mt-6">
          <label className="field-label" htmlFor="context-input">
            3. Context or Constraints <span className="text-muted text-xs">(optional)</span>
          </label>
          <input
            id="context-input"
            type="text"
            className="clean-input mt-2"
            placeholder="E.g., Team size: 5 engineers, 2-year runway, strict latency SLAs."
            value={context}
            onChange={(e) => setContext(e.target.value)}
          />
        </div>

        {/* Action Button */}
        <div className="setup-action-row mt-6">
          <Button
            type="submit"
            variant="primary"
            size="lg"
            className="w-full launch-battle-btn"
            loading={loading}
            disabled={loading || !modelA || !modelB || Boolean(catalogError)}
            icon="⚔"
          >
            Launch Dialectic Battle
          </Button>
        </div>
      </form>
    </div>
  );
};
