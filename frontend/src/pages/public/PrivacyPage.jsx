import React from 'react'

export const PrivacyPage = () => <main className="section-container legal-page py-12"><h1 className="page-title">Privacy</h1><p className="page-sub">How Sangram AI handles information when you use the service.</p>
  <section className="mt-6"><h2>Account and service data</h2><p>Account details, preferences, battle prompts, and generated battle records are sent to and stored by the Sangram AI backend to provide the service. Your browser uses an authentication cookie to make signed-in requests.</p></section>
  <section className="mt-6"><h2>AI providers</h2><p>When you start a battle, the prompt and relevant debate context are sent from the backend to the configured AI providers selected for that battle. Provider credentials are held by the backend and are not sent to your browser.</p></section>
  <section className="mt-6"><h2>Payments and email</h2><p>Payment processing is not currently enabled. Email verification and password recovery depend on the backend email configuration.</p></section>
  <section className="mt-6"><h2>Questions</h2><p>Contact the Sangram AI team for questions about your account or data.</p></section>
</main>
