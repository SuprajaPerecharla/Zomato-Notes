# Zomato Notes — On-Call Knowledge Base

Internal incident notes and knowledge-base app for Zomato's on-call support engineering team.

---

## Project Structure

```
zomato-notes/
├── backend/
│   ├── main.py            # FastAPI app — all endpoints (Parts 1, 2, 3)
│   ├── models.py          # SQLAlchemy User + Note ORM models
│   ├── schemas.py         # Pydantic v2 request/response schemas
│   ├── database.py        # engine, SessionLocal, get_db, init_db
│   ├── crud.py            # CRUD + reporting query logic
│   ├── algorithms.py      # Part 2: insertion sort, binary search ×2, linear search
│   ├── ai_service.py      # Part 3: get_ai_response() + 5-part prompt template
│   ├── semantic_search.py # Part 3: sentence-transformers embeddings + cosine similarity
│   ├── ranking_dataset.py # Part 2 sample dataset (15 notes)
│   ├── ai_sample_notes.py # Part 3 sample dataset (10 notes)
│   ├── seed.py            # loads all sample data into the database
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html         # Single-page app shell
│   ├── style.css          # Dark-theme stylesheet
│   ├── script.js          # Vanilla JS — all API calls to real backend
│   └── mock-data.js       # Dev convenience: mock data when backend is offline
├── sample_import.txt      # 10 non-empty lines for the bulk-import endpoint
└── README.md
```

---

## Quick Start

### 1. Backend

```bash
cd backend

# Python 3.11–3.13 (recommended)
python -m venv .venv
source .venv/bin/activate

# Python 3.14 — pydantic-core needs a pre-release wheel
pip install --pre pydantic pydantic-settings
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your OPENAI_API_KEY to .env (optional — app works without it)

# Start the server
uvicorn main:app --reload --port 8000
```

API docs: **http://localhost:8000/docs**

### 2. Seed the database

```bash
cd backend
python seed.py           # inserts 25 sample notes + 2 users
python seed.py --reset   # wipe and re-seed
```

### 3. Frontend

Open `frontend/index.html` directly in your browser, **or** serve it:

```bash
cd frontend
python -m http.server 5500
# then open http://localhost:5500
```

The frontend calls the backend at `http://localhost:8000` by default.
If the backend is unreachable it falls back to `mock-data.js` automatically.

### 4. Bulk import

```bash
curl -X POST "http://localhost:8000/notes/bulk-import/json" \
  -H "Content-Type: application/json" \
  -d "{\"lines\": $(jq -R '[.,inputs]' < sample_import.txt)}"
```

Or paste the contents of `sample_import.txt` into the Import dialog in the UI.

---

## API Reference

Full interactive docs at **http://localhost:8000/docs**.

### Part 1 — Core CRUD

| Method | Path | Description |
|---|---|---|
| `POST` | `/notes/` | Create note (auto-tags if tags empty) |
| `GET` | `/notes/` | List notes (filter: severity, tag, author_id) |
| `GET` | `/notes/{id}` | Get single note |
| `PUT` | `/notes/{id}` | Update note |
| `DELETE` | `/notes/{id}` | Delete note |
| `POST` | `/notes/bulk-import/json` | Bulk import from JSON list of strings |
| `GET` | `/notes/report/stats` | Stats: counts, top tags, recent notes |
| `POST` | `/users/` | Create user |
| `GET` | `/users/` | List users |

### Part 2 — Ranking Engine

| Method | Path | Description |
|---|---|---|
| `GET` | `/search/?q=…&mode=keyword` | BM25 + exact-title + prefix search |
| `GET` | `/search/?q=…&mode=semantic` | Cosine similarity over embeddings |
| `GET` | `/search/?q=…&mode=auto` | Keyword + semantic merged |
| `GET` | `/search/tag/{tag}` | Tag quick-jump (linear scan) |
| `GET` | `/search/sort` | Insertion-sort demo (sort_by, order) |
| `GET` | `/search/by-id/{id}` | Binary search by ID demo |

### Part 3 — AI Layer

| Method | Path | Description |
|---|---|---|
| `POST` | `/ai/ask/{note_id}?question=…` | Ask LLM about a note |
| `POST` | `/ai/autotag/{note_id}?apply=true` | Suggest + optionally apply tags |
| `POST` | `/ai/summarise/{note_id}` | One-sentence summary |
| `POST` | `/ai/classify` | Predict severity for raw text |
| `POST` | `/ai/runbook/{note_id}` | Next-action runbook suggestion |

---

## Architecture

```
Browser (vanilla HTML/CSS/JS)
        │  fetch /notes, /search, /ai, …
        ▼
FastAPI (main.py) — single flat file, port 8000
        │
        ├── database.py   SQLite via SQLAlchemy
        ├── crud.py       DB operations + reporting
        ├── algorithms.py insertion sort · binary search ×2 · linear search · BM25
        ├── ai_service.py OpenAI chat completions (5-part prompt template)
        └── semantic_search.py  sentence-transformers + numpy cosine similarity
```

### Algorithms (Part 2)

| Function | Complexity | Used in |
|---|---|---|
| `insertion_sort` | O(n²) | `/search/sort` |
| `binary_search_by_id` | O(log n) | `/search/by-id/{id}` |
| `binary_search_by_title` | O(log n + k) | `ranked_keyword_search` |
| `linear_search` | O(n) | full-text fallback |
| `ranked_keyword_search` | O(n log n) | `/search/?mode=keyword` |
| `tag_quick_jump` | O(n) | `/search/tag/{tag}` |

### AI (Part 3)

| Feature | How it works |
|---|---|
| Auto-tagger | Fires on note creation when tags are empty; calls `gpt-4o-mini` with the 5-part prompt template |
| Semantic search | `all-MiniLM-L6-v2` encodes notes to 384-dim unit-norm vectors; cosine sim via numpy |
| Summarise | 5-part prompt, 30-word output constraint |
| Classify severity | 5-part prompt, single-word response |
| Runbook step | 5-part prompt, one bullet point |

---

## Without an OpenAI Key

The app is fully functional without an API key:

- Notes can be tagged manually.
- Keyword and semantic search both work.
- AI endpoints return a graceful fallback message.
- Semantic search uses `sentence-transformers` locally (no API key needed).

---

## Seed Users

After `python seed.py`:

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | admin |
| `engineer` | `engineer123` | engineer |
