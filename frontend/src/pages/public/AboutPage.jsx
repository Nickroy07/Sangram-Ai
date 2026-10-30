import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../../components/common/Button';

export const AboutPage = () => {
  return (
    <div className="about-page-view">
      <div className="page-hero-banner">
        <div className="section-container text-center">
          <span className="section-tag">OUR MISSION & PHILOSOPHY</span>
          <h1 className="page-hero-title">About Sangram AI</h1>
          <p className="page-hero-sub">
            Sangram AI explores a new way to work with AI by bringing multiple perspectives into one arena.
          </p>
        </div>
      </div>

      <div className="section-container py-12">
        <div className="about-essay-container">
          <div className="essay-card">
            <h2 className="essay-title">The Problem: The Solitary Chatbot Illusion</h2>
            <p className="essay-paragraph">
              Every major AI frontier model is trained with distinct alignment techniques, safety thresholds, and implicit epistemic biases. When an engineer or decision-maker prompts a single model, they receive a polished, convincing answer. But conviction does not equal truth.
            </p>
            <p className="essay-paragraph">
              Without adversarial pressure, a single model’s blind spots remain undetected. You don’t know what counter-evidence Claude would present against GPT’s architectural recommendation, or how Gemini’s long-context retrieval would challenge Llama’s systems assumptions.
            </p>
          </div>

          <div className="essay-card">
            <h2 className="essay-title">The Solution: Adversarial Dialectic</h2>
            <p className="essay-paragraph">
              In classical philosophy, dialectic is discourse between two people holding different points of view about a subject who wish to establish the truth through reasoned argumentation. Sangram AI transplants this ancient methodology directly into AI engineering.
            </p>
            <p className="essay-paragraph">
              Instead of reading answers in isolation, Sangram AI places models into an adversarial chamber where they must defend their theses, cross-examine competing claims, and arrive at a weighted consensus.
            </p>
          </div>

          <div className="essay-card">
            <h2 className="essay-title">A workspace for stronger decisions</h2>
            <p className="essay-paragraph">
              Sangram AI brings multiple AI models into a shared debate. Each model makes a case, challenges the other, and contributes to a final recommendation you can review and save.
            </p>
            <p className="essay-paragraph">
              In future phases, live API provider endpoints, private enterprise LLM fine-tunes, and persistent cloud vector vaults will be integrated seamlessly behind our established service contracts.
            </p>
          </div>

          <div className="essay-action-card text-center mt-8">
            <h3 className="essay-action-heading">Join the Dialectic Exploration</h3>
            <p className="essay-action-sub">Experience how different minds produce stronger answers.</p>
            <div className="mt-4 flex justify-center gap-4">
              <Link to="/app/arena/new">
                <Button variant="primary" size="lg" icon="⚔">
                  Enter the Arena
                </Button>
              </Link>
              <Link to="/home">
                <Button variant="outline" size="lg">
                  Explore Home
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

