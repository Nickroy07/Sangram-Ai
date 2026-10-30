import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { faqs } from '../../data/faqs';
import { Button } from '../../components/common/Button';

export const FaqPage = () => {
  const [openIndexes, setOpenIndexes] = useState([0, 1]);

  const toggleFaq = (index) => {
    if (openIndexes.includes(index)) {
      setOpenIndexes(openIndexes.filter(i => i !== index));
    } else {
      setOpenIndexes([...openIndexes, index]);
    }
  };

  return (
    <div className="faq-page-view">
      <div className="page-hero-banner">
        <div className="section-container text-center">
          <span className="section-tag">KNOWLEDGE BASE</span>
          <h1 className="page-hero-title">Frequently Asked Questions</h1>
          <p className="page-hero-sub">
            Clear answers about the Sangram AI arena, consensus synthesis, cognitive archetypes, and supported model profiles.
          </p>
        </div>
      </div>

      <div className="section-container py-12 max-w-3xl mx-auto">
        <div className="faq-accordion-list">
          {faqs.map((faq, index) => {
            const isOpen = openIndexes.includes(index);
            return (
              <div key={index} className={`faq-item ${isOpen ? 'open' : ''}`}>
                <button
                  type="button"
                  className="faq-question-btn"
                  onClick={() => toggleFaq(index)}
                  aria-expanded={isOpen}
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

        <div className="faq-support-box mt-12 text-center">
          <h4>Have a question not addressed here?</h4>
          <p>Our engineering support team is happy to assist.</p>
          <div className="mt-4">
            <Link to="/contact">
              <Button variant="outline">Contact Support →</Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
