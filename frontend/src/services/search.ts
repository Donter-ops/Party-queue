export interface SearchResultItem {
  title: string;
  artist: string;
  provider: string;
  confidence: number;
  external_id: string;
  external_url?: string | null;
}

const apiBaseUrl = `${window.location.protocol}//${window.location.hostname}:8000`;

export async function searchSongs(input: string): Promise<SearchResultItem[]> {
  const trimmedInput = input.trim();
  if (!trimmedInput) {
    return [];
  }

  const response = await fetch(`${apiBaseUrl}/search?input=${encodeURIComponent(trimmedInput)}`);
  if (!response.ok) {
    throw new Error("Search request failed.");
  }

  return (await response.json()) as SearchResultItem[];
}
