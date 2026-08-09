/**
 * mock-data.js — dev convenience (ungraded).
 * Mirrors the canonical SEED_NOTES / SEED_USERS exactly.
 * Used when window.USE_MOCK = true or the backend is unreachable.
 */

window.MOCK_USERS = [
  { id: 1, name: "Alice", email: "alice@example.com" },
  { id: 2, name: "Bob",   email: "bob@example.com"   },
];

window.MOCK_NOTES = [
  { id: 1, owner_id: 1, title: "Standup Summary",    tag: "work",
    content: "Discussed sprint progress, blockers on the payments API integration, and the plan for the demo on Friday.",
    created_at: new Date(Date.now() - 1*86400000).toISOString(), updated_at: new Date(Date.now() - 1*86400000).toISOString() },

  { id: 2, owner_id: 1, title: "Sprint Retro Notes", tag: "work",
    content: "Retro highlighted communication gaps between frontend and backend teams and agreed on daily syncs going forward.",
    created_at: new Date(Date.now() - 2*86400000).toISOString(), updated_at: new Date(Date.now() - 2*86400000).toISOString() },

  { id: 3, owner_id: 2, title: "One on One",         tag: "work",
    content: "Quick check-in, no blockers, discussed career growth goals for next quarter.",
    created_at: new Date(Date.now() - 3*86400000).toISOString(), updated_at: new Date(Date.now() - 3*86400000).toISOString() },

  { id: 4, owner_id: 1, title: "Morning Run",        tag: "health",
    content: "Ran 5km along the river trail before breakfast, felt great.",
    created_at: new Date(Date.now() - 4*86400000).toISOString(), updated_at: new Date(Date.now() - 4*86400000).toISOString() },

  { id: 5, owner_id: 2, title: "Doctor Visit",       tag: "health",
    content: "Annual checkup went well, blood pressure normal, scheduled next visit in six months.",
    created_at: new Date(Date.now() - 5*86400000).toISOString(), updated_at: new Date(Date.now() - 5*86400000).toISOString() },

  { id: 6, owner_id: 1, title: "Pasta Recipe",       tag: "recipes",
    content: "Boil pasta, saute garlic in olive oil, add tomatoes, basil, and a pinch of chili flakes.",
    created_at: new Date(Date.now() - 6*86400000).toISOString(), updated_at: new Date(Date.now() - 6*86400000).toISOString() },

  { id: 7, owner_id: 2, title: "Smoothie Recipe",    tag: "recipes",
    content: "Blend banana, spinach, almond milk, and a spoon of peanut butter for breakfast.",
    created_at: new Date(Date.now() - 7*86400000).toISOString(), updated_at: new Date(Date.now() - 7*86400000).toISOString() },

  { id: 8, owner_id: 1, title: "Flight Booking",     tag: "travel",
    content: "Booked a round trip flight for the December vacation, window seat confirmed.",
    created_at: new Date(Date.now() - 8*86400000).toISOString(), updated_at: new Date(Date.now() - 8*86400000).toISOString() },

  { id: 9, owner_id: 2, title: "Random Thought",     tag: "random",
    content: "Maybe the library needs a better recommendation system based on reading history.",
    created_at: new Date(Date.now() - 9*86400000).toISOString(), updated_at: new Date(Date.now() - 9*86400000).toISOString() },

  { id: 10, owner_id: 1, title: "Quote To Remember", tag: "random",
    content: "Done is better than perfect, keep shipping.",
    created_at: new Date(Date.now() - 10*86400000).toISOString(), updated_at: new Date(Date.now() - 10*86400000).toISOString() },
];

window.MOCK_STATS = {
  total: 10,
  by_tag: [
    { tag: "work",    count: 3 },
    { tag: "health",  count: 2 },
    { tag: "recipes", count: 2 },
    { tag: "travel",  count: 1 },
    { tag: "random",  count: 2 },
  ],
  top_tags: [
    { tag: "work",    count: 3 },
    { tag: "health",  count: 2 },
    { tag: "recipes", count: 2 },
    { tag: "random",  count: 2 },
    { tag: "travel",  count: 1 },
  ],
  recent: window.MOCK_NOTES.slice(0, 5),
  created_last_7days: [],
};
