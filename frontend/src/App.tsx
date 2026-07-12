import axios from "axios";
import { useEffect, useMemo, useState, type JSX } from "react";

import { ApplicationShell } from "./components/layout/application-shell";
import { CreateRoomScreen } from "./components/layout/create-room-screen";
import { RoomDashboard } from "./components/layout/room-dashboard";
import type { CreateSongPayload, Room, RoomDetail } from "./types";

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
    } catch {
      setErrorMessage("Could not create room. Check whether the backend is running.");
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
    } catch {
      setErrorMessage("Could not load room.");
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
    } catch {
      setErrorMessage("Could not add song.");
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
    } catch {
      setErrorMessage("Could not move song.");
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
    } catch {
      setErrorMessage("Could not remove song.");
    }
  }

  async function handleCopyShareLink(): Promise<void> {
    if (!roomShareUrl) {
      return;
    }

    try {
      await navigator.clipboard.writeText(roomShareUrl);
      setErrorMessage("Room link copied to clipboard.");
    } catch {
      setErrorMessage("Could not copy room link.");
    }
  }

  function handleLeaveRoom(): void {
    setRoom(null);
    setErrorMessage(null);
  }

  const memberCount = room
    ? new Set(room.songs.map((song) => song.added_by.trim()).filter(Boolean)).size
    : 0;

  return (
    <ApplicationShell memberCount={memberCount} roomName={room?.name}>
      {room ? (
        <RoomDashboard
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
        />
      ) : (
        <CreateRoomScreen
          errorMessage={errorMessage}
          isLoading={isCreatingRoom}
          onCreateRoom={handleCreateRoom}
          onJoinRoom={handleJoinRoom}
        />
      )}
    </ApplicationShell>
  );
}
