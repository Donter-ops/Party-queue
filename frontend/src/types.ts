export interface Song {
  id: string;
  title: string;
  artist: string;
  added_by: string;
  source: string;
  external_url?: string | null;
  position: number;
  resolution_confidence?: number | null;
  resolution_reason?: string | null;
}

export interface Room {
  id: string;
  name: string;
}

export interface RoomDetail extends Room {
  songs: Song[];
}

export interface PlaybackProviderMatch {
  provider: string | null;
  provider_track_id: string | null;
  confidence: number;
  fallback_provider?: string | null;
  resolved_title?: string | null;
  resolved_artist?: string | null;
}

export interface PlaybackSession {
  room_id: string;
  current_song: Song | null;
  next_song: Song | null;
  provider_match: PlaybackProviderMatch | null;
  youtube_video_id?: string | null;
  queue_position: number | null;
  previous_available: boolean;
  queue_length: number;
  current_provider?: string | null;
  playable_provider?: string | null;
  current_song_id?: string | null;
  resolver_cache_hit: boolean;
  state: "IDLE" | "PLAYING" | "PAUSED" | "FINISHED" | "SKIPPED";
  started_at: string | null;
  updated_at: string;
}

export interface ResolverScoreContribution {
  label: string;
  value: number;
  kind: string;
  detail: string;
}

export interface ResolverSpotifyMetadata {
  track_id: string | null;
  track_name: string;
  artists: string[];
  album: string | null;
  duration_ms: number | null;
  isrc: string | null;
}

export interface ResolverCandidateTrace {
  rank: number;
  video_id: string;
  video_title: string;
  channel: string | null;
  duration_seconds: number | null;
  score: number;
  confidence: number;
  contributions: ResolverScoreContribution[];
  reasons: string[];
  lost_reason: string | null;
}

export interface ResolverWinnerTrace {
  video_id: string | null;
  video_title: string | null;
  confidence: number;
  reason: string;
}

export interface ResolverDebugTrace {
  created_at: string;
  room_id?: string | null;
  source_provider: string;
  target_provider: string;
  cache_hit: boolean;
  spotify: ResolverSpotifyMetadata | null;
  search_query: string | null;
  candidates: ResolverCandidateTrace[];
  winner: ResolverWinnerTrace;
  confidence: number;
  reason: string;
}

export interface CreateSongPayload {
  title: string;
  artist: string;
  added_by: string;
  source: string;
  external_url?: string | null;
}
