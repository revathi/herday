import json
import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def _bmi_context(profile) -> str:
    h = profile.get("height_cm", 0)
    w = profile.get("weight_kg", 0)
    if not h or not w:
        return ""
    bmi = round(w / ((h / 100) ** 2), 1)
    if bmi < 18.5:
        category, advice = "Underweight", "suggest calorie-dense, protein-rich meals"
    elif bmi < 25:
        category, advice = "Normal", "maintain balanced meals with good protein and fibre"
    elif bmi < 30:
        category, advice = "Overweight", "prefer low-carb, high-protein meals and avoid heavy gravies"
    else:
        category, advice = "Obese", "suggest light, low-calorie meals with vegetables and lean protein"
    return f"- BMI: {bmi} ({category}) — {advice}"

def build_prompt(profile, day, work_tasks=None, home_tasks=None, rejected_meals=None):
    meetings = "\n".join([f"  - {m['time']}: {m['title']} ({m['duration_mins']} mins)" for m in day["meetings"]])
    fridge = ", ".join(day["fridge_items"])

    # Use DB tasks if provided, otherwise fall back to JSON stub
    if work_tasks is not None:
        work_str = "\n".join([f"  - [{t.priority.upper()}] {t.title} (due: {t.due_date or 'not set'}, ~{t.est_mins} mins)" for t in work_tasks])
    else:
        work_str = "\n".join([f"  - [{t['priority'].upper()}] {t['title']} (due: {t['due']}, ~{t['estimated_mins']} mins)" for t in day["work_tasks"]])

    if home_tasks is not None:
        home_str = "\n".join([f"  - {t.title} (~{t.est_mins} mins)" for t in home_tasks])
    else:
        home_str = "\n".join([f"  - {t['title']} (~{t['estimated_mins']} mins)" for t in day["home_tasks"]])

    return f"""You are a proactive AI life-load assistant helping {profile['user']} manage her day.

USER PROFILE:
- Dietary preference: {profile['dietary']}
- Cuisine preferences: {', '.join(profile['cuisine_preferences'])}
- Max cook time on busy days: {profile['max_cook_time_busy_day']} minutes
- Family size: {profile['family_size']}
{_bmi_context(profile)}

TODAY'S CONTEXT:
- Energy level: {day['energy_level']}
- Meetings today:
{meetings}
- Work tasks:
{work_str}
- Home tasks:
{home_str}
- Items currently in fridge: {fridge}
{f"- Do NOT suggest these meals (previously rejected): {', '.join(rejected_meals)}" if rejected_meals else ""}

This is an Indian household. Meal planning rules based on energy level:

BUSY DAY (low energy, 4+ meetings):
- Breakfast: quick home cooked Indian meal under {profile['max_cook_time_busy_day']} mins
- Lunch: pack kid's lunchbox using leftovers from breakfast where possible
- Dinner: simple ready-made or minimal-effort Indian meal under {profile['max_cook_time_busy_day']} mins — NO ordering outside

NORMAL DAY (medium/high energy):
- All 3 meals home cooked, under {profile['max_cook_time_normal_day']} mins each
- Suggest cross-meal reuse where possible (e.g. extra chapati from breakfast used for lunch)

IMPORTANT: NEVER suggest ordering outside or delivery. Always suggest a home cooked or ready-made easy recipe.

Today's energy is: {day['energy_level']}

Respond ONLY with valid JSON in this exact format:
{{
  "day_assessment": "one sentence describing how heavy this day is",
  "top_work_tasks": [
    {{"task": "task name", "reason": "why this is top priority"}}
  ],
  "deferred_work_tasks": [
    {{"task": "task name", "reason": "why to defer"}}
  ],
  "meals": {{
    "breakfast": {{
      "name": "meal name",
      "prep_time_mins": 10,
      "ingredients_needed": ["item1"],
      "using_from_fridge": ["item1"],
      "instructions": "brief 2-sentence instructions",
      "reuse_tip": "how this can be reused for lunch or dinner"
    }},
    "lunch": {{
      "type": "lunchbox or home_cooked",
      "name": "meal or lunchbox description",
      "note": "what to pack or prepare",
      "reuse_from": "breakfast or none"
    }},
    "dinner": {{
      "type": "home_cooked",
      "name": "meal name",
      "prep_time_mins": 0,
      "ingredients_needed": [],
      "using_from_fridge": [],
      "instructions": "brief 2-sentence recipe instructions",
      "reuse_tip": ""
    }}
  }},
  "grocery_list": ["item1", "item2"],
  "time_saved_mins": 45,
  "motivational_note": "a short empathetic note for Sarah"
}}

Rules:
- top_work_tasks: max 2 tasks
- all meals must be {profile['dietary']}
- grocery_list: only items NOT already in the fridge
- time_saved_mins: realistic estimate of planning time saved
- reuse_tip: always look for cross-meal ingredient reuse to reduce cooking effort
"""

def run_agent(work_tasks=None, home_tasks=None, rejected_meals=None):
    profile = load_json("data/user_profile.json")
    day = load_json("data/sarah_monday.json")

    prompt = build_prompt(profile, day, work_tasks=work_tasks,
                          home_tasks=home_tasks, rejected_meals=rejected_meals)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)

def suggest_meal(meal_type="dinner", rejected_meals=None):
    """Ask Claude for a single meal suggestion — used when user rejects current meal."""
    profile = load_json("data/user_profile.json")
    day     = load_json("data/sarah_monday.json")
    fridge  = ", ".join(day["fridge_items"])
    rejected_str = f"Do NOT suggest these: {', '.join(rejected_meals)}" if rejected_meals else ""
    is_busy = day["energy_level"] == "low"

    extra = f"Suggest a home cooked or easy ready-made {profile['dietary']} Indian meal under {profile['max_cook_time_busy_day']} mins. Never suggest ordering outside."

    prompt = f"""Suggest one Indian {meal_type} option.
- Dietary: {profile['dietary']}
- Fridge items: {fridge}
- Family size: {profile['family_size']}
{_bmi_context(profile)}
{extra}
{rejected_str}

Respond ONLY with valid JSON:
{{
  "type": "home_cooked or order_outside",
  "name": "meal name",
  "prep_time_mins": 10,
  "ingredients_needed": ["item1"],
  "using_from_fridge": ["item1"],
  "instructions": "recipe or order suggestion",
  "reuse_tip": "how leftovers can be reused"
}}"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

def chat_agent(user_message: str, chat_history: list,
               work_tasks=None, home_tasks=None) -> str:
    """Context-aware chat — Claude knows the full day context before responding."""
    profile = load_json("data/user_profile.json")
    day     = load_json("data/sarah_monday.json")
    fridge  = ", ".join(day["fridge_items"])

    work_str = "\n".join([f"  - [{t.priority.upper()}] {t.title}" for t in (work_tasks or [])])
    home_str = "\n".join([f"  - {t.title}" for t in (home_tasks or [])])

    system_prompt = f"""You are a warm, proactive AI life-load assistant for {profile['user']}.
You help her manage work tasks, home tasks, and meal planning together.

CURRENT CONTEXT:
- Energy level today: {day['energy_level']}
- Meetings today: {len(day['meetings'])} meetings
- Dietary preference: {profile['dietary']}
- BMI context: {_bmi_context(profile)}
- Fridge items: {fridge}
- Active work tasks: {work_str or 'None'}
- Active home tasks: {home_str or 'None'}

Be warm, concise and empathetic — max 3 sentences.
IMPORTANT: Never list out meals, tasks or grocery items in detail in your reply.
If the user asks about meals/tasks/grocery, acknowledge warmly and tell them to check the relevant tab — the details are already there.
If the user seems stressed or tired, acknowledge it in one sentence before advising."""

    messages = chat_history + [{"role": "user", "content": user_message}]

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=system_prompt,
        messages=messages
    )
    return response.content[0].text.strip()

if __name__ == "__main__":
    result = run_agent()
    print(json.dumps(result, indent=2))
