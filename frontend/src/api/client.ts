/**
 * Thin API client — all calls go to the real FastAPI backend.
 * The Vite proxy forwards /api/* to http://localhost:8000.
 */

import type {
  Note,
  NoteCreate,
  NoteUpdate,
  Tag,
  SearchResponse,
  TagJumpResult,
  AutoTagResponse,
} from "./types";

const BASE = "/api";

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${text}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Notes
// ---------------------------------------------------------------------------

export const getNotes = (params?: {
  skip?: number;
  limit?: number;
  severity?: string;
  tag?: string;
}) => {
  const qs = new URLSearchParams();
  if (params?.skip !== undefined) qs.set("skip", String(params.skip));
  if (params?.limit !== undefined) qs.set("limit", String(params.limit));
  if (params?.severity) qs.set("severity", params.severity);
  if (params?.tag) qs.set("tag", params.tag);
  const query = qs.toString() ? `?${qs}` : "";
  return request<Note[]>(`/notes/${query}`);
};

export const getNote = (id: number) => request<Note>(`/notes/${id}`);

export const createNote = (payload: NoteCreate) =>
  request<Note>("/notes/", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const updateNote = (id: number, payload: NoteUpdate) =>
  request<Note>(`/notes/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });

export const deleteNote = (id: number) =>
  request<void>(`/notes/${id}`, { method: "DELETE" });

export const autoTagNote = (id: number, apply = false) =>
  request<AutoTagResponse>(`/notes/${id}/autotag?apply=${apply}`, {
    method: "POST",
  });

// ---------------------------------------------------------------------------
// Tags
// ---------------------------------------------------------------------------

export const getTags = () => request<Tag[]>("/tags/");

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------

export const search = (
  q: string,
  mode: "keyword" | "semantic" | "auto" = "auto",
  top_k = 20
) => {
  const qs = new URLSearchParams({ q, mode, top_k: String(top_k) });
  return request<SearchResponse>(`/search/?${qs}`);
};

export const tagJump = (tagName: string) =>
  request<TagJumpResult>(`/search/tag/${encodeURIComponent(tagName)}`);
