import axios from "axios";
import { useEffect, useMemo, useState, type JSX } from "react";

import { ApplicationShell } from "./components/layout/application-shell";
import { ConnectSpotifyScreen } from "./components/layout/connect-spotify-screen";
import { CreateRoomScreen } from "./components/layout/create-room-screen";
import { RoomDashboard } from "./components/layout/room-dashboard";
import type {
  CreateSongPayload,
  PlaybackSession,
  ResolverDebugTrace,
  Room,
  RoomDetail,
} from "./types";

const apiBaseUrl = `${window.location.protocol}//${window.location.hostname}:8000`;

const api = axios.create({
  baseURL: apiBaseUrl,
});

function getInitialRoomId(): string | null {
  const roomId = new URLSearchParams(window.location.search).get("room");
  return roomId && roomId.trim() ? roomId.trim() : null;
}

export function App(): JSX.Element {
  const pathname = window.location.pathname;
  const [room, setRoom] = useState<RoomDetail | null>(null);
  const [isCreatingRoom, setIsCreatingRoom] = useState(false);
  const [isRefreshingRoom, setIsRefreshingRoom] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [playbackSession, setPlaybackSession] = useState<PlaybackSession | null>(null);
  const [resolverDebugTrace, setResolverDebugTrace] = useState<ResolverDebugTrace | null>(null);
  const [savedGuestName, setSavedGuestName] = useState("");
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);
  const isDevelopment =
    window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";

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
    void refreshPlayback(roomId);
    if (isDevelopment) {
      void refreshResolverDebug(roomId);
    }
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
      void refreshPlayback(room.id, { silent: true });
      if (isDevelopment) {
        void refreshResolverDebug(room.id, { silent: true });
      }
    }, 3000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [autoRefreshEnabled, isDevelopment, room]);

  useEffect(() => {
    if (!room) {
      window.history.replaceState({}, "", window.location.pathname);
      setPlaybackSession(null);
      setResolverDebugTrace(null);
      return;
    }

    const nextUrl = `${window.location.pathname}?room=${room.id}`;
    window.history.replaceState({}, "", nextUrl);
  }, [room]);

  useEffect(() => {
    if (!room) {
      return;
    }

    void refreshPlayback(room.id);
    if (isDevelopment) {
      void refreshResolverDebug(room.id, { silent: true });
    }
  }, [isDevelopment, room?.id]);

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
      setPlaybackSession(null);
      setResolverDebugTrace(null);
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
      await refreshPlayback(roomId);
      if (isDevelopment) {
        await refreshResolverDebug(roomId);
      }
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
      await refreshPlayback(room.id, { silent: true });
      if (isDevelopment) {
        await refreshResolverDebug(room.id, { silent: true });
      }
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
      await refreshPlayback(room.id, { silent: true });
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
      await refreshPlayback(room.id, { silent: true });
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
    setPlaybackSession(null);
    setResolverDebugTrace(null);
    setErrorMessage(null);
  }

  async function refreshPlayback(
    roomId: string,
    options?: { silent?: boolean },
  ): Promise<void> {
    try {
      const response = await api.get<PlaybackSession | null>(`/rooms/${roomId}/playback`);
      setPlaybackSession(response.data);
    } catch {
      if (!options?.silent) {
        setErrorMessage("Could not load playback.");
      }
    }
  }

  async function refreshResolverDebug(
    roomId: string,
    options?: { silent?: boolean },
  ): Promise<void> {
    if (!isDevelopment) {
      return;
    }

    try {
      const response = await api.get<ResolverDebugTrace | null>(`/rooms/${roomId}/resolver/debug/latest`);
      setResolverDebugTrace(response.data);
    } catch {
      if (!options?.silent) {
        setResolverDebugTrace(null);
      }
    }
  }

  async function startPlayback(roomId: string): Promise<void> {
    try {
      const response = await api.post<PlaybackSession>(`/rooms/${roomId}/playback/start`);
      setPlaybackSession(response.data);
      setErrorMessage(null);
    } catch {
      setErrorMessage("Could not start playback.");
    }
  }

  async function pausePlayback(roomId: string): Promise<void> {
    try {
      const response = await api.post<PlaybackSession>(`/rooms/${roomId}/playback/pause`);
      setPlaybackSession(response.data);
      setErrorMessage(null);
    } catch {
      setErrorMessage("Could not pause playback.");
    }
  }

  async function resumePlayback(roomId: string): Promise<void> {
    try {
      const response = await api.post<PlaybackSession>(`/rooms/${roomId}/playback/resume`);
      setPlaybackSession(response.data);
      setErrorMessage(null);
    } catch {
      setErrorMessage("Could not resume playback.");
    }
  }

  async function handlePlaybackFinished(): Promise<void> {
    if (!room) {
      return;
    }

    try {
      const response = await api.post<PlaybackSession>(`/rooms/${room.id}/playback/finish`);
      setPlaybackSession(response.data);
      setErrorMessage(null);
    } catch {
      setErrorMessage("Could not advance playback.");
    }
  }

  async function handlePlaybackNext(): Promise<void> {
    if (!room) {
      return;
    }

    try {
      const response = await api.post<PlaybackSession>(`/rooms/${room.id}/playback/next`);
      setPlaybackSession(response.data);
      setErrorMessage(null);
      await refreshRoom(room.id, { silent: true });
    } catch {
      setErrorMessage("Could not skip to the next song.");
    }
  }

  async function handlePlaybackPrevious(): Promise<void> {
    if (!room) {
      return;
    }

    try {
      const response = await api.post<PlaybackSession>(`/rooms/${room.id}/playback/previous`);
      setPlaybackSession(response.data);
      setErrorMessage(null);
      await refreshRoom(room.id, { silent: true });
    } catch {
      setErrorMessage("Could not return to the previous song.");
    }
  }

  async function handlePlaybackToggle(): Promise<void> {
    if (!room) {
      return;
    }

    if (playbackSession?.state === "PLAYING") {
      await pausePlayback(room.id);
      return;
    }

    if (playbackSession?.state === "PAUSED") {
      await resumePlayback(room.id);
      return;
    }

    await startPlayback(room.id);
  }

  const memberCount = room
    ? new Set(room.songs.map((song) => song.added_by.trim()).filter(Boolean)).size
    : 0;

  if (pathname === "/connect-spotify") {
    const params = new URLSearchParams(window.location.search);
    const statusParam = params.get("status");
    const status =
      statusParam === "success" || statusParam === "error" ? statusParam : "idle";
    const connectErrorMessage = params.get("error");

    return (
      <ApplicationShell memberCount={0} roomName="Spotify Host">
        <ConnectSpotifyScreen errorMessage={connectErrorMessage} status={status} />
      </ApplicationShell>
    );
  }

  return (
    <ApplicationShell memberCount={memberCount} roomName={room?.name}>
      {room ? (
        <RoomDashboard
          errorMessage={errorMessage}
          isRefreshing={isRefreshingRoom}
          playbackSession={playbackSession}
          resolverDebugTrace={resolverDebugTrace}
          room={room}
          roomShareUrl={roomShareUrl}
          savedGuestName={savedGuestName}
          onAddSong={handleAddSong}
          onCopyShareLink={handleCopyShareLink}
          onDeleteSong={handleDeleteSong}
          onLeaveRoom={handleLeaveRoom}
          onMoveSong={handleMoveSong}
          onPlaybackFinished={handlePlaybackFinished}
          onPlaybackNext={handlePlaybackNext}
          onPlaybackPrevious={handlePlaybackPrevious}
          onPlaybackToggle={handlePlaybackToggle}
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
