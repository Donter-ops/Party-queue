# PartyQueue Architecture

## Vision

PartyQueue follows an AI-first architecture.

Business logic is separated from provider implementations.

Reasoning is separated from execution.

---

# Layers

Frontend

↓

API

↓

Services

↓

Orchestrator Agent

↓

Tools

↓

Providers

↓

External APIs

---

# Principles

The frontend never knows providers.

The API never knows providers.

Services never know providers.

Only Tools communicate with Providers.

Only the Agent decides which Tool should be executed.

---

# Design Goals

- Provider independent
- AI ready
- Easily testable
- Modular
- Replaceable components
- Multi-agent ready

---

# Future Architecture

Frontend

↓

API

↓

Services

↓

Orchestrator Agent

↓

Resolver Agent

↓

Recommendation Agent

↓

Playback Agent

↓

Tools

↓

Providers