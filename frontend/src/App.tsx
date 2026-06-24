import { useEffect, useState } from "react";
import axios from "axios";

import { CreateRoom } from "./components/CreateRoom";
import { RoomView } from "./components/RoomView";

export interface Song {
  id: string;
  title: string;
  artist: string;
  added_by: string;
  source: string;
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
}

const api = axios.create({
  baseURL: "http://localhost:8000",
});

export function App(): JSX.Element {
  const [room, setRoom] = useState<RoomDetail | null>(null);
  const [isCreatingRoom, setIsCreatingRoom] = useState(false);
  const [isRefreshingRoom, setIsRefreshingRoom] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    setErrorMessage(null);
  }, [room]);

  async function handleCreateRoom(): Promise<void> {
    try {
      setIsCreatingRoom(true);
      setErrorMessage(null);

      const createResponse = await api.post<Room>("/rooms", {
        name: "My Party",
      });

      const roomResponse = await api.get<RoomDetail>(`/rooms/${createResponse.data.id}`);
      setRoom(roomResponse.data);
    } catch (error) {
      setErrorMessage("Room konnte nicht erstellt werden. Prüfe, ob das Backend läuft.");
    } finally {
      setIsCreatingRoom(false);
    }
  }

  async function refreshRoom(roomId: string): Promise<void> {
    try {
      setIsRefreshingRoom(true);
      const response = await api.get<RoomDetail>(`/rooms/${roomId}`);
      setRoom(response.data);
      setErrorMessage(null);
    } catch (error) {
      setErrorMessage("Room konnte nicht geladen werden.");
    } finally {
      setIsRefreshingRoom(false);
    }
  }

  async function handleAddSong(payload: CreateSongPayload): Promise<void> {
    if (!room) {
      return;
    }

    try {
      setErrorMessage(null);
      await api.post(`/rooms/${room.id}/songs`, payload);
      await refreshRoom(room.id);
    } catch (error) {
      setErrorMessage("Song konnte nicht hinzugefügt werden.");
    }
  }

  return (
    <main className="min-h-screen px-4 py-8 text-vinyl sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-5xl items-center justify-center">
        {room ? (
          <RoomView
            isRefreshing={isRefreshingRoom}
            room={room}
            onAddSong={handleAddSong}
          />
        ) : (
          <CreateRoom
            errorMessage={errorMessage}
            isLoading={isCreatingRoom}
            onCreateRoom={handleCreateRoom}
          />
        )}
      </div>

      {room && errorMessage ? (
        <div className="fixed bottom-4 left-1/2 w-[min(92vw,32rem)] -translate-x-1/2 rounded-2xl bg-vinyl px-5 py-4 text-sm font-medium text-white shadow-party">
          {errorMessage}
        </div>
      ) : null}
    </main>
  );
}
