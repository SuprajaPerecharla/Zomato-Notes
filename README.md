# Zomato Notes — On-Call Knowledge Base

Internal incident notes and knowledge-base app for Zomato's on-call support engineering team. Engineers capture short notes during and after incidents, tag them for later retrieval, search across them quickly while an incident is live, and get lightweight AI assistance so classifying and finding notes costs as little time as possible during a stressful on-call shift.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Browser (React + Vite)               │
│                                                          │
│  Dashboard  NoteEditor  NoteDetail  SearchPage           │
│  └─ TagSidebar  └─ TagInput  └─ NoteCard                 │
│                                                          │
│  src/api/client.ts  ──── /api/* ──────────────────────► │
└───────────────────────────────────┬─────────────────────┘
                                    │  HTTP (Vite proxy dev)
                                    │  Direct call (prod build)
┌───────────────────────────────────▼─────────────────────┐
│              FastAPI  (app/main.py)  :8000                │
│                                                          │
│  /api/notes/*   →  routers/notes.py  →  crud.py          │
│  /api/search/*  →  routers/search.py                     │
│  /api/tags/*    →  routers/tags.py                       │
│                                                          │
│  ┌──────────────────────┐  ┌────────────────────────┐   │
│  │   Ranking Engine     │  │  Intelligence Layer     │   │
│  │  services/ranking.py │  │  services/intelligence  │   │
│  │                      │  │  .py                    │   │
│  │  • exact_title_search│  │  • auto_tag (OpenAI)    │   │
│  │  • BM25 keyword rank │  │  • semantic_search      │   │
│  │  • tag_quick_jump    │  │    (sentence-transformers│  │
│  └──────────────────────┘  └────────────────────────┘   │
│                                                          │
│  SQLAlchemy ORM  →  SQLite  (zomato_notes.db)            │
└─────────────────────────────────────────────────────────┘
```

### Component map

| Layer | File(s) | Purpose |
|---|---|---|
| ORM models | `backend/app/models.py` | `Note`, `Tag`, `note_tags` join table |
| Schemas | `backend/app/schemas.py` | Pydantic v2 request/response validation |
| CRUD | `backend/app/crud.py` | Raw DB operations, no business logic |
| Notes router | `backend/app/routers/notes.py` | CRUD + auto-tag endpoint |
| Search router | `backend/app/routers/search.py` | Unified search + tag jump |
| Tags router | `backend/app/routers/tags.py` | Tag list |
| **Ranking Engine** | `backend/app/services/ranking.py` | Hand-written BM25, exact title, tag jump |
| **Intelligence** | `backend/app/services/intelligence.py` | OpenAI auto-tagger + semantic search |
| API client | `frontend/src/api/client.ts` | Typed fetch wrapper — calls real backend |
| Pages | `frontend/src/components/` | Dashboard, NoteEditor, NoteDetail, SearchPage |

---

## Prerequisites

| Tool | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ (for frontend) |
| npm | 9+ |
| OpenAI API key | optional — auto-tag and semantic search degrade gracefully without it |

---

## Quick Start

### 1. Clone

```bash
git clone <your-repo-url>
cd "Zomato Notes"
```

### 2. Backend

```bash
cd backend

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY (optional but recommended)

# Install dependencies (handles Python 3.14's pydantic pre-release automatically)
chmod +x install.sh && ./install.sh
source .venv/bin/activate

# Start the API server
uvicorn app.main:app --reload --port 8000
```

> **Python 3.14 note:** `pydantic-core` does not yet ship a stable wheel for Python 3.14.
> `install.sh` detects this and installs the pre-release automatically.
> On Python 3.11–3.13 a plain `pip install -r requirements.txt` works fine.

The API is now live at **http://localhost:8000**.  
Interactive docs: **http://localhost:8000/docs**

### 3. Frontend

```bash
cd frontend

npm install
npm run dev
```

The dashboard is now live at **http://localhost:5173**.

> The Vite dev server proxies all `/api/*` requests to `http://localhost:8000`, so no CORS config is needed during development.

---

## Environment Variables

All variables live in `backend/.env` (copy from `.env.example`).

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./zomato_notes.db` | SQLAlchemy connection string |
| `OPENAI_API_KEY` | _(empty)_ | Required for auto-tagging. App works without it. |
| `OPENAI_MODEL` | `gpt-4o-mini` | Chat model used by the auto-tagger |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | sentence-transformers model for semantic search |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Comma-separated allowed origins |

---

## Feature Walkthrough

### Core App

- **Dashboard** — paginated note list with severity filter and tag sidebar for quick navigation.
- **New / Edit Note** — title, body (monospace), severity picker, tag input (Enter or comma to add). Validates required fields client- and server-side.
- **Note Detail** — full body, metadata, one-click delete with confirmation, edit link, and manual auto-tag trigger.

### Ranking Engine (`services/ranking.py`)

All algorithms are hand-written — no Elasticsearch, Whoosh, or other search library.

| Algorithm | Description |
|---|---|
| `exact_title_search` | O(n) linear scan; normalised string equality; score = 1.0 |
| `keyword_search` | BM25-inspired TF-IDF with title (3×) and tag (2×) field weighting |
| `tag_quick_jump` | O(n × avg_tags) membership scan, recency sorted |
| `ranked_search` | Pipeline: exact match first → BM25 → recency blend |

### Intelligence Layer (`services/intelligence.py`)

| Feature | How it works |
|---|---|
| **Auto-tagger** | On note creation (if no tags supplied), calls `gpt-4o-mini` with a system prompt to suggest up to 5 incident-relevant tags. Falls back silently if key is absent. |
| **Semantic search** | Encodes notes with `all-MiniLM-L6-v2` (sentence-transformers) into 384-dim unit-norm vectors stored as JSON in SQLite. Cosine similarity via numpy — no vector DB. |
| **Embedding persistence** | Computed in a FastAPI `BackgroundTask` after create/update so the API response is never blocked. |

### Search Modes (Search Page)

| Mode | Algorithm |
|---|---|
| **Smart (auto)** | BM25 + semantic merged, deduplicated, re-ranked by score |
| **Keyword** | BM25 only — always available, fast |
| **Semantic** | Cosine similarity over stored embeddings — requires model |

---

## API Reference

The full OpenAPI spec is available at `http://localhost:8000/docs` when the server is running.

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/notes/` | Create a note (triggers auto-tag + embedding) |
| `GET` | `/api/notes/` | List notes (filter by severity, tag; paginate) |
| `GET` | `/api/notes/{id}` | Get a single note |
| `PUT` | `/api/notes/{id}` | Update a note |
| `DELETE` | `/api/notes/{id}` | Delete a note |
| `POST` | `/api/notes/{id}/autotag` | Suggest (or apply) AI tags for a note |
| `GET` | `/api/search/?q=…&mode=…` | Ranked search (keyword / semantic / auto) |
| `GET` | `/api/search/tag/{tag}` | Tag quick-jump — all notes with this tag |
| `GET` | `/api/tags/` | List all tags |

---

## Project Structure

```
Zomato Notes/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app, lifespan, CORS, router wiring
│   │   ├── config.py         # Pydantic-settings config
│   │   ├── database.py       # SQLAlchemy engine, session, init_db
│   │   ├── models.py         # ORM: Note, Tag, note_tags
│   │   ├── schemas.py        # Pydantic v2 schemas
│   │   ├── crud.py           # DB operations
│   │   ├── routers/
│   │   │   ├── notes.py      # /api/notes CRUD + autotag
│   │   │   ├── search.py     # /api/search keyword+semantic+tag-jump
│   │   │   └── tags.py       # /api/tags list
│   │   └── services/
│   │       ├── ranking.py    # Hand-written BM25, exact-title, tag-jump
│   │       └── intelligence.py  # OpenAI auto-tagger + semantic search
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── api/
    │   │   ├── client.ts     # Typed fetch wrapper — no mocks
    │   │   └── types.ts      # TypeScript interfaces
    │   ├── components/
    │   │   ├── Layout.tsx        # App shell, global search bar
    │   │   ├── Dashboard.tsx     # Note list + filters + pagination
    │   │   ├── NoteCard.tsx      # Note preview card
    │   │   ├── NoteDetail.tsx    # Full note view + delete + auto-tag
    │   │   ├── NoteEditor.tsx    # Create / edit form
    │   │   ├── SearchPage.tsx    # Smart search with mode switcher
    │   │   ├── TagSidebar.tsx    # Tag quick-jump sidebar
    │   │   ├── TagChip.tsx       # Clickable tag pill
    │   │   ├── TagInput.tsx      # Tag entry widget
    │   │   └── SeverityBadge.tsx # Colour-coded severity pill
    │   ├── App.tsx           # React Router routes
    │   ├── main.tsx          # React entry point
    │   └── index.css         # Tailwind + global styles
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.js
    └── index.html
```

---

## Without an OpenAI Key

The app is fully functional without an API key:

- Notes can be manually tagged via the tag input in NoteEditor.
- Search defaults to keyword (BM25) mode.
- The "AI Suggest" and "Auto-tag" buttons will return an empty suggestion list and show a toast message.
- Semantic search falls back gracefully: the sentence-transformers model still loads locally (no API key needed) and embeddings are computed on-device.

---

## License

MIT
