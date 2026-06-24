# PartyQueue

PartyQueue ist ein kleines Hobbyprojekt, um gemeinsam eine Musik-Queue zu erstellen.

## Features

- Räume erstellen
- Songs hinzufügen
- Gemeinsame Queue
- Echtzeitupdates (geplant)
- Spotify Integration (geplant)
- YouTube Integration (geplant)

## Backend

```bash
cd backend

python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt

uvicorn main:app --reload
