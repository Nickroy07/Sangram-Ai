/** Public product information shared by the FAQ and pricing pages. */
export const faqs = [
  {
    q: 'How does Sangram AI differ from asking two chatbots separately?',
    a: 'Sangram AI runs a shared, multi-round exchange: each model can read and respond to the other model’s arguments, then a selected model writes a synthesis.'
  },
  {
    q: 'Which AI models are available in the Arena?',
    a: 'The catalog includes OpenAI, Google, Anthropic, Groq, Mistral, and xAI model profiles. A profile can be selected only when its provider key is configured on the Sangram AI backend.'
  },
  {
    q: 'What is a cognitive archetype?',
    a: 'An archetype gives a model a specific reasoning perspective, such as analytical, skeptical, or pragmatic, for its arguments in a battle.'
  },
  {
    q: 'Does Sangram AI calculate a consensus score?',
    a: 'The current backend generates a written synthesis but does not calculate a numeric agreement score. The interface does not invent one.'
  },
  {
    q: 'Can I share or export a battle?',
    a: 'Completed battles are saved to your account history. Public share links and downloadable exports are not available yet.'
  },
  {
    q: 'How are AI providers connected?',
    a: 'Provider credentials are stored on the backend. They are never sent to your browser, and a model is unavailable until its provider is configured.'
  }
];
