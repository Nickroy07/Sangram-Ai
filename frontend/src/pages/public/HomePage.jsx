import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { faqs } from '../../data/faqs';
import { billingApi, catalogApi } from '../../services/api';
import { Button } from '../../components/common/Button';

export const HomePage = () => {
  const [activeFaq, setActiveFaq] = useState(0);
  const [models, setModels] = useState([]);
  const [plans, setPlans] = useState([]);
  const [catalogError, setCatalogError] = useState('');

  useEffect(() => {
    Promise.all([catalogApi.models(), billingApi.plans()])
      .then(([modelCatalog, planCatalog]) => {
        setModels(modelCatalog);
        setPlans(planCatalog.map((plan) => ({
          ...plan,
          tagline: plan.description,
          price: { monthly: plan.pricing.monthlyCents / 100 },
          period: '/ month',
          popular: plan.id === 'pro',
          features: plan.features.slice(0, 4).map((text) => ({ text, included: true })),
          cta: plan.id === 'free' ? 'Start Free' : `Choose ${plan.name}`,
          ctaLink: plan.id === 'free' ? '/auth/signup' : `/checkout?plan=${plan.id}&interval=monthly`,
        })));
      })
      .catch((error) => setCatalogError(error.message));
  }, []);

  const benefits = [
    {
      num: '01',
      title: 'Multiple Perspectives',
      desc: 'Never rely on a single model’s blind spots. Compare answers from different frontier architectures side by side in real time.',
      icon: '✦'
    },
    {
      num: '02',
      title: 'Structured Cross-Examination',
      desc: 'Models actively critique each other’s claims across multiple rounds, exposing omissions, hallucinations, and unverified assumptions.',
      icon: '⚔'
    },
    {
      num: '03',
      title: 'One Consolidated Answer',
      desc: 'Our Dialectic Synthesis engine extracts points of agreement, resolves legitimate trade-offs, and delivers one clear, actionable conclusion.',
      icon: '⚡'
    }
  ];

  const steps = [
    {
      step: '01',
      title: 'Select Combatants',
      desc: 'Choose two frontier AI models (e.g. Claude 3.5 Sonnet vs GPT-4o) and assign distinct cognitive perspectives.'
    },
    {
      step: '02',
      title: 'State the Dilemma',
      desc: 'Submit a hard technical trade-off, architectural question, strategic decision, or research query.'
    },
    {
      step: '03',
      title: 'Witness the Debate',
      desc: 'Models debate across rounds: presenting thesis claims, raising counterarguments, and revising their positions.'
    },
    {
      step: '04',
      title: 'Receive Synthesis',
      desc: 'Review the written synthesis and trade-offs, then copy the result into your workflow.'
    }
  ];

  return (
    <div className="home-page-view">
      {/* SECTION 1: Restored Motion Series Hero with Looping Fibre-Optic Light Video & Glassmorphism */}
      <section className="home-hero-section hero" id="top">
        {/* Looping Fibre-Optic Light-Painting Video Background */}
        <video
          className="hero-art-video"
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
          aria-hidden="true"
          poster="https://d2ol7oe51mr4n9.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/130837c4-0244-4f37-9c61-8d801d93fd29.jpg"
          src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260912_104303_0c6d60b2-9353-408e-9449-585108a22fb5.mp4"
        />

        {/* Motion Series Multi-Gradient Veil for High-Contrast Text Legibility */}
        <div className="hero-veil" aria-hidden="true" />

        <div className="hero-content-container">
          <div className="hero-badge">
            <span className="hero-badge-dot"></span>
            <span>DIALECTIC AI WORKSPACE</span>
          </div>

          <h1 className="hero-main-title">
            Different Minds.<br />
            <span className="hero-glow-text">One Arena.</span>
          </h1>

          <p className="hero-supporting-title">
            What Happens When AI Challenges AI?
          </p>

          <p className="hero-description-text">
            Bring different AI models into one arena. Compare their reasoning, challenge their answers, and discover one consolidated response.
          </p>

          {/* Motion Series Glassmorphism CTA Actions */}
          <div className="hero-actions-row">
            <Link to="/app/arena">
              <button type="button" className="btn btn-primary btn-lg btn-glass-cta hero-primary-btn">
                <span>Enter the Arena</span>
                <span className="btn-icon">⚔</span>
              </button>
            </Link>
            <a href="#how-it-works">
              <button type="button" className="btn btn-secondary btn-lg hero-secondary-btn">
                <span>Explore How It Works ↓</span>
              </button>
            </a>
          </div>

          {/* Product availability */}
          <div className="hero-meta-row">
            <span className="hero-proto-label">
              <span className="demo-dot" aria-hidden="true" />
              Live model debates, with provider availability shown in your workspace
            </span>
            <Link to="/features" className="neural-link-pill" title="Explore Sangram AI features"><span>Explore features</span><span aria-hidden="true">?</span></Link>
          </div>

          <div className="hero-trust-row mt-6">
            <span className="trust-label">Compatible with leading foundational model profiles:</span>
            <div className="trust-model-chips">
              {models.map((model) => <span className="t-chip" key={model.id}>{model.name}</span>)}
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 2: Clean Arena Demonstration Visual */}
      <section className="section-arena-visual">
        <div className="section-container">
          <div className="section-header text-center">
            <span className="section-tag">HOW THE ARENA WORKS</span>
            <h2 className="section-title">The Dialectic Arena in Action</h2>
            <p className="section-desc">
              Two models examine: <em>"Should an early-stage B2B SaaS adopt Microservices or a Modular Monolith?"</em>
            </p>
          </div>

          <div className="arena-interactive-card">
            {/* Top Bar */}
            <div className="arena-card-topbar">
              <div className="arena-status-group">
                <span className="status-live-dot"></span>
                <span className="status-live-text">EXAMPLE DEBATE · CROSS-EXAMINATION</span>
              </div>
              <div className="arena-model-pills">
                <span className="model-pill pill-gpt">ChatGPT (GPT-4o)</span>
                <span className="vs-connector">VS</span>
                <span className="model-pill pill-claude">Claude (Sonnet 3.5)</span>
              </div>
            </div>

            {/* Clash Stream */}
            <div className="arena-clash-body">
              <div className="clash-column col-left">
                <div className="fighter-badge fighter-gpt">
                  <span className="f-icon">✦</span>
                  <span className="f-name">ChatGPT</span>
                  <span className="f-role">Initial Thesis</span>
                </div>
                <div className="clash-speech-bubble">
                  <p>
                    "Microservices allow independent deployment velocity and isolate domain failures. If your startup anticipates rapid scaling, establishing network boundaries early prevents painful monolithic refactors later."
                  </p>
                </div>
              </div>

              <div className="clash-center-dialectic">
                <span className="dialectic-vs">VS</span>
              </div>

              <div className="clash-column col-right">
                <div className="fighter-badge fighter-claude">
                  <span className="f-icon">🛡</span>
                  <span className="f-name">Claude</span>
                  <span className="f-role">Cross-Examination</span>
                </div>
                <div className="clash-speech-bubble">
                  <p>
                    "That advice ignores distributed systems tax. A seed team with 6 engineers will waste 40% of sprint capacity managing gRPC interfaces, network latency, and distributed traces. A Modular Monolith yields identical boundaries with zero operational overhead."
                  </p>
                </div>
              </div>
            </div>

            {/* Synthesis Verdict */}
            <div className="arena-synthesis-verdict">
              <div className="verdict-header">
                <div className="verdict-title-group">
                  <span className="verdict-star">★</span>
                  <h4 className="verdict-heading">Consolidated Dialectic Verdict</h4>
                </div>
                <span className="confidence-pill">Synthesis preview</span>
              </div>
              <div className="verdict-body">
                <p className="verdict-takeaway">
                  <strong>Unified Conclusion:</strong> Build a <strong>Modular Monolith</strong> now with strict directory-level boundary enforcement. Only bifurcate a component into an independent microservice when that specific module experiences 10x differential traffic or requires dedicated hardware acceleration.
                </p>
              </div>
              <div className="verdict-footer">
                <span className="tensions-tag">Resolved: Operational Tax vs Domain Isolation</span>
                <Link to="/app/arena" className="try-arena-link">
                  Launch Custom Battle with this Prompt →
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 3: Product Benefits */}
      <section className="section-benefits">
        <div className="section-container">
          <div className="section-header text-center">
            <span className="section-tag">WHY SANGRAM AI</span>
            <h2 className="section-title">Rethinking How We Reason With AI</h2>
            <p className="section-desc">
              Moving beyond the echo-chamber of single-model chatbots.
            </p>
          </div>

          <div className="benefits-grid">
            {benefits.map((b) => (
              <div key={b.num} className="benefit-card">
                <div className="benefit-top">
                  <span className="benefit-num">{b.num}</span>
                  <span className="benefit-icon">{b.icon}</span>
                </div>
                <h3 className="benefit-title">{b.title}</h3>
                <p className="benefit-desc">{b.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SECTION 4: How It Works */}
      <section className="section-how-it-works" id="how-it-works">
        <div className="section-container">
          <div className="section-header text-center">
            <span className="section-tag">WORKFLOW</span>
            <h2 className="section-title">From Question to Consolidated Truth</h2>
            <p className="section-desc">Four structured stages designed to extract high-conviction answers.</p>
          </div>

          <div className="steps-connected-grid">
            {steps.map((st) => (
              <div key={st.step} className="step-card">
                <div className="step-num-badge">{st.step}</div>
                <h3 className="step-title">{st.title}</h3>
                <p className="step-desc">{st.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SECTION 5: Supported Models */}
      <section className="section-models-showcase">
        <div className="section-container">
          <div className="section-header text-center">
            <span className="section-tag">THE COMBATANTS</span>
            <h2 className="section-title">Six World-Class Model Architectures</h2>
            <p className="section-desc">
              Each tuned with distinct epistemic traits, strengths, and reasoning styles.
            </p>
          </div>

          {catalogError && <p className="auth-alert error-alert" role="alert">{catalogError}</p>}
          <div className="models-showcase-grid">
            {models.map((m) => (
              <div key={m.id} className="showcase-model-card">
                <div className="model-card-top">
                  <span className="m-accent-dot" style={{ backgroundColor: m.accent?.color || '#5B9DFF' }}></span>
                  <span className="m-name">{m.name}</span>
                  <span className="m-badge">{m.provider}</span>
                </div>
                <div className="m-version">{m.modelLabel}</div>
                <p className="m-desc">{m.desc}</p>
                <div className="m-footer">
                  <span className="m-status-text">{m.is_available ? 'Available' : 'Provider key required'}</span>
                  <Link to={m.is_available ? ("/app/arena/new?m1=" + m.id) : "/models"} className="m-select-btn">{m.is_available ? "Configure" : "Details"}</Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SECTION 6: Transparent Pricing Preview */}
      <section className="section-pricing-preview">
        <div className="section-container">
          <div className="section-header text-center">
            <span className="section-tag">TRANSPARENT PLANS</span>
            <h2 className="section-title">Built for Engineers, Researchers, and Teams</h2>
            <p className="section-desc">Compare the current plan catalog. Paid subscriptions are not available yet.</p>
          </div>

          {catalogError && <p className="auth-alert error-alert" role="alert">{catalogError}</p>}
          <div className="pricing-cards-grid">
            {plans.slice(0, 3).map((plan) => (
              <div key={plan.id} className={`pricing-card ${plan.popular ? 'card-featured' : ''}`}>
                {plan.badge && <span className="plan-badge">{plan.badge}</span>}
                <h3 className="plan-name">{plan.name}</h3>
                <p className="plan-tagline">{plan.tagline}</p>
                <div className="plan-price-row">
                  <span className="price-num">${plan.price.monthly}</span>
                  <span className="price-period">{plan.period}</span>
                </div>
                <ul className="plan-feature-list">
                  {plan.features.slice(0, 4).map((f, i) => (
                    <li key={i} className={f.included ? 'feat-yes' : 'feat-no'}>
                      <span>{f.included ? '✓' : '—'}</span>
                      <span>{f.text}</span>
                    </li>
                  ))}
                </ul>
                {plan.id === 'free' ? <Link to={plan.ctaLink} className="plan-cta-wrapper"><Button variant="outline" className="w-full">{plan.cta}</Button></Link> : <Button variant="outline" className="w-full" disabled>Payments unavailable</Button>}
              </div>
            ))}
          </div>

          <div className="text-center mt-6">
            <Link to="/pricing" className="view-full-pricing-link">
              View full plan matrix & feature comparison →
            </Link>
          </div>
        </div>
      </section>

      {/* SECTION 7: FAQ */}
      <section className="section-faq">
        <div className="section-container">
          <div className="section-header text-center">
            <span className="section-tag">FREQUENTLY ASKED QUESTIONS</span>
            <h2 className="section-title">Answers to Common Inquiries</h2>
            <p className="section-desc">Everything you need to know about dialectic battles.</p>
          </div>

          <div className="faq-accordion-list">
            {faqs.slice(0, 5).map((faq, index) => {
              const isOpen = activeFaq === index;
              return (
                <div key={index} className={`faq-item ${isOpen ? 'open' : ''}`}>
                  <button
                    type="button"
                    className="faq-question-btn"
                    onClick={() => setActiveFaq(isOpen ? -1 : index)}
                    aria-expanded={isOpen}
                  >
                    <span className="faq-q-text">{faq.q}</span>
                    <span className="faq-chevron">{isOpen ? '−' : '+'}</span>
                  </button>
                  {isOpen && (
                    <div className="faq-answer-body">
                      <p>{faq.a}</p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* SECTION 8: Final CTA */}
      <section className="section-final-cta">
        <div className="section-container">
          <div className="final-cta-card">
            <h2 className="cta-headline">Ready to Enter the Arena?</h2>
            <p className="cta-desc">
              Bring different perspectives together and reach a stronger conclusion. Launch your first dialectic session in seconds.
            </p>
            <div className="cta-btn-group">
              <Link to="/app/arena">
                <Button variant="primary" size="lg" icon="⚔">
                  Enter the Arena Now
                </Button>
              </Link>
              <Link to="/auth/signup">
                <Button variant="outline" size="lg">
                  Create Free Account
                </Button>
              </Link>
            </div>
            <span className="cta-sub-note">No credit card required · Free tier available</span>
          </div>
        </div>
      </section>
    </div>
  );
};

