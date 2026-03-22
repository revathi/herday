# Shakti 💜 — AI Life-Load Assistant

A unified AI assistant that eliminates the invisible mental load on women by intelligently managing meal planning, grocery tracking, and professional task prioritisation — all in one place. Powered by Claude AI (Anthropic).

---

## How to Run

```bash
# Activate virtual environment
venv/Scripts/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

App opens at: http://localhost:8501

---

## Tech Stack

| Layer | Tool |
|-------|------|
| Language | Python 3.12 |
| AI Brain | Claude API (Anthropic) — Haiku model |
| Frontend | Streamlit (Lavender theme) |
| Database | SQLite via SQLAlchemy |
| Env | python-dotenv |

---

## Project Structure

```
women_ai/
├── app.py              — Main Streamlit UI (single page, chat-first)
├── agent.py            — Claude AI agent (daily plan, meal suggestions, chat)
├── analytics.py        — Weekly time-saved tracking and summary
├── database.py         — SQLite connection and session management
├── models.py           — SQLAlchemy models (Task, Meal, DailyLog)
├── crud.py             — Database operations (tasks, meals, logs)
├── main.py             — Terminal entry point for quick testing
├── requirements.txt    — Python dependencies
├── .env                — Anthropic API key (not committed)
├── data/
│   ├── user_profile.json   — User preferences, health info, dietary settings
│   └── sarah_monday.json   — Stub data: heavy Monday scenario for demo
└── tasks.md            — Full product backlog (Frontend, Backend, AI tasks)
```

---

## Demo Scenario — Heavy Day (Sarah's Monday)

Sarah has 5 back-to-back meetings, a Q1 report due today, and low energy. She opens Shakti and types *"Plan my day — it's a heavy one"*.

The assistant:
- Detects it is a heavy day from calendar + energy level
- Surfaces only the **top 2 work tasks** she can realistically complete
- Defers the rest automatically with reasons
- Suggests a **quick Indian breakfast** using fridge items
- Plans a **kid's lunchbox** using breakfast leftovers
- Recommends **ordering outside for dinner** (heavy day, low energy)
- Generates a **grocery list** for only missing items
- Saves approximately **45–55 minutes** of mental planning

---

## Sprint Summary

### Sprint 1 — Core AI Agent ✅
- Claude API integration via `agent.py`
- Stub data for Sarah's heavy Monday (`sarah_monday.json`)
- Terminal output via `main.py`
- User profile JSON (`user_profile.json`) with dietary and cook time preferences
- Basic Streamlit dashboard (`app.py`)

### Sprint 2 — Task Management ✅
- SQLite database with SQLAlchemy (`database.py`, `models.py`)
- Task model: domain (work/home), priority, due date, estimated time, done, deferred
- Full CRUD operations (`crud.py`)
- Unified task list in sidebar — work + home in one view with filter
- Done and Defer buttons per task
- Deferred tasks section with Bring Back option
- Seed data pre-loaded for demo

### Sprint 3 — Meal Planning ✅
- Meal model in SQLite: meal_type, name, prep time, instructions, ingredients, reuse_tip, status
- 3 meals per day: Breakfast, Lunch (lunchbox), Dinner
- Smart meal logic based on energy level:
  - Busy day → quick breakfast + kid lunchbox + order outside for dinner
  - Normal day → all 3 home cooked
- Cross-meal reuse suggestions (e.g. extra chapati reused for lunchbox)
- Accept / Reject per meal — rejected meals never suggested again
- Auto-suggest alternative meal on reject (no page reload)
- Grocery list auto-generated from meal plan

### Sprint 4 — User Profile + Health ✅
- Profile editor in sidebar (read-only view + Edit toggle)
- Fields: name, dietary preference, cuisine preferences, cook time limits, family size
- Health fields: height, weight, age
- BMI auto-calculated and displayed with category (Underweight / Normal / Overweight / Obese)
- BMI passed to Claude — meal suggestions adapt to health goal
- Profile saved to `user_profile.json` — agent picks up changes on next plan generation

### Sprint 5 — Calendar Integration ⏭
- Skipped for demo — using stub meeting data from `sarah_monday.json`
- Production plan: Google Calendar API to read live events and assess daily bandwidth

### Sprint 6 — Adaptive Learning ⏭
- Skipped for demo
- Production plan: track accepted/rejected choices over time, build preference profile per user

### Sprint 7 — Chat Interface ✅
- `chat_agent()` function in `agent.py` — context-aware conversational AI
- Claude receives full context before every message: tasks, meals, meetings, energy, BMI
- Chat is the hero of the main canvas — first thing user sees
- 3 suggested prompt buttons on empty chat for easy demo start
- Auto-generates daily plan when planning intent detected in message
- Plan cards appear below chat after generation
- Persistent chat history within session

### Sprint 8 — Analytics Dashboard ✅
- `DailyLog` model tracks: date, time saved, meals planned, energy level
- `analytics.py` calculates weekly summary
- Analytics section in sidebar shows:
  - Total time saved this week (in hours)
  - Total meals planned
  - Tasks completed
  - Bar chart — time saved per day
  - Meal preference bar — accepted vs rejected ratio

### Sprint 9 — UI Polish ✅
- Full lavender theme (soft purple background, white cards, purple accents)
- App renamed to **HerDay 💜**
- Single page layout with 4 tabs: Tasks, Meals, Grocery, Insights
- Slim sidebar: energy level, meetings (time-aware), done today, shopping list, on the menu
- Chat as hero — main canvas leads with conversation
- 3 suggested prompts: What's in my day / What should I cook / What to buy
- Meetings auto-mark done based on current time
- Sarah appreciated as done count increases
- Grocery items disappear when checked off
- Insights tab: time saved chart, meal favourites, BMI-based food guidance

### Sprint 10 — User Authentication & Data Privacy 🔜
> Addresses hackathon criterion: *"Maintain strict data privacy given the blending of personal, household, and professional information"*

**Plan:**
- `User` table in SQLite — username, sha256-hashed password, all profile fields
- `user_id` column added to `Task`, `Meal`, `DailyLog` — each user sees only their own data
- Login + Register pages shown before main app (`st.stop()` gate)
- Demo account pre-seeded: `revathi / demo123`
- Profile saved to DB per user — no more shared JSON file
- Logout button in sidebar
- All data stays local — nothing sent externally except anonymised context to Claude API

**Files to change:** `models.py`, `database.py`, `crud.py`, `app.py`

---

## Key Features for Hackathon Judges

| Requirement | How Shakti delivers |
|-------------|-------------------|
| Unified cross-domain interface | Work + home tasks in one list; meals + tasks on one page |
| Adaptive preference learning | Accept/reject meals; BMI-aware suggestions; rejected meals never repeated |
| Calendar + schedule integration | Meeting load from stub (live calendar in roadmap) |
| Proactive meal plans + grocery lists | Auto-generated on chat request; no manual input needed |
| Time saved metric | Weekly analytics dashboard with bar chart |
| Proactive over reactive | Chat auto-triggers plan; suggested prompts; agent acts first |
| Energy-aware scheduling | Low energy → quick meals + fewer tasks surfaced |
| Data privacy | Login gate, per-user data isolation by user_id, sha256 password hashing, all data local (Sprint 10) |

---

## Roadmap (Post-Hackathon)

- Google Calendar API integration (Sprint 5)
- Adaptive learning from user behaviour (Sprint 6)
- Push notifications — morning briefing
- Multi-user support with PostgreSQL
- Mobile-responsive UI
- Voice input via Whisper API
