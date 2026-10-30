import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../../components/common/Button';

export const HowItWorksPage = () => {
  const workflowStages = [
    {
      num: '01',
      title: 'Select Combatant Models',
      desc: 'Choose two different model profiles from the live catalog. A model is selectable when its provider is configured on the backend. You can also assign cognitive archetypes to each participant.',
      visual: 'Choose two available models and optional archetypes'
    },
    {
      num: '02',
      title: 'Submit Question & Context',
      desc: 'Enter your question and optional context. The backend sends the prompt to each selected provider and stores the resulting battle in your account.',
      visual: 'Question Prompt + Optional Boundary Criteria'
    },
    {
      num: '03',
      title: 'Adversarial Debate & Cross-Examination',
      desc: 'The models exchange opening positions, counterarguments, rebuttals, and final positions. Each response is based on the battle context available to that provider call.',
      visual: 'Opening → Counterarguments → Rebuttals → Final positions'
    },
    {
      num: '04',
      title: 'Consolidated Synthesis & Verdict',
      desc: 'The backend asks the selected synthesis model to produce a written recommendation that separates points of agreement from unresolved trade-offs. A numeric consensus score is not currently calculated.',
      visual: 'Unified decision + trade-off summary'
    }
  ];

  return (
    <div className="how-it-works-view">
      <div className="page-hero-banner">
        <div className="section-container text-center">
          <span className="section-tag">METHODOLOGY</span>
          <h1 className="page-hero-title">How the Dialectic Engine Works</h1>
          <p className="page-hero-sub">
            A structured four-step dialectic process that replaces solitary guesswork with adversarial synthesis.
          </p>
        </div>
      </div>

      <div className="section-container py-12">
        <div className="workflow-timeline">
          {workflowStages.map((stage, i) => (
            <div key={stage.num} className="workflow-step-card">
              <div className="step-left">
                <span className="step-badge-large">{stage.num}</span>
                {i < workflowStages.length - 1 && <div className="step-stem-line"></div>}
              </div>
              <div className="step-right">
                <h3 className="step-stage-title">{stage.title}</h3>
                <p className="step-stage-desc">{stage.desc}</p>
                <div className="step-mock-visual">
                  <span className="visual-tag">Visual Protocol:</span>
                  <span className="visual-detail">{stage.visual}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="interactive-try-banner mt-12 text-center">
          <h3>Experience the Battle in Real Time</h3>
          <p>Start a battle with the AI providers enabled for your account.</p>
          <div className="mt-4">
            <Link to="/app/arena/new">
              <Button variant="primary" size="lg" icon="⚔">
                Launch Arena Session
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

