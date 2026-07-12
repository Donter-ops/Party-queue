# PartyQueue Tool Specification

## Philosophy

Tools are the only way an agent interacts with the outside world.

Agents never communicate directly with providers.

---

# QueueTool

Responsibilities

- read queue
- update queue
- reorder queue
- remove songs

---

# SearchTool

Responsibilities

- search songs
- search artists
- search albums

Future Providers

- Spotify
- YouTube
- Apple Music

---

# MetadataTool

Responsibilities

- fetch metadata
- normalize metadata
- compare metadata

---

# PlaybackTool

Responsibilities

Future implementation

- play
- pause
- next
- previous

---

# UserTool

Responsibilities

Future implementation

- read user profile
- read subscriptions
- read provider preferences

---

# LoggingTool

Responsibilities

Future implementation

- store agent decisions
- reasoning history
- confidence scores