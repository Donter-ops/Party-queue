# 🎵 PartyQueue

> **One Queue. Every Music Service.**

PartyQueue is a free and open-source cross-provider music queue that allows people using different music services to enjoy a shared listening experience.

Instead of forcing everyone onto the same streaming platform, PartyQueue resolves songs across providers so guests can contribute regardless of where the music comes from.

---

# ✨ Features

## Currently supported

- ✅ Spotify links
- ✅ YouTube links
- ✅ YouTube Music links
- ✅ Text search
- ✅ Shared music queue
- ✅ Cross-provider song resolution
- ✅ YouTube / YouTube Music playback
- ✅ Open Source

---

# 🚧 Coming Soon

- Apple Music support
- Deezer support
- Amazon Music support
- Improved matching engine
- Better UI / UX
- Mobile App
- Public deployment

See **ROADMAP.md** for the complete roadmap.

---

# 💡 Why PartyQueue?

Most existing group music applications only work if everyone uses the same streaming service.

PartyQueue removes this limitation.

Guests can add songs from Spotify while the host plays them through YouTube Music.

In the future, additional providers such as Apple Music, Deezer and Amazon Music will seamlessly integrate into the same queue.

---

# 🏗️ Architecture

```
                Spotify
               YouTube
           YouTube Music
             Apple Music
                Deezer
            Amazon Music
                   │
                   ▼
           Input Resolver
                   │
                   ▼
            Canonical Song
                   │
                   ▼
          Playback Resolver
                   │
                   ▼
          Host Music Provider
```

The application internally converts every song into a provider-independent representation before resolving it to the host's preferred music service.

This architecture makes PartyQueue scalable and allows new providers to be added without changing the overall playback system.

---

# 🛠️ Tech Stack

## Backend

- Python
- FastAPI
- SQLAlchemy

## Frontend

- React
- TypeScript
- Vite

## Music Providers

- Spotify Web API
- YouTube
- YouTube Music

---

# 🚀 Getting Started

## Clone the repository

```bash
git clone https://github.com/<YOUR_USERNAME>/PartyQueue.git

cd PartyQueue
```

---

## Backend

```bash
cd backend

pip install -r requirements.txt
```

Copy

```
.env.example
```

to

```
backend/.env
```

and fill in your Spotify credentials.

Start the backend

```bash
uvicorn main:app --reload
```

---

## Frontend

```bash
cd frontend

npm install

npm run dev
```

---

# ⚙️ Environment Variables

PartyQueue uses a local `.env` file for provider credentials.

An example configuration is included in:

```
.env.example
```

Never commit your own `.env` file.

---

# 🤝 Contributing

Contributions are welcome!

If you would like to improve PartyQueue, please read

```
CONTRIBUTING.md
```

before opening a Pull Request.

Whether it's fixing bugs, improving the UI, adding documentation or implementing a new music provider — every contribution is appreciated.

---

# 🗺️ Roadmap

The roadmap is maintained separately in

```
ROADMAP.md
```

---

# 📄 License

This project is licensed under the MIT License.

See the **LICENSE** file for details.

## License

MIT License
