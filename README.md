# 🎵 PartyQueue

> AI-first cross-platform music queue.

PartyQueue allows groups of friends to build a shared music queue, regardless of which music service they use.

Instead of forcing everyone onto the same streaming platform, PartyQueue uses an intelligent orchestration layer that resolves songs across multiple providers and plays them on the host's preferred music service.

---

## ✨ Vision

Today's music streaming services are isolated ecosystems.

If one friend uses Spotify and another uses YouTube Music, listening together becomes unnecessarily difficult.

PartyQueue solves this by introducing an AI-powered orchestration layer that understands songs independently from streaming providers.

The goal is simple:

- One shared queue
- Multiple music services
- One seamless listening experience

---

## 🚀 Current Features

### Rooms

- Create party rooms
- Join rooms via share link
- Shared queue
- Reordering
- Remove songs

### Search

- MusicBrainz integration
- Universal search
- Spotify link support
- YouTube link support

### AI Architecture

- Orchestrator Agent
- Decision Engine
- Cognitive Pipeline
- Canonical Song model
- Playback Strategy
- Playback Resolver
- Provider Resolver

### Playback

- Provider-independent playback architecture
- Spotify OAuth
- Spotify session management
- Playback Engine
- Provider matching

---

## 🏗 Architecture

```
User

↓

Universal Input

↓

Input Resolver

↓

Orchestrator Agent

↓

Decision Engine

↓

Canonical Song

↓

Playback Strategy

↓

Playback Resolver

↓

Provider Resolver

↓

Playback Engine

↓

Streaming Provider
```

---

## 🤖 AI-First Design

Unlike traditional music queue applications, PartyQueue is built around an intelligent orchestration layer.

The AI Agent is responsible for:

- understanding incoming music links
- resolving metadata
- matching songs across providers
- selecting the best playback provider
- preparing future cross-platform playback

This allows PartyQueue to remain provider-independent.

---

## 🛠 Tech Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- MusicBrainz API

### Frontend

- React
- TypeScript
- Tailwind CSS
- Vite

### AI Architecture

- Agent-based orchestration
- Decision Engine
- Cognitive Pipeline
- Provider abstraction

---

## 🔐 Spotify Integration

Implemented:

- Spotify OAuth
- Access Token Management
- Refresh Tokens
- Playback API integration
- Device discovery
- Debug endpoints

Note:

Spotify playback requires a Spotify Premium account due to Spotify Web API restrictions.

---

## 🎯 Roadmap

### ✅ Completed

- Shared Rooms
- Queue Management
- Universal Search
- MusicBrainz Integration
- AI Agent
- Decision Engine
- Playback Architecture
- Spotify OAuth

### 🚧 In Progress

- YouTube Playback
- Automatic Queue Playback
- Canonical Song Cache
- Multi-provider Resolution

### 🔮 Planned

- Apple Music
- Deezer
- SoundCloud
- Smart AI Matching
- Multi-Agent Collaboration
- Learning Resolver
- Mobile Application

---

## 📖 Philosophy

PartyQueue is intentionally built around simplicity.

Users should not have to think about streaming providers.

They simply add songs.

The orchestration layer handles the rest.

---

## 📜 License

MIT License

---

## ❤️ Project Status

Current Version:

**v0.1.0-alpha**

PartyQueue is under active development.
