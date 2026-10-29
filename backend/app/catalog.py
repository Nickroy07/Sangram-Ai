"""Static catalog of combatant AI models and cognitive archetypes.

Single source of truth shared by the public catalog routes (app/api/v1/models.py),
the AI gateway (availability + provider mapping) and the battle engine
(archetype personas). Mirrors frontend/src/data/models.js and archetypes.js.
"""

from typing import List

from app.schemas.model import ArchetypeProfile, ModelAccent, ModelProfile

MODELS_CATALOG: List[ModelProfile] = [
    ModelProfile(
        id="chatgpt",
        name="ChatGPT",
        provider="OpenAI",
        modelLabel="GPT-5",
        apiModel=None,
        desc="Structured, first-principles reasoning with broad general-knowledge fluency.",
        accent=ModelAccent(
            color="#35D6A4",
            soft="rgba(53, 214, 164, 0.12)",
            line="rgba(53, 214, 164, 0.45)",
        ),
        is_available=True,
    ),
    ModelProfile(
        id="gemini",
        name="Gemini",
        provider="Google",
        modelLabel="Gemini 2.5 Pro",
        apiModel=None,
        desc="Long-context, multimodal architecture tuned for synthesis across sources.",
        accent=ModelAccent(
            color="#5B9DFF",
            soft="rgba(91, 157, 255, 0.12)",
            line="rgba(91, 157, 255, 0.45)",
        ),
        is_available=True,
    ),
    ModelProfile(
        id="claude",
        name="Claude",
        provider="Anthropic",
        modelLabel="Claude Sonnet 4.5",
        apiModel=None,
        desc="Methodical, nuance-aware critique with careful epistemic hedging.",
        accent=ModelAccent(
            color="#E9A05E",
            soft="rgba(233, 160, 94, 0.12)",
            line="rgba(233, 160, 94, 0.45)",
        ),
        is_available=True,
    ),
    ModelProfile(
        id="llama",
        name="Llama",
        provider="Meta",
        modelLabel="Llama 4",
        apiModel=None,
        desc="Open-weights flagship profile built for rigorous systems-level argumentation.",
        accent=ModelAccent(
            color="#9B9CFF",
            soft="rgba(155, 156, 255, 0.13)",
            line="rgba(155, 156, 255, 0.45)",
        ),
        is_available=True,
    ),
    ModelProfile(
        id="mistral",
        name="Mistral",
        provider="Mistral AI",
        modelLabel="Mistral Large 2",
        apiModel=None,
        desc="High-efficiency profile with concise, code-forward, minimal-waste argumentation.",
        accent=ModelAccent(
            color="#E4719B",
            soft="rgba(228, 113, 155, 0.12)",
            line="rgba(228, 113, 155, 0.45)",
        ),
        is_available=True,
    ),
    ModelProfile(
        id="grok",
        name="Grok",
        provider="xAI",
        modelLabel="Grok 4",
        apiModel=None,
        desc="Contrarian challenger profile that stress-tests conventional assumptions.",
        accent=ModelAccent(
            color="#B9C6DA",
            soft="rgba(185, 198, 218, 0.12)",
            line="rgba(185, 198, 218, 0.4)",
        ),
        is_available=True,
    ),
]

ARCHETYPES_CATALOG: List[ArchetypeProfile] = [
    ArchetypeProfile(
        id="logician",
        name="Analytical Logician",
        shortName="Logician",
        tag="Formal & Deductive",
        motto="Truth through systematic deduction and formal validity.",
        description="Grounds every argument in axiomatic first principles. Deconstructs claims into premise, inference, and conclusion, systematically exposing unstated assumptions and logical fallacies.",
        traits=["First-principles rigor", "Formal validity", "Fallacy deconstruction"],
        debateStyle="Axiomatic proofs, invariant checks, structural precision",
        accent=ModelAccent(
            color="#38BDF8",
            soft="rgba(56, 189, 248, 0.12)",
            line="rgba(56, 189, 248, 0.45)",
        ),
    ),
    ArchetypeProfile(
        id="visionary",
        name="Creative Visionary",
        shortName="Visionary",
        tag="Lateral & Expansive",
        motto="Break the problem space with lateral perspective.",
        description="Reframes orthodox constraints through paradigm-shifting foresight. Connects disparate domains through associative leaps, projecting second-order emergent possibilities that linear thinking overlooks.",
        traits=["Paradigm innovation", "Future extrapolation", "Associative leaps"],
        debateStyle="Lateral reframing, emergent synthesis, expansive horizons",
        accent=ModelAccent(
            color="#C084FC",
            soft="rgba(192, 132, 252, 0.12)",
            line="rgba(192, 132, 252, 0.45)",
        ),
    ),
    ArchetypeProfile(
        id="pragmatist",
        name="Pragmatic Realist",
        shortName="Pragmatist",
        tag="Ground Truth & Feasibility",
        motto="Execution viability dictates actual value.",
        description="Tests every high-minded proposal against operational physics, organizational friction, and economic constraints. Rejects elegant theories that fail at the point of contact with reality.",
        traits=["Friction audits", "Operational trade-offs", "Execution physics"],
        debateStyle="Empirical testing, failure-mode analysis, implementation audits",
        accent=ModelAccent(
            color="#34D399",
            soft="rgba(52, 211, 153, 0.12)",
            line="rgba(52, 211, 153, 0.45)",
        ),
    ),
    ArchetypeProfile(
        id="skeptic",
        name="Inquisitive Skeptic",
        shortName="Skeptic",
        tag="Falsification & Inquiry",
        motto="Stress-test every assumption until only the robust survives.",
        description="Applies Popperian falsification and boundary stress-testing. Probes edge cases, challenges survivorship bias, and questions whether apparent consensus is simply intellectual complacency.",
        traits=["Hypothesis falsification", "Edge-case interrogation", "Epistemic caution"],
        debateStyle="Socratic probing, edge-case pressure, counter-example discovery",
        accent=ModelAccent(
            color="#FBBF24",
            soft="rgba(251, 191, 36, 0.12)",
            line="rgba(251, 191, 36, 0.45)",
        ),
    ),
    ArchetypeProfile(
        id="synthesizer",
        name="Integrative Synthesizer",
        shortName="Synthesizer",
        tag="Dialectical Harmony",
        motto="Superior answers integrate opposing truths.",
        description="Identifies the kernel of validity in contradictory positions. Transcends false dichotomies by constructing higher-order frameworks that unite thesis and antithesis into actionable consensus.",
        traits=["Dialectical integration", "Systems thinking", "Bridge building"],
        debateStyle="Nuanced mediation, common-ground extraction, multi-dimensional framing",
        accent=ModelAccent(
            color="#22D3EE",
            soft="rgba(34, 211, 238, 0.12)",
            line="rgba(34, 211, 238, 0.45)",
        ),
    ),
    ArchetypeProfile(
        id="provocateur",
        name="Bold Provocateur",
        shortName="Provocateur",
        tag="Contrarian Dissent",
        motto="Consensus is comfort; friction generates breakthrough.",
        description="Disrupts cozy conventional wisdom with sharp, uncomfortable counter-theses. Forces opponents out of rote talking points by attacking the sacred cows that nobody else dares to question.",
        traits=["Status-quo challenge", "High-tension angles", "Productive disruption"],
        debateStyle="Contrarian shocks, taboo questioning, friction-driven breakthroughs",
        accent=ModelAccent(
            color="#FB7185",
            soft="rgba(251, 113, 133, 0.12)",
            line="rgba(251, 113, 133, 0.45)",
        ),
    ),
]
