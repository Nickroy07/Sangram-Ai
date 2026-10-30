import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { faqs } from '../../data/faqs';
import { billingApi } from '../../services/api';
import { Button } from '../../components/common/Button';

const billingFrequencies = [
  { id: 'monthly', label: 'Monthly' },
  { id: 'yearly', label: 'Annual' }
];

export const PricingPage = () => {
  const [interval, setInterval] = useState('monthly');
  const [activeFaq, setActiveFaq] = useState(0);
  const [plans, setPlans] = useState([]);
  const [error, setError] = useState('');
  useEffect(() => { billingApi.plans().then((items) => setPlans(items.map((item) => ({
    ...item, popular: false, tagline: item.description,
    price: { monthly: item.pricing.monthlyCents / 100, yearly: item.pricing.yearlyCents / 1200 },
    period: '/ month', cta: item.id === 'free' ? 'Create account' : 'Payments unavailable',
    features: item.features.map((text) => ({ text, included: true }))
  })))).catch((err) => setError(err.message)); }, []);

  return (
    <div className="pricing-page-view">
      <div className="page-hero-banner">
        <div className="section-container text-center">
          <span className="section-tag">INVESTMENT IN CLARITY</span>
          <h1 className="page-hero-title">Predictable Plans for High-Conviction Decisions</h1>
          <p className="page-hero-sub">
            Whether you are testing individual architectural hunches or equipping an enterprise engineering squad, Sangram AI scales with you.
          </p>

          {/* Billing Frequency Toggle */}
          <div className="billing-toggle-container mt-8">
            <div className="toggle-pill-wrapper">
              {billingFrequencies.map((f) => (
                <button
                  key={f.id}
                  type="button"
                  className={`toggle-option-btn ${interval === f.id ? 'active' : ''}`}
                  onClick={() => setInterval(f.id)}
                >
                  <span>{f.label}</span>
                  {f.discountBadge && <span className="discount-tag">{f.discountBadge}</span>}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="section-container py-12">
        <p className="auth-alert error-alert" role="status">Paid plans are catalog entries only. Checkout, subscriptions, and plan entitlements are not enabled yet.</p>
        {/* Pricing Cards Grid (4 Plans: Free, Pro, Power, Team) */}
        <div className="pricing-cards-full-grid">
          {error && <p className="auth-alert error-alert" role="alert">{error}</p>}
          {plans.map((p) => {
            const price = interval === 'yearly' ? p.price.yearly : p.price.monthly;
            const checkoutUrl = '/auth/signup';

            return (
              <div
                key={p.id}
                className={`full-pricing-card ${p.popular ? 'card-highlighted' : ''}`}
              >
                {p.badge && <div className="card-top-badge">{p.badge}</div>}
                <div className="card-header-block">
                  <h3 className="plan-title">{p.name}</h3>
            <p className="plan-subtitle">{p.description}</p>
                </div>

                <div className="card-price-block">
                  <div className="price-number-row">
                    <span className="currency">$</span>
                    <span className="amount">{price}</span>
                    <span className="cadence">{p.period}</span>
                  </div>
                  {interval === 'yearly' && p.price.monthly > 0 && (
                    <span className="annual-billed-note">Billed annually (${price * 12}/yr)</span>
                  )}
                  {p.price.monthly === 0 && <span className="annual-billed-note">No subscription charge</span>}
                </div>

                <div className="card-cta-wrapper">
                  {p.id === 'free' ? <Link to={checkoutUrl} className="w-full block"><Button variant="outline" size="lg" className="w-full">{p.cta}</Button></Link> : <Button variant="outline" size="lg" className="w-full" disabled>{p.cta}</Button>}
                </div>

                <div className="card-features-block">
                  <span className="features-header-title">What is included:</span>
                  <ul className="plan-perks-list">
                {p.features.map((feat, idx) => (
                      <li key={idx} className={feat.included ? 'perk-active' : 'perk-inactive'}>
                        <span className="perk-bullet">{feat.included ? '✓' : '—'}</span>
                        <span className="perk-label">{feat.text}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            );
          })}
        </div>

        {/* Pricing FAQs */}
        <div className="pricing-faq-section mt-16">
          <div className="text-center mb-8">
            <span className="section-tag">FREQUENTLY ASKED</span>
            <h2 className="section-title">Billing & Subscription Questions</h2>
          </div>

          <div className="faq-accordion-list">
            {faqs.slice(0, 4).map((faq, idx) => {
              const isOpen = activeFaq === idx;
              return (
                <div key={idx} className={`faq-item ${isOpen ? 'open' : ''}`}>
                  <button
                    type="button"
                    className="faq-question-btn"
                    onClick={() => setActiveFaq(isOpen ? -1 : idx)}
                  >
                    <span className="faq-q-text">{faq.q}</span>
                    <span className="faq-chevron">{isOpen ? '−' : '+'}</span>
                  </button>
                  {isOpen && (
                    <div className="faq-answer-body animate-fade-in">
                      <p>{faq.a}</p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
