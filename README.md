# PartyQueue

PartyQueue is a free, open-source shared music queue for groups. It accepts songs from multiple input sources and plays them through a provider-independent playback layer.

## Supported today

**Input**

- Spotify links
- YouTube links
- YouTube Music links
- Text search (MusicBrainz-backed)

**Playback**

- YouTube / YouTube Music

**Cross-provider**

- Spotify input can be resolved and played back via YouTube / YouTube Music.

## Planned providers

These are not implemented yet:

- Apple Music
- Deezer
- Amazon Music

## Requirements

- Python 3.11+
- Node.js 20+
- Spotify Developer app credentials
- Optional: YouTube Data API key for richer search

## Environment configuration

Copy `.env.example` to `.env` in the repository root and configure:

- `SPOTIFY_CLIENT_ID` – required
- `SPOTIFY_CLIENT_SECRET` – required
- `SPOTIFY_REDIRECT_URI` – Spotify OAuth callback (default: `http://127.0.0.1:8000/auth/spotify/callback`)
- `FRONTEND_SPOTIFY_REDIRECT_URI` – frontend redirect after OAuth (default: `http://127.0.0.1:5173/connect-spotify`)
- `YOUTUBE_API_KEY` – optional; improves YouTube search
- `PARTYQUEUE_ENV` – set to `production` to hide development debug endpoints

## Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
uvicorn main:app --reload
```

API: `http://127.0.0.1:8000`

## Frontend

```bash
cd frontend
npm install
npm run dev
```

App: `http://127.0.0.1:5173`

## Architecture

```
User input (link or search)
  -> Input Resolver
  -> Orchestrator Agent
  -> Canonical Song
  -> Playback Strategy / Resolver
  -> Playback Engine
  -> YouTube / YouTube Music player
```

Rooms, queue management, and playback controls are exposed through a FastAPI backend. The React frontend renders the shared queue and web player.

Spotify OAuth is used for optional host-side Spotify playback. Cross-provider resolution allows Spotify links to be matched and played on YouTube when Spotify catalog access is unavailable.

## License

MIT License
