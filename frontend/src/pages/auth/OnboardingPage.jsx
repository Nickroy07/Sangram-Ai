import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { Button } from '../../components/common/Button';
import { Logo } from '../../components/common/Logo';
import { catalogApi, userApi } from '../../services/api';

export const OnboardingPage = () => {
  const [step, setStep] = useState(1);
  const [selectedRole, setSelectedRole] = useState('Engineer / Architect');
  const [favoriteModels, setFavoriteModels] = useState([]);
  const [favoriteArchetype, setFavoriteArchetype] = useState('');
  const [models, setModels] = useState([]);
  const [archetypes, setArchetypes] = useState([]);
  const [saving, setSaving] = useState(false);

  const { user, setUser } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  useEffect(() => { Promise.all([catalogApi.models(), catalogApi.archetypes()]).then(([modelList, archetypeList]) => {
    setModels(modelList); setArchetypes(archetypeList);
    setFavoriteModels(modelList.filter((model) => model.is_available).slice(0, 2).map((model) => model.id));
    setFavoriteArchetype(archetypeList[0]?.id || '');
  }).catch((err) => showToast(err.message, 'error')); }, []);

  const toggleModel = (id) => {
    if (favoriteModels.includes(id)) {
      if (favoriteModels.length > 2) {
        setFavoriteModels(favoriteModels.filter(m => m !== id));
      } else {
        showToast('Please keep at least 2 models selected for arena battles.', 'warn');
      }
    } else {
      setFavoriteModels([...favoriteModels, id]);
    }
  };

  const handleFinish = async () => {
    setSaving(true);
    try {
      const updated = await userApi.completeOnboarding({ occupation: selectedRole, models: favoriteModels, archetype: favoriteArchetype });
      setUser(updated); showToast('Preferences saved.', 'success'); navigate('/app');
    } catch (err) { showToast(err.message, 'error'); }
    finally { setSaving(false); }
  };

  const roles = [
    'Software Engineer / Architect',
    'AI Researcher / Data Scientist',
    'Product Manager / Strategist',
    'Technical Leader / Founder',
    'Student / Researcher'
  ];

  return (
    <div className="onboarding-card animate-scale-in">
      <div className="flex justify-center mb-6">
        <Logo size="md" showWordmark={true} href="/home" />
      </div>

      <div className="onboarding-progress-bar">
        <div className={`step-dot ${step >= 1 ? 'active' : ''}`}>1</div>
        <div className="step-line"></div>
        <div className={`step-dot ${step >= 2 ? 'active' : ''}`}>2</div>
        <div className="step-line"></div>
        <div className={`step-dot ${step >= 3 ? 'active' : ''}`}>3</div>
      </div>

      {step === 1 && (
        <div className="onboarding-step-content animate-fade-in">
          <h2 className="onboarding-title">How do you plan to use Sangram AI?</h2>
          <p className="onboarding-sub">Tell us your focus so we can tailor the dialectic consensus weighting.</p>

          <div className="role-options-list">
            {roles.map(role => (
              <button
                key={role}
                type="button"
                className={`role-select-card ${selectedRole === role ? 'selected' : ''}`}
                onClick={() => setSelectedRole(role)}
              >
                <span className="role-radio">{selectedRole === role ? '●' : '○'}</span>
                <span className="role-text">{role}</span>
              </button>
            ))}
          </div>

          <div className="onboarding-actions">
            <div></div>
            <Button variant="primary" onClick={() => setStep(2)}>
              Next: Select Models →
            </Button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="onboarding-step-content animate-fade-in">
          <h2 className="onboarding-title">Pick your core debate combatants</h2>
          <p className="onboarding-sub">Choose at least two models to confront each other in your arena.</p>

          <div className="models-onboarding-grid">
            {models.map(m => {
              const selected = favoriteModels.includes(m.id);
              return (
                <div
                  key={m.id}
                  className={`model-pick-card ${selected ? 'picked' : ''} ${!m.is_available ? 'unavailable' : ''}`}
                  onClick={() => m.is_available && toggleModel(m.id)}
                >
                  <div className="model-pick-top">
                    <span className="model-pick-dot" style={{ backgroundColor: m.accent.color }}></span>
                    <span className="model-pick-name">{m.name}</span>
                    <span className="pick-checkbox">{selected ? '✓' : '+'}</span>
                  </div>
                  <span className="model-pick-provider">{m.provider} · {m.modelLabel}</span>
                  <p className="model-pick-desc">{m.desc}</p>
                </div>
              );
            })}
          </div>

          <div className="onboarding-actions">
            <Button variant="outline" onClick={() => setStep(1)}>
              ← Back
            </Button>
            <Button variant="primary" onClick={() => setStep(3)}>
              Next: Cognitive Lens →
            </Button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="onboarding-step-content animate-fade-in">
          <h2 className="onboarding-title">Default Cognitive Lens</h2>
          <p className="onboarding-sub">Assign a thinking style that challenges baseline consensus.</p>

          <div className="archetypes-onboarding-grid">
            {archetypes.slice(0, 4).map(arch => (
              <div
                key={arch.id}
                className={`archetype-pick-card ${favoriteArchetype === arch.id ? 'picked' : ''}`}
                onClick={() => setFavoriteArchetype(arch.id)}
              >
                <div className="arch-top">
                  <span className="arch-name">{arch.name}</span>
                  {favoriteArchetype === arch.id && <span className="arch-check">✓</span>}
                </div>
                <p className="arch-desc">{arch.description}</p>
              </div>
            ))}
          </div>

          <div className="onboarding-actions">
            <Button variant="outline" onClick={() => setStep(2)}>
              ← Back
            </Button>
            <Button variant="primary" onClick={handleFinish} loading={saving} disabled={saving || favoriteModels.length < 2}>
              Enter Workspace Chamber 🚀
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
