import { useEffect, useMemo, useState } from "react";
import type { JSX } from "react";
import axios from "axios";

import { CreateRoom } from "./components/CreateRoom";
import { RoomView } from "./components/RoomView";

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

const apiBaseUrl = `${window.location.protocol}//${window.location.hostname}:8000`;

const api = axios.create({
  baseURL: apiBaseUrl,
});

function getInitialRoomId(): string | null {
  const roomId = new URLSearchParams(window.location.search).get("room");
  return roomId && roomId.trim() ? roomId.trim() : null;
}

export function App(): JSX.Element {
  const [room, setRoom] = useState<RoomDetail | null>(null);
  const [isCreatingRoom, setIsCreatingRoom] = useState(false);
  const [isRefreshingRoom, setIsRefreshingRoom] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [savedGuestName, setSavedGuestName] = useState("");
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);

  useEffect(() => {
    const storedGuestName = window.localStorage.getItem("partyqueue:guest-name");
    if (storedGuestName) {
      setSavedGuestName(storedGuestName);
    }
  }, []);

  useEffect(() => {
    const roomId = getInitialRoomId();
    if (!roomId) {
      return;
    }

    void refreshRoom(roomId);
  }, []);

  useEffect(() => {
    setErrorMessage(null);
  }, [room]);

  useEffect(() => {
    if (!room || !autoRefreshEnabled) {
      return;
    }

    const intervalId = window.setInterval(() => {
      void refreshRoom(room.id, { silent: true });
    }, 15000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [autoRefreshEnabled, room]);

  useEffect(() => {
    if (!room) {
      window.history.replaceState({}, "", window.location.pathname);
      return;
    }

    const nextUrl = `${window.location.pathname}?room=${room.id}`;
    window.history.replaceState({}, "", nextUrl);
  }, [room]);

  const roomShareUrl = useMemo(() => {
    if (!room) {
      return "";
    }

    return `${window.location.origin}${window.location.pathname}?room=${room.id}`;
  }, [room]);

  async function handleCreateRoom(roomName: string): Promise<void> {
    try {
      setIsCreatingRoom(true);
      setErrorMessage(null);

      const createResponse = await api.post<Room>("/rooms", {
        name: roomName,
      });

      const roomResponse = await api.get<RoomDetail>(`/rooms/${createResponse.data.id}`);
      setRoom(roomResponse.data);
    } catch (error) {
      setErrorMessage("Raum konnte nicht erstellt werden. Prüfe, ob das Backend läuft.");
    } finally {
      setIsCreatingRoom(false);
    }
  }

  async function refreshRoom(
    roomId: string,
    options?: { silent?: boolean },
  ): Promise<void> {
    try {
      if (!options?.silent) {
        setIsRefreshingRoom(true);
      }

      const response = await api.get<RoomDetail>(`/rooms/${roomId}`);
      setRoom(response.data);
      setErrorMessage(null);
    } catch (error) {
      setErrorMessage("Raum konnte nicht geladen werden.");
    } finally {
      if (!options?.silent) {
        setIsRefreshingRoom(false);
      }
    }
  }

  async function handleJoinRoom(roomId: string): Promise<void> {
    try {
      setIsCreatingRoom(true);
      setErrorMessage(null);
      await refreshRoom(roomId);
    } finally {
      setIsCreatingRoom(false);
    }
  }

  async function handleAddSong(payload: CreateSongPayload): Promise<void> {
    if (!room) {
      return;
    }

    try {
      setErrorMessage(null);
      if (payload.added_by) {
        window.localStorage.setItem("partyqueue:guest-name", payload.added_by);
        setSavedGuestName(payload.added_by);
      }

      await api.post(`/rooms/${room.id}/songs`, payload);
      await refreshRoom(room.id);
    } catch (error) {
      setErrorMessage("Song konnte nicht hinzugefügt werden.");
    }
  }

  async function handleMoveSong(songId: string, nextPosition: number): Promise<void> {
    if (!room) {
      return;
    }

    try {
      setErrorMessage(null);
      await api.put(`/rooms/${room.id}/songs/${songId}/move`, {
        new_position: nextPosition,
      });
      await refreshRoom(room.id);
    } catch (error) {
      setErrorMessage("Song konnte nicht verschoben werden.");
    }
  }

  async function handleDeleteSong(songId: string): Promise<void> {
    if (!room) {
      return;
    }

    try {
      setErrorMessage(null);
      await api.delete(`/rooms/${room.id}/songs/${songId}`);
      await refreshRoom(room.id);
    } catch (error) {
      setErrorMessage("Song konnte nicht entfernt werden.");
    }
  }

  async function handleCopyShareLink(): Promise<void> {
    if (!roomShareUrl) {
      return;
    }

    try {
      await navigator.clipboard.writeText(roomShareUrl);
      setErrorMessage("Share-Link wurde in die Zwischenablage kopiert.");
    } catch (error) {
      setErrorMessage("Share-Link konnte nicht kopiert werden.");
    }
  }

  function handleLeaveRoom(): void {
    setRoom(null);
    setErrorMessage(null);
  }

  return (
    <main className="min-h-screen px-4 py-6 text-vinyl sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-7xl items-center justify-center">
        {room ? (
          <RoomView
            autoRefreshEnabled={autoRefreshEnabled}
            errorMessage={errorMessage}
            isRefreshing={isRefreshingRoom}
            room={room}
            roomShareUrl={roomShareUrl}
            savedGuestName={savedGuestName}
            onAddSong={handleAddSong}
            onCopyShareLink={handleCopyShareLink}
            onDeleteSong={handleDeleteSong}
            onLeaveRoom={handleLeaveRoom}
            onMoveSong={handleMoveSong}
            onRefreshRoom={() => refreshRoom(room.id)}
            onToggleAutoRefresh={() => {
              setAutoRefreshEnabled((currentValue) => !currentValue);
            }}
          />
        ) : (
          <CreateRoom
            errorMessage={errorMessage}
            isLoading={isCreatingRoom}
            onCreateRoom={handleCreateRoom}
            onJoinRoom={handleJoinRoom}
          />
        )}
      </div>
    </main>
  );
}
