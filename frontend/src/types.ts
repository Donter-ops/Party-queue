export interface Song {
  id: string;
  title: string;
  artist: string;
  added_by: string;
  source: string;
  external_url?: string | null;
  position: number;
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
  state: "IDLE" | "PLAYING" | "PAUSED" | "FINISHED" | "SKIPPED";
  started_at: string | null;
  updated_at: string;
}

export interface CreateSongPayload {
  title: string;
  artist: string;
  added_by: string;
  source: string;
  external_url?: string | null;
}
