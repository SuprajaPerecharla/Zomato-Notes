"""
seed.py — Load the canonical seed data into the database.

Usage
-----
    cd backend
    python seed.py            # seed (idempotent — skips existing records)
    python seed.py --reset    # wipe all data first, then seed

Seed data
---------
  SEED_USERS  — 2 users: Alice, Bob
  SEED_NOTES  — 10 notes across 5 tags: work, health, recipes, travel, random
"""

from __future__ import annotations

import argparse
from database import init_db, SessionLocal
import models
import schemas
import crud


# ---------------------------------------------------------------------------
# Canonical seed data (verbatim from spec)
# ---------------------------------------------------------------------------

SEED_USERS = [
    {"id": 1, "name": "Alice", "email": "alice@example.com", "password": "alicepass123"},
    {"id": 2, "name": "Bob",   "email": "bob@example.com",   "password": "bobpass123"},
]

SEED_NOTES = [
    {
        "id": 1, "owner_id": 1,
        "title": "Standup Summary", "tag": "work",
        "content": "Discussed sprint progress, blockers on the payments API integration, and the plan for the demo on Friday.",
    },
    {
        "id": 2, "owner_id": 1,
        "title": "Sprint Retro Notes", "tag": "work",
        "content": "Retro highlighted communication gaps between frontend and backend teams and agreed on daily syncs going forward.",
    },
    {
        "id": 3, "owner_id": 2,
        "title": "One on One", "tag": "work",
        "content": "Quick check-in, no blockers, discussed career growth goals for next quarter.",
    },
    {
        "id": 4, "owner_id": 1,
        "title": "Morning Run", "tag": "health",
        "content": "Ran 5km along the river trail before breakfast, felt great.",
    },
    {
        "id": 5, "owner_id": 2,
        "title": "Doctor Visit", "tag": "health",
        "content": "Annual checkup went well, blood pressure normal, scheduled next visit in six months.",
    },
    {
        "id": 6, "owner_id": 1,
        "title": "Pasta Recipe", "tag": "recipes",
        "content": "Boil pasta, saute garlic in olive oil, add tomatoes, basil, and a pinch of chili flakes.",
    },
    {
        "id": 7, "owner_id": 2,
        "title": "Smoothie Recipe", "tag": "recipes",
        "content": "Blend banana, spinach, almond milk, and a spoon of peanut butter for breakfast.",
    },
    {
        "id": 8, "owner_id": 1,
        "title": "Flight Booking", "tag": "travel",
        "content": "Booked a round trip flight for the December vacation, window seat confirmed.",
    },
    {
        "id": 9, "owner_id": 2,
        "title": "Random Thought", "tag": "random",
        "content": "Maybe the library needs a better recommendation system based on reading history.",
    },
    {
        "id": 10, "owner_id": 1,
        "title": "Quote To Remember", "tag": "random",
        "content": "Done is better than perfect, keep shipping.",
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def seed_users(db) -> dict:
    """Create seed users; skip if email already exists. Returns {name: User}."""
    created = {}
    for u in SEED_USERS:
        existing = crud.get_user_by_email(db, u["email"])
        if existing:
            created[u["name"]] = existing
            print(f"  [skip] user '{u['name']}' ({u['email']}) already exists")
        else:
            user = crud.create_user(db, schemas.UserCreate(
                name=u["name"], email=u["email"], password=u["password"]
            ))
            created[u["name"]] = user
            print(f"  [ok]   user '{user.name}' created  id={user.id}")
    return created


def seed_notes(db, users: dict) -> int:
    """Create seed notes; skip if title already exists. Returns count inserted."""
    existing_titles = {n.title.strip().lower() for n in crud.get_all_notes(db)}
    # Map seed user name → DB id
    name_to_id = {name: user.id for name, user in users.items()}
    # Map seed owner_id index → DB user name
    idx_to_name = {1: "Alice", 2: "Bob"}

    count = 0
    for data in SEED_NOTES:
        if data["title"].strip().lower() in existing_titles:
            print(f"  [skip] note '{data['title']}'")
            continue
        owner_name = idx_to_name.get(data["owner_id"])
        owner_db_id = name_to_id.get(owner_name) if owner_name else None

        note = crud.create_note(db, schemas.NoteCreate(
            title=data["title"],
            content=data["content"],
            tag=data["tag"],
            owner_id=owner_db_id,
        ))
        existing_titles.add(note.title.strip().lower())
        print(f"  [ok]   note id={note.id} '{note.title}' [{note.tag}]  owner={owner_name}")
        count += 1
    return count


def reset_db(db) -> None:
    print("Resetting database …")
    db.query(models.Note).delete()
    db.query(models.User).delete()
    db.commit()
    print("Reset complete.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Seed the Zomato Notes database.")
    parser.add_argument("--reset", action="store_true", help="Wipe all data before seeding")
    args = parser.parse_args()

    print("Initialising database schema …")
    init_db()

    db = SessionLocal()
    try:
        if args.reset:
            reset_db(db)

        print("\n── Seeding users ──────────────────────────")
        users = seed_users(db)

        print("\n── Seeding notes ──────────────────────────")
        n = seed_notes(db, users)

        print(f"\nDone — inserted {n} new note(s).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
