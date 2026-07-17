import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  type JSX,
} from "react";

declare global {
  interface Window {
    YT?: YouTubeNamespace;
    onYouTubeIframeAPIReady?: () => void;
  }
}

interface YouTubePlayerInstance {
  playVideo(): void;
  pauseVideo(): void;
  loadVideoById(options: { videoId: string }): void;
  destroy(): void;
}

interface YouTubePlayerEvent {
  data: number;
  target: YouTubePlayerInstance;
}

interface YouTubeNamespace {
  Player: new (
    element: HTMLElement,
    options: {
      videoId?: string;
      playerVars?: Record<string, number>;
      events?: {
        onReady?: (event: YouTubePlayerEvent) => void;
        onStateChange?: (event: YouTubePlayerEvent) => void;
      };
    },
  ) => YouTubePlayerInstance;
  PlayerState: {
    ENDED: number;
  };
}

export interface YouTubePlayerHandle {
  play(): void;
  pause(): void;
  load(videoId: string): void;
}

interface YouTubePlayerProps {
  videoId: string | null;
  onEnded?: () => void;
  onReady?: () => void;
}

let youtubeIframeApiPromise: Promise<YouTubeNamespace> | null = null;

function loadYouTubeIframeApi(): Promise<YouTubeNamespace> {
  if (window.YT?.Player) {
    return Promise.resolve(window.YT);
  }

  if (youtubeIframeApiPromise) {
    return youtubeIframeApiPromise;
  }

  youtubeIframeApiPromise = new Promise<YouTubeNamespace>((resolve, reject) => {
    const existingScript = document.getElementById("partyqueue-youtube-iframe-api");
    const previousReadyHandler = window.onYouTubeIframeAPIReady;

    window.onYouTubeIframeAPIReady = () => {
      previousReadyHandler?.();
      if (window.YT?.Player) {
        resolve(window.YT);
        return;
      }

      reject(new Error("YouTube IFrame API did not initialize."));
    };

    if (existingScript) {
      return;
    }

    const script = document.createElement("script");
    script.id = "partyqueue-youtube-iframe-api";
    script.src = "https://www.youtube.com/iframe_api";
    script.async = true;
    script.onerror = () => reject(new Error("Could not load YouTube IFrame API."));
    document.head.appendChild(script);
  });

  return youtubeIframeApiPromise;
}

export const YouTubePlayer = forwardRef<YouTubePlayerHandle, YouTubePlayerProps>(
  function YouTubePlayer({ videoId, onEnded, onReady }, ref): JSX.Element {
    const containerRef = useRef<HTMLDivElement | null>(null);
    const playerRef = useRef<YouTubePlayerInstance | null>(null);
    const loadedVideoIdRef = useRef<string | null>(videoId);
    const onEndedRef = useRef(onEnded);
    const onReadyRef = useRef(onReady);

    useEffect(() => {
      onEndedRef.current = onEnded;
      onReadyRef.current = onReady;
    }, [onEnded, onReady]);

    useImperativeHandle(ref, () => ({
      play() {
        playerRef.current?.playVideo();
      },
      pause() {
        playerRef.current?.pauseVideo();
      },
      load(nextVideoId: string) {
        if (!playerRef.current) {
          return;
        }

        loadedVideoIdRef.current = nextVideoId;
        playerRef.current.loadVideoById({ videoId: nextVideoId });
      },
    }));

    useEffect(() => {
      let isMounted = true;

      void loadYouTubeIframeApi()
        .then((youtube) => {
          if (!isMounted || !containerRef.current || playerRef.current) {
            return;
          }

          playerRef.current = new youtube.Player(containerRef.current, {
            videoId: videoId ?? undefined,
            playerVars: {
              autoplay: videoId ? 1 : 0,
              controls: 0,
              playsinline: 1,
              rel: 0,
            },
            events: {
              onReady(event) {
                onReadyRef.current?.();
                if (loadedVideoIdRef.current) {
                  event.target.playVideo();
                }
              },
              onStateChange(event) {
                if (event.data === youtube.PlayerState.ENDED) {
                  onEndedRef.current?.();
                }
              },
            },
          });
        })
        .catch(() => {
          // Player failures stay silent here so the room view can continue rendering.
        });

      return () => {
        isMounted = false;
        playerRef.current?.destroy();
        playerRef.current = null;
      };
    }, []);

    useEffect(() => {
      if (!playerRef.current || !videoId || videoId === loadedVideoIdRef.current) {
        return;
      }

      loadedVideoIdRef.current = videoId;
      playerRef.current.loadVideoById({ videoId });
    }, [videoId]);

    return (
      <div className="overflow-hidden rounded-[28px] bg-black/40 shadow-[0_24px_80px_rgba(15,23,42,0.4)]">
        <div className="aspect-video min-h-[240px] w-full" ref={containerRef} />
      </div>
    );
  },
);
