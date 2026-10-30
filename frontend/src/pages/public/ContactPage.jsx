import React, { useState } from 'react';
import { useToast } from '../../context/ToastContext';
import { Button } from '../../components/common/Button';
import { Input, Textarea } from '../../components/common/Input';
import { supportApi } from '../../services/api';

export const ContactPage = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [subject, setSubject] = useState('General Inquiry');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const { showToast } = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !email.trim() || !message.trim()) {
      showToast('Please fill out all required contact fields.', 'warn');
      return;
    }

    setLoading(true);
    try {
      await supportApi.contact({
        name: name.trim(),
        email: email.trim(),
        subject,
        message: message.trim()
      });
      setSubmitted(true);
      showToast('Message sent! Our engineering team will reply shortly.', 'success');
    } catch (err) {
      showToast(err.message || 'Failed to send message. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="contact-page-view">
      <div className="page-hero-banner">
        <div className="section-container text-center">
          <span className="section-tag">GET IN TOUCH</span>
          <h1 className="page-hero-title">Contact Sangram AI</h1>
          <p className="page-hero-sub">
            Whether you want enterprise team deployment, custom cognitive personas, or feedback, we are here.
          </p>
        </div>
      </div>

      <div className="section-container py-12 max-w-4xl mx-auto">
        <div className="contact-grid">
          {/* Left Column: Direct info */}
          <div className="contact-info-panel">
            <h3 className="info-panel-title">Direct Inquiries</h3>
            <p className="info-panel-desc">
              Reach out directly for enterprise war-room chambers, custom LLM fine-tunes, or technical partnerships.
            </p>

            <div className="info-contact-points">
              <div className="point-item">
                <span className="point-icon">✉</span>
                <div>
                  <span className="point-label">Email Support</span>
                  <span className="point-value">team@sangram.ai</span>
                </div>
              </div>

              <div className="point-item">
                <span className="point-icon">🏢</span>
                <div>
                  <span className="point-label">Office</span>
                  <span className="point-value">Bangalore / San Francisco</span>
                </div>
              </div>

              <div className="point-item">
                <span className="point-icon">⚡</span>
                <div>
                  <span className="point-label">Response Time</span>
                  <span className="point-value">Typically within 24 business hours</span>
                </div>
              </div>
            </div>

            <div className="repo-reference-box">
              <span className="repo-ref-title">Open Development:</span>
              <a
                href="https://github.com/Nickroy07/Sangram-Ai.git"
                target="_blank"
                rel="noreferrer"
                className="repo-ref-link"
              >
                github.com/Nickroy07/Sangram-Ai ↗
              </a>
            </div>
          </div>

          {/* Right Column: Interactive Form */}
          <div className="contact-form-panel">
            {submitted ? (
              <div className="contact-success-state animate-fade-in text-center py-8">
                <div className="success-icon-badge">✓</div>
                <h3>Message Received</h3>
                <p className="mt-2 text-muted">
                  Thank you, <strong>{name}</strong>. We received your note regarding <em>"{subject}"</em> and will reply to <strong>{email}</strong> shortly.
                </p>
                <Button
                  variant="outline"
                  className="mt-6"
                  onClick={() => {
                    setSubmitted(false);
                    setMessage('');
                  }}
                >
                  Send another message
                </Button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="contact-form" noValidate>
                <Input
                  label="Your Name"
                  type="text"
                  placeholder="Alex Vance"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />

                <Input
                  label="Work Email"
                  type="email"
                  placeholder="alex@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />

                <div className="form-field">
                  <label className="form-label">Subject</label>
                  <select
                    className="input-control"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                  >
                    <option value="General Inquiry">General Inquiry</option>
                    <option value="Enterprise War Room">Enterprise War Room Chamber</option>
                    <option value="Custom Model Integration">Custom Model Fine-Tune</option>
                    <option value="Bug / Feedback">Frontend Feedback</option>
                  </select>
                </div>

                <Textarea
                  label="Message"
                  rows={5}
                  placeholder="Describe your question or use case..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  required
                />

                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  className="w-full mt-4"
                  loading={loading}
                >
                  Send Message
                </Button>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
