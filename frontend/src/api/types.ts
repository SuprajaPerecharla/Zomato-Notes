export type Severity = "low" | "medium" | "high" | "critical";

export interface Tag {
  id: number;
  name: string;
}

export interface Note {
  id: number;
  title: string;
  body: string;
  severity: Severity;
  tags: Tag[];
  created_at: string;
  updated_at: string;
}

export interface NoteCreate {
  title: string;
  body: string;
  severity: Severity;
  tags: string[];
}

export interface NoteUpdate {
  title?: string;
  body?: string;
  severity?: Severity;
  tags?: string[];
}

export interface SearchResult {
  note: Note;
  score: number;
  match_type: "exact_title" | "keyword" | "semantic";
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total: number;
}

export interface TagJumpResult {
  tag: string;
  notes: Note[];
  total: number;
}

export interface AutoTagResponse {
  suggested_tags: string[];
  applied: boolean;
}
