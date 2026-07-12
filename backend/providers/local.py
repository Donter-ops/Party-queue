from __future__ import annotations

from providers.base import MusicProvider, ProviderSong


class LocalSearchProvider(MusicProvider):
    """Deterministic in-memory provider used for local catalog search.

    This provider exists purely to activate the first real search workflow in
    the architecture. It does not represent a streaming provider and is safe to
    use as a provider-agnostic catalog until external integrations are added.
    """

    def __init__(self) -> None:
        self.catalog = [
            ProviderSong("local", "1", "Bohemian Rhapsody", "Queen"),
            ProviderSong("local", "2", "Africa", "Toto"),
            ProviderSong("local", "3", "Blinding Lights", "The Weeknd"),
            ProviderSong("local", "4", "Numb", "Linkin Park"),
            ProviderSong("local", "5", "Billie Jean", "Michael Jackson"),
            ProviderSong("local", "6", "Dancing Queen", "ABBA"),
            ProviderSong("local", "7", "Mr. Brightside", "The Killers"),
            ProviderSong("local", "8", "Viva La Vida", "Coldplay"),
            ProviderSong("local", "9", "Rolling in the Deep", "Adele"),
            ProviderSong("local", "10", "Smells Like Teen Spirit", "Nirvana"),
            ProviderSong("local", "11", "Wonderwall", "Oasis"),
            ProviderSong("local", "12", "Bad Guy", "Billie Eilish"),
            ProviderSong("local", "13", "Lose Yourself", "Eminem"),
            ProviderSong("local", "14", "Take On Me", "a-ha"),
            ProviderSong("local", "15", "Levitating", "Dua Lipa"),
            ProviderSong("local", "16", "Shape of You", "Ed Sheeran"),
            ProviderSong("local", "17", "Uptown Funk", "Mark Ronson"),
            ProviderSong("local", "18", "Hotel California", "Eagles"),
        ]

    def search(self, query: str) -> list[ProviderSong]:
        """Return local catalog matches sorted by simple token overlap."""
        normalized_query = query.lower().strip()
        query_tokens = [token for token in normalized_query.split() if token]
        if not query_tokens:
            return []

        scored_matches: list[tuple[int, ProviderSong]] = []
        for song in self.catalog:
            haystack = f"{song.title} {song.artist}".lower()
            score = sum(1 for token in query_tokens if token in haystack)
            if score > 0:
                scored_matches.append((score, song))

        scored_matches.sort(
            key=lambda item: (
                -item[0],
                item[1].artist.lower(),
                item[1].title.lower(),
            )
        )
        return [song for _, song in scored_matches]

    def resolve(self, url: str) -> ProviderSong:
        raise NotImplementedError("Local search provider does not resolve URLs.")

    def get_song(self, provider_id: str) -> ProviderSong:
        raise NotImplementedError("Local search provider does not fetch by provider ID.")
