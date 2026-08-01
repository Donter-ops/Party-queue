# Contributing to PartyQueue

Thanks for your interest!

## Getting Started

Clone the repository

Backend

- install requirements
- create backend/.env
- run FastAPI

Frontend

- npm install
- npm run dev

## Pull Requests

- create a feature branch
- keep PRs focused
- explain what changed

## Code Style

- Python: type hints
- TypeScript: strict mode
- keep architecture modular

## Providers

When adding a new music provider:

- don't modify PlaybackEngine
- don't modify PlaybackStrategy
- use ProviderResolver
- keep provider specific logic isolated
