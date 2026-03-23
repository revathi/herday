# Women AI Life-Load Assistant — Product Backlog

## Vision
A unified AI assistant that eliminates the invisible mental load on women by intelligently managing meal planning, grocery tracking, and professional task prioritisation in one adaptive system.

---

## FRONTEND TASKS

### F1 — Unified Dashboard
- [ ] Build a single-screen dashboard combining work tasks, meal plan, and grocery list
- [ ] Add a "Today's Load" summary card (meetings + meals + pending tasks)
- [ ] Show weekly time-saved metric with a simple visual (bar/donut chart)

### F2 — Task Management UI
- [ ] Work task list with priority indicators (High / Medium / Low)
- [ ] Home task list with category tags (Cooking, Cleaning, Errands, etc.)
- [ ] Drag-and-drop to reschedule or reprioritise tasks
- [ ] Manual defer button on each task — user can defer a task themselves
- [ ] Deferred tasks shown in a collapsible section with "Bring Back" option

### F3 — Meal Planning UI
- [ ] Weekly meal plan calendar view (breakfast, lunch, dinner)
- [ ] One-click meal swap for busy days
- [ ] Show estimated prep time per meal

### F4 — Grocery Management UI
- [ ] Auto-generated grocery list from meal plan
- [ ] Checkbox to mark items as bought
- [ ] Group items by category (Dairy, Vegetables, Snacks, etc.)

### F5 — Energy Level Input
- [ ] Daily energy check-in (simple slider or emoji selector: 😴 Low / 😐 Medium / ⚡ High)
- [ ] Display adapted suggestions based on selected energy level

### F6 — Calendar Integration UI
- [ ] Show synced calendar events alongside tasks for the day
- [ ] Visual bandwidth indicator (how busy the day looks)

### F7 — Settings & Privacy
- [ ] User profile setup (dietary preferences, work hours, recurring commitments)
- [ ] Data privacy controls — view, export, or delete personal data
- [ ] Notification preferences

---

## BACKEND TASKS

### B1 — User & Auth
- [ ] User registration and login (email/password + optional Google OAuth)
- [ ] Secure session management
- [ ] Store and retrieve user preferences and history

### B2 — Task Management API
- [ ] CRUD endpoints for work tasks (create, read, update, delete)
- [ ] CRUD endpoints for home/household tasks
- [ ] Tag tasks with domain (work/home), priority, due date, estimated duration

### B3 — Meal Planning API
- [ ] Store meal plans per user per week
- [ ] Endpoint to fetch meal suggestions based on schedule and energy level
- [ ] Track meal history to learn preferences over time

### B4 — Grocery Management API
- [ ] Auto-generate grocery list from selected meal plan
- [ ] CRUD endpoints for grocery items
- [ ] Mark items as purchased; carry over unpurchased items to next week

### B5 — Calendar Integration
- [ ] Connect to Google Calendar API (read events, detect busy slots)
- [ ] Assess daily bandwidth (light / moderate / heavy day) based on calendar
- [ ] Expose bandwidth data to AI layer for proactive suggestions

### B6 — Notification & Reminder Service
- [ ] Send proactive reminders (e.g., "Heavy meeting day — here's a 15-min dinner idea")
- [ ] Daily morning briefing notification (tasks + meals for the day)
- [ ] Configurable reminder timing per user

### B7 — Analytics & Time-Saved Metric
- [ ] Track tasks completed, meals planned, grocery lists generated
- [ ] Calculate estimated weekly time saved (vs. manual planning)
- [ ] Expose data to frontend dashboard

---

## AI TASKS

### A1 — Core AI Agent (Claude-powered)
- [ ] Set up Anthropic Claude API integration
- [ ] Build the central agent that receives user context and generates responses
- [ ] Define agent personality: proactive, empathetic, concise

### A2 — Adaptive Preference Learning
- [ ] Track user choices over time (meals accepted/rejected, task patterns)
- [ ] Build a preference profile per user (favourite meals, peak productivity hours, etc.)
- [ ] Use profile to personalise future suggestions without manual input

### A3 — Intelligent Task Prioritisation
- [ ] AI ranks work tasks by deadline, energy cost, and available time
- [ ] Suggest which tasks to defer on heavy days
- [ ] Rebalance task list dynamically when new events are added to calendar
- [ ] User can manually defer tasks (not just AI-driven deferral)

### A4 — Proactive Meal Planning
- [ ] Generate weekly meal plan based on: schedule, energy forecast, past preferences
- [ ] On heavy meeting days, auto-suggest meals under 15 minutes prep time
- [ ] Avoid repeating meals too frequently (learn rotation preferences)

### A5 — Smart Grocery List Generation
- [ ] Extract ingredients from planned meals automatically
- [ ] Deduplicate and consolidate quantities across meals
- [ ] Suggest add-ons based on season, past purchases, or nutritional balance

### A6 — Natural Language Interface
- [ ] Allow user to talk to the agent in plain English
  - e.g., "I'm exhausted today, help me plan dinner and clear my task list"
  - e.g., "What do I need to buy this week?"
- [ ] Agent responds with actionable output, not just information

### A7 — Energy-Aware Scheduling
- [ ] Correlate calendar load with user energy input
- [ ] Predict energy levels for upcoming days based on schedule patterns
- [ ] Adjust meal complexity and task load suggestions accordingly

### A8 — Privacy-First AI Design
- [ ] All personal data stays server-side; no training on user data externally
- [ ] Summarise data before sending to AI (no raw personal details in prompts)
- [ ] Allow user to reset AI memory / preference profile at any time

---

## SPRINT SUGGESTIONS (Recommended Build Order)

| Sprint | Focus |
|--------|-------|
| Sprint 1 | A1 (Core Agent) + B1 (Auth) + F6 (Basic Dashboard) |
| Sprint 2 | B2 + F2 (Task Management) + A3 (Task Prioritisation) |
| Sprint 3 | B3 + F3 (Meal Planning) + A4 (AI Meal Suggestions) |
| Sprint 4 | B4 + F4 (Grocery List) + A5 (Smart Grocery) |
| Sprint 5 | B5 + F6 (Calendar Sync) + A7 (Energy-Aware Scheduling) |
| Sprint 6 | F5 (Energy Input) + A2 (Preference Learning) + B6 (Notifications) |
| Sprint 7 | B7 + F1 (Dashboard metrics) + A6 (Natural Language) |
| Sprint 8 | F7 (Privacy Settings) + A8 (Privacy-First AI) + Polish |
| Sprint 10 | B1 (User Auth) — Login, Register, per-user data isolation |

---

## Sprint 10 — User Authentication & Data Privacy

> Directly addresses hackathon criterion: *"Maintain strict data privacy, given the blending of personal, household, and professional information"*

### Backend
- [ ] Add `User` model to SQLite — username, password_hash (sha256), name, all profile fields
- [ ] Add `user_id` foreign key to `Task`, `Meal`, `DailyLog` tables
- [ ] `create_user(db, username, password, name, **profile)` — register new user
- [ ] `verify_user(db, username, password)` — login check with hashed password
- [ ] `seed_demo_user(db)` — pre-seed Revathi/Sarah account (`revathi / demo123`)
- [ ] Update all CRUD functions to filter by `user_id` — each user sees only their own data
- [ ] `update_user_profile(db, user_id, **fields)` — save profile to DB instead of JSON

### Frontend
- [ ] Login page — username + password form, shown before main app
- [ ] Register page — name, username, password + basic profile setup
- [ ] Demo hint on login page: *"Try: revathi / demo123"*
- [ ] `st.session_state["user"]` holds logged-in user object
- [ ] `st.stop()` gate — main app blocked until user is authenticated
- [ ] Logout button in sidebar
- [ ] Profile save writes to DB instead of `user_profile.json`

### Privacy Story for Judges
- Every user's tasks, meals, health data and logs are isolated by `user_id`
- Passwords never stored in plain text — sha256 hashed
- All data stays local (SQLite) — nothing sent to external services except anonymised context to Claude API
- Users can register, log in, and their data is theirs alone
