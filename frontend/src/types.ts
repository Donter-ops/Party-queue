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

export interface CreateSongPayload {
  title: string;
  artist: string;
  added_by: string;
  source: string;
  external_url?: string | null;
}
