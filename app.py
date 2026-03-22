import base64
import json
import streamlit as st
from database import init_db, SessionLocal
from crud import (get_tasks, add_task, mark_done, seed_tasks,
                  save_meal, get_meals, update_meal_status, get_rejected_meal_names,
                  defer_task, restore_task, delete_task,
                  verify_user, create_user, get_user_by_username,
                  update_user_profile, seed_demo_user)
from agent import run_agent, suggest_meal, chat_agent, load_json
from analytics import log_daily_plan, get_weekly_summary

# ── Init ──────────────────────────────────────────────────────────────────────
init_db()
db = SessionLocal()
seed_demo_user(db)

st.set_page_config(page_title="HerDay — Plan less. Live more.", page_icon="💜", layout="wide")

def _logo_b64():
    with open("logo.png", "rb") as f:
        return base64.b64encode(f.read()).decode()

LOGO_B64 = _logo_b64()

day = load_json("data/sarah_monday.json")

# ── Auth Gate ─────────────────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #f3f0ff; }
    [data-testid="baseButton-primary"] { background-color: #7c3aed !important; border: none !important; color: white !important; border-radius: 10px !important; }
    .stButton > button { border-radius: 8px; border: 1.5px solid #7c3aed; color: #7c3aed; background: white; }
    .stButton > button:hover { background: #7c3aed !important; color: white !important; }
    .hero-panel {
        background: linear-gradient(145deg, #5b21b6, #7c3aed);
        border-radius: 20px; padding: 2.5rem 2rem;
        color: white; height: 100%;
    }
    .hero-title { font-size: 2rem; font-weight: 900; margin-bottom: 0.3rem; }
    .hero-sub { font-size: 1rem; opacity: 0.85; margin-bottom: 2rem; }
    .feature-card {
        background: rgba(255,255,255,0.12);
        border-radius: 12px; padding: 0.9rem 1rem;
        margin-bottom: 0.8rem; display: flex; align-items: flex-start; gap: 0.8rem;
    }
    .feature-icon { font-size: 1.6rem; line-height: 1; }
    .feature-text { font-size: 0.88rem; line-height: 1.4; opacity: 0.95; }
    .feature-label { font-weight: 700; font-size: 0.95rem; }
    .badge-row { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 2rem; }
    .badge { background: rgba(255,255,255,0.2); border-radius: 99px;
             padding: 0.3rem 0.8rem; font-size: 0.75rem; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        st.markdown(f"""
        <div style="text-align:center; margin-bottom:1.5rem;">
            <div style="font-size:2.2rem; font-weight:900; color:#5b21b6;">HerDay 💜</div>
            <div style="color:#6b7280; font-size:0.95rem;">Plan less. Live more.</div>
        </div>
        """, unsafe_allow_html=True)
        login_tab, register_tab = st.tabs(["Sign in", "Create account"])

        with login_tab:
            lu = st.text_input("Username", key="login_user")
            lp = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login", type="primary", use_container_width=True):
                user = verify_user(db, lu.strip(), lp)
                if user:
                    st.session_state["user"] = user
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
            st.caption("Demo account: **revathi** / **demo123**")

        with register_tab:
            rname = st.text_input("Full Name", key="reg_name")
            ru    = st.text_input("Username", key="reg_user")
            rp    = st.text_input("Password", type="password", key="reg_pass")
            rp2   = st.text_input("Confirm Password", type="password", key="reg_pass2")
            if st.button("Register", type="primary", use_container_width=True):
                if not rname or not ru or not rp:
                    st.error("Please fill all fields.")
                elif rp != rp2:
                    st.error("Passwords do not match.")
                elif get_user_by_username(db, ru.strip()):
                    st.error("Username already taken.")
                else:
                    user = create_user(db, username=ru.strip(), password=rp, name=rname)
                    st.session_state["user"] = user
                    st.rerun()
            st.caption("You can set dietary preferences in your profile after login.")

    # Watermark injected last so form renders first
    st.markdown(f"""
    <img src="data:image/png;base64,{LOGO_B64}" style="
        position:fixed; left:-4%; top:50%; transform:translateY(-50%);
        height:55vh; width:auto; opacity:0.22; mix-blend-mode:multiply;
        pointer-events:none; z-index:0;"/>
    """, unsafe_allow_html=True)
    st.stop()

# ── Logged-in user ────────────────────────────────────────────────────────────
user = st.session_state["user"]
seed_tasks(db, user_id=user.id)

# Build profile dict from user object (keeps rest of code compatible)
profile = {
    "user":                    user.name,
    "dietary":                 user.dietary,
    "cuisine_preferences":     json.loads(user.cuisine_preferences),
    "allergies":               json.loads(user.allergies),
    "max_cook_time_busy_day":  user.max_cook_time_busy_day,
    "max_cook_time_normal_day":user.max_cook_time_normal_day,
    "work_hours":              user.work_hours,
    "peak_energy_hours":       user.peak_energy_hours,
    "family_size":             user.family_size,
    "height_cm":               user.height_cm,
    "weight_kg":               user.weight_kg,
    "age":                     user.age,
}

priority_colors = {"high": "🔴", "medium": "🟡", "low": "🟢"}
energy_map      = {"low": "😴 Low", "medium": "😐 Medium", "high": "⚡ High"}

# ── Lavender Theme ────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Global background */
[data-testid="stAppViewContainer"] {
    background-color: #f3f0ff;
}
[data-testid="stSidebar"] {
    background-color: #5b21b6;
    border-right: none;
}
[data-testid="stSidebar"] * {
    color: #ffffff !important;
}
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #ffffff !important;
    font-weight: 800;
    font-size: 1.2rem;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] small {
    color: #e9d5ff !important;
    font-size: 0.85rem;
}
[data-testid="stSidebar"] .stButton > button {
    border: 1.5px solid #e9d5ff !important;
    color: #ffffff !important;
    background: rgba(255,255,255,0.15) !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.25) !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.2) !important;
}
[data-testid="stSidebar"] .streamlit-expanderHeader,
[data-testid="stSidebar"] [data-testid="stExpanderToggleIcon"],
[data-testid="stSidebar"] details summary {
    background: rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
    color: #ffffff !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] {
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 8px !important;
    background: rgba(255,255,255,0.08) !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] > div:last-child {
    background: transparent !important;
}
[data-testid="stSidebar"] details > div,
[data-testid="stSidebar"] [data-testid="stExpanderDetails"] {
    background: transparent !important;
    color: #ffffff !important;
}

/* Cards */
.plan-card {
    background: white;
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
    border: 1px solid #ddd6fe;
    box-shadow: 0 2px 8px rgba(124,58,237,0.06);
}
.card-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    color: #7c3aed;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}

/* Buttons */
.stButton > button {
    border-radius: 8px;
    border: 1.5px solid #7c3aed;
    color: #7c3aed;
    background: white;
    font-weight: 600;
}
.stButton > button:hover {
    background: #7c3aed;
    color: white;
}
[data-testid="baseButton-primary"] > button,
button[kind="primary"] {
    background: #7c3aed !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
}

/* Chat */
[data-testid="stChatInput"] {
    border-radius: 12px;
    border: 2px solid #7c3aed;
}

/* Metrics */
[data-testid="metric-container"] {
    background: white;
    border-radius: 10px;
    padding: 0.5rem 0.8rem;
    border: 1px solid #ddd6fe;
}

/* Header */
.app-header {
    font-size: 1.5rem;
    font-weight: 800;
    color: #5b21b6;
    margin-bottom: 0.1rem;
}
.app-sub {
    font-size: 0.85rem;
    color: #7c3aed;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar — slim: branding + energy + meetings + profile ────────────────────
with st.sidebar:
    st.markdown("### HerDay 💜")
    st.caption(f"Hi, {profile['user']}!")
    st.caption(f"{energy_map.get(day['energy_level'])} energy today")

    st.markdown("---")

    # Split meetings into upcoming vs done by current time
    from datetime import datetime as _dt2
    def _meeting_end_dt(m):
        import re, datetime as _dttm
        t = m["time"].strip().upper().replace(".", "")
        # normalise "9:00am" / "9:00 AM" / "9AM" → always have a space before AM/PM
        t = re.sub(r"(\d)(AM|PM)", r"\1 \2", t)
        for fmt in ("%I:%M %p", "%I %p"):
            try:
                start = _dt2.strptime(t, fmt)
                today = now.date()
                start = start.replace(year=today.year, month=today.month, day=today.day)
                return start + _dttm.timedelta(minutes=m["duration_mins"])
            except ValueError:
                pass
        return None

    now = _dt2.now()
    meetings_done     = [m for m in day["meetings"] if (e := _meeting_end_dt(m)) and now > e]
    meetings_upcoming = [m for m in day["meetings"] if (e := _meeting_end_dt(m)) is None or now <= e]

    if meetings_upcoming:
        with st.expander(f"📅 Meetings Today ({len(meetings_upcoming)} upcoming)"):
            for m in meetings_upcoming:
                st.caption(f"**{m['time']}** — {m['title']}")

    # Done tasks + completed meetings + appreciation
    done_tasks = get_tasks(db, user_id=user.id, done=True)
    total_done = len(done_tasks) + len(meetings_done)

    if meetings_done or done_tasks:
        if total_done >= 7:
            st.success("You're crushing it today! 🌟")
        elif total_done >= 4:
            st.info("Great momentum — keep going!")
        elif total_done >= 1:
            st.caption("Nice start!")

        with st.expander(f"✅ Done Today ({total_done})"):
            for m in meetings_done:
                st.caption(f"~~{m['time']} — {m['title']}~~")
            for t in done_tasks:
                st.caption(f"~~{t.title}~~")

    st.markdown("---")

    # Shopping List
    if "plan" in st.session_state:
        bought = st.session_state.get("bought_items", set())
        grocery = [i for i in st.session_state["plan"].get("grocery_list", []) if i not in bought]
        with st.expander(f"🛒 Shopping List ({len(grocery)} left)"):
            if grocery:
                for item in grocery:
                    st.caption(f"• {item}")
            else:
                st.caption("All picked up!")

    st.markdown("---")

    # On the Menu
    if "plan" in st.session_state:
        meals = st.session_state["plan"].get("meals", {})
        meal_ids = st.session_state.get("latest_meal_ids", {})
        accepted = get_meals(db, user_id=user.id, status="accepted")
        accepted_ids = {m.id for m in accepted}
        icons = {"breakfast": "🌅", "lunch": "☀️", "dinner": "🌙"}
        menu_items = [(mt, meals[mt]) for mt in ["breakfast", "lunch", "dinner"]
                      if mt in meals and meal_ids.get(mt) in accepted_ids]
        if menu_items:
            with st.expander(f"🍽 On the Menu ({len(menu_items)})"):
                for mt, m in menu_items:
                    st.caption(f"{icons[mt]} **{m.get('name', '')}**")
                    if m.get("prep_time_mins"):
                        st.caption(f"⏱ {m['prep_time_mins']} mins")

    st.markdown("---")
    st.markdown("**👤 Profile**")
    h, w = profile.get("height_cm", 0), profile.get("weight_kg", 0)
    if h and w:
        bmi = round(w / ((h / 100) ** 2), 1)
        bmi_label = "Underweight" if bmi < 18.5 else "Normal" if bmi < 25 else "Overweight" if bmi < 30 else "Obese"
        st.caption(f"BMI: {bmi} — {bmi_label}")
    st.caption(f"Diet: {profile['dietary'].capitalize()} | Family: {profile['family_size']}")

    if not st.session_state.get("editing_profile", False):
        if st.button("Edit Profile", type="primary", use_container_width=True):
            st.session_state["editing_profile"] = True
            st.rerun()
    else:
        with st.form("profile_form"):
            name     = st.text_input("Name", value=profile["user"])
            dietary  = st.selectbox("Diet", ["vegetarian", "vegan", "non-vegetarian", "pescatarian"],
                                    index=["vegetarian", "vegan", "non-vegetarian", "pescatarian"].index(profile["dietary"]))
            cuisines = st.text_input("Cuisines", value=", ".join(profile["cuisine_preferences"]))
            c_busy   = st.number_input("Busy cook time (mins)", min_value=5, max_value=60,
                                       value=profile["max_cook_time_busy_day"], step=5)
            c_norm   = st.number_input("Normal cook time (mins)", min_value=15, max_value=120,
                                       value=profile["max_cook_time_normal_day"], step=5)
            fam      = st.number_input("Family size", min_value=1, max_value=10,
                                       value=profile["family_size"], step=1)
            hc1, hc2, hc3 = st.columns(3)
            with hc1:
                ht = st.number_input("Height", min_value=100, max_value=220,
                                     value=profile.get("height_cm", 160), step=1)
            with hc2:
                wt = st.number_input("Weight", min_value=30, max_value=200,
                                     value=profile.get("weight_kg", 65), step=1)
            with hc3:
                age = st.number_input("Age", min_value=10, max_value=100,
                                      value=profile.get("age", 30), step=1)
            s1, s2 = st.columns(2)
            with s1:
                save = st.form_submit_button("Save", type="primary")
            with s2:
                cancel = st.form_submit_button("Cancel")
            if save:
                updated_user = update_user_profile(db, user.id,
                    name=name, dietary=dietary,
                    cuisine_preferences=json.dumps([c.strip() for c in cuisines.split(",") if c.strip()]),
                    max_cook_time_busy_day=c_busy, max_cook_time_normal_day=c_norm,
                    family_size=fam, height_cm=ht, weight_kg=wt, age=age)
                st.session_state["user"] = updated_user
                st.session_state["editing_profile"] = False
                st.success("Saved!")
                st.rerun()
            if cancel:
                st.session_state["editing_profile"] = False
                st.rerun()

# ── Background logo watermark ─────────────────────────────────────────────────
st.markdown(f"""
<style>
.herday-watermark {{
    position: fixed;
    top: 50%;
    left: 62%;
    transform: translate(-50%, -50%);
    width: 650px;
    opacity: 0.13;
    z-index: 0;
    pointer-events: none;
}}
</style>
<img class="herday-watermark" src="data:image/png;base64,{LOGO_B64}"/>
""", unsafe_allow_html=True)

# ── Main Canvas ───────────────────────────────────────────────────────────────
hcol1, hcol2, hcol3 = st.columns([5, 3, 1])
with hcol1:
    st.markdown(f'<div class="app-header">HerDay 💜</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="app-sub">Plan less. Live more. — {day["date"]}</div>', unsafe_allow_html=True)
with hcol2:
    pass
with hcol3:
    if st.button("Log out", key="logout_top"):
        st.session_state.clear()
        st.rerun()

# ── Chat — Hero ───────────────────────────────────────────────────────────────
pcol1, pcol2, pcol3 = st.columns(3)
prompts = [
    ("What's in my day", "What tasks and meetings do I have today? Give me a quick overview of what's on my plate."),
    ("What should I cook",  "What should I cook today given my fridge items and energy level?"),
    ("What to buy",         "What groceries do I need to buy today based on my fridge items?"),
]
for col, (label, message) in zip([pcol1, pcol2, pcol3], prompts):
    with col:
        if st.button(label, use_container_width=True):
            st.session_state["pending_input"] = message
            st.rerun()

user_input = st.chat_input("Ask HerDay anything about your day...")
if not user_input and st.session_state.get("pending_input"):
    user_input = st.session_state.pop("pending_input")

if user_input:
    try:
        with st.spinner("Thinking..."):
            work_tasks = get_tasks(db, user_id=user.id, domain="work")
            home_tasks = get_tasks(db, user_id=user.id, domain="home")
            reply = chat_agent(user_message=user_input, chat_history=[],
                               work_tasks=work_tasks, home_tasks=home_tasks)
        st.session_state["last_reply"] = reply
    except Exception:
        st.session_state["last_reply"] = "I'm having trouble connecting right now. Please check your internet and try again."
        st.rerun()
    # Detect intent and set active tab
    msg = user_input.lower()
    if any(k in msg for k in ["grocery", "groceries", "shop", "buy", "ingredients"]):
        st.session_state["active_tab"] = 2   # Grocery tab (check before meal — "buy" is more specific)
    elif any(k in msg for k in ["meal", "cook", "breakfast", "lunch", "dinner", "eat", "food"]):
        st.session_state["active_tab"] = 1   # Meals tab
    elif any(k in msg for k in ["insight", "analytics", "time saved", "progress"]):
        st.session_state["active_tab"] = 3   # Insights tab
    else:
        st.session_state["active_tab"] = 0   # Tasks tab (default)

    planning_keywords = ["plan my day", "plan my", "schedule", "help me priorit", "tired", "exhausted",
                         "busy", "what should i cook", "dinner", "breakfast", "lunch"]
    is_grocery_intent = st.session_state.get("active_tab") == 2
    if not is_grocery_intent and any(kw in msg for kw in planning_keywords):
        with st.spinner("Generating your plan..."):
            try:
                rejected = get_rejected_meal_names(db, user_id=user.id)
                plan = run_agent(work_tasks=work_tasks, home_tasks=home_tasks, rejected_meals=rejected)
                st.session_state["plan"] = plan
                meals_data = plan.get("meals", {})
                saved_ids = {}
                for mtype in ["breakfast", "lunch", "dinner"]:
                    m = meals_data.get(mtype, {})
                    saved = save_meal(db, user_id=user.id, meal_type=mtype,
                                     name=m.get("name", mtype.capitalize()),
                                     prep_time_mins=m.get("prep_time_mins", 0),
                                     instructions=m.get("instructions", m.get("note", "")),
                                     ingredients=m.get("ingredients_needed", []),
                                     reuse_tip=m.get("reuse_tip", ""))
                    saved_ids[mtype] = saved.id
                st.session_state["latest_meal_ids"] = saved_ids
                log_daily_plan(db, time_saved_mins=plan.get("time_saved_mins", 45),
                               energy_level=day["energy_level"], meals_planned=3)
            except Exception as e:
                st.error(f"Error: {e}")
    st.rerun()

if st.session_state.get("last_reply"):
    st.info(f"💜 {st.session_state['last_reply']}")

st.markdown("---")

# ── Top Nav Tabs ──────────────────────────────────────────────────────────────
domain_icons = {"work": "💼", "home": "🏠"}
active_tab = st.session_state.get("active_tab", 0)
tab1, tab2, tab3, tab4 = st.tabs(["📋 Tasks", "🍽 Meals", "🛒 Grocery", "📊 Insights"])
# Inject JS to auto-click the right tab
if active_tab > 0:
    tab_js = f"""
    <script>
    setTimeout(function() {{
        const tabs = window.parent.document.querySelectorAll('[data-testid="stTab"]');
        if (tabs.length > {active_tab}) {{ tabs[{active_tab}].click(); }}
    }}, 300);
    </script>
    """
    st.components.v1.html(tab_js, height=0)

# ── Tab 1: Tasks ──────────────────────────────────────────────────────────────
with tab1:
    sound = st.session_state.pop("play_sound", None)
    if sound == "done":
        st.toast("Task done! 💜")
        st.components.v1.html("""
        <style>
        @keyframes rise {
            0%   { transform: translateY(0) scale(1);   opacity: 1; }
            100% { transform: translateY(-95vh) scale(0.6); opacity: 0; }
        }
        .balloon {
            position: fixed; bottom: 10px;
            width: 36px; height: 44px; border-radius: 50%;
            animation: rise 3s ease-in forwards;
            z-index: 9999;
        }
        .balloon::after {
            content: '';
            position: absolute; bottom: -12px; left: 50%;
            transform: translateX(-50%);
            width: 1px; height: 14px;
            background: rgba(0,0,0,0.25);
        }
        </style>
        <script>
        var colors = ['#f472b6','#a78bfa','#34d399','#fb923c','#60a5fa','#fbbf24','#e879f9'];
        for(var i=0;i<7;i++){
            var b=document.createElement('div');
            b.className='balloon';
            b.style.background=colors[i];
            b.style.left=(10+i*13)+'%';
            b.style.animationDelay=(i*0.18)+'s';
            document.body.appendChild(b);
            setTimeout(function(el){document.body.removeChild(el)},3500,b);
        }
        var c=new AudioContext(),notes=[523,659,784,1047];
        notes.forEach(function(f,i){var o=c.createOscillator(),g=c.createGain();
        o.connect(g);g.connect(c.destination);o.frequency.value=f;
        g.gain.setValueAtTime(0.2,c.currentTime+i*0.08);
        g.gain.exponentialRampToValueAtTime(0.001,c.currentTime+i*0.08+0.12);
        o.start(c.currentTime+i*0.08);o.stop(c.currentTime+i*0.08+0.12);});
        </script>""", height=0)
    elif sound == "defer":
        st.toast("Task deferred to tomorrow 📌")
        st.markdown("""<script>
        var c=new AudioContext(),o=c.createOscillator(),g=c.createGain();
        o.connect(g);g.connect(c.destination);o.frequency.value=400;
        o.frequency.linearRampToValueAtTime(280,c.currentTime+0.18);
        g.gain.setValueAtTime(0.2,c.currentTime);
        g.gain.exponentialRampToValueAtTime(0.001,c.currentTime+0.25);
        o.start(c.currentTime);o.stop(c.currentTime+0.25);
        </script>""", unsafe_allow_html=True)

    # ── AI Day Summary (when plan exists) ─────────────────────────────────────
    if "plan" in st.session_state:
        plan = st.session_state["plan"]
        st.info(f"**{plan['day_assessment']}**  ·  ⏱ ~{plan['time_saved_mins']} mins of planning saved")

    # ── Build unified item list: meetings + work tasks + home tasks ────────────
    # Meetings from stub — sorted by clock time, split into upcoming vs done
    import re as _re, datetime as _dttm2
    from datetime import datetime as _dt
    _now = _dt.now()

    def _meeting_end(m):
        t = m["time"].strip().upper().replace(".", "")
        t = _re.sub(r"(\d)(AM|PM)", r"\1 \2", t)
        for fmt in ("%I:%M %p", "%I %p"):
            try:
                start = _dt.strptime(t, fmt).replace(
                    year=_now.year, month=_now.month, day=_now.day)
                return start + _dttm2.timedelta(minutes=m["duration_mins"])
            except ValueError:
                pass
        return None

    def _meeting_sort_key(m):
        e = _meeting_end(m)
        return e if e else _dt.max

    all_meetings_sorted = sorted(day["meetings"], key=_meeting_sort_key)
    meetings_upcoming_tab = [m for m in all_meetings_sorted if (e := _meeting_end(m)) is None or _now <= e]
    meetings_done_tab     = [m for m in all_meetings_sorted if (e := _meeting_end(m)) is not None and _now > e]

    # AI priority order: top tasks first, then rest, deferred last
    ai_top_titles = []
    ai_deferred_titles = []
    if "plan" in st.session_state:
        plan = st.session_state["plan"]
        ai_top_titles    = [t["task"].strip().lower() for t in plan.get("top_work_tasks", [])]
        ai_deferred_titles = [t["task"].strip().lower() for t in plan.get("deferred_work_tasks", [])]

    def task_sort_key(t):
        title_lower = t.title.strip().lower()
        if title_lower in ai_top_titles:
            return (0, {"high": 0, "medium": 1, "low": 2}.get(t.priority, 1))
        if title_lower in ai_deferred_titles:
            return (2, {"high": 0, "medium": 1, "low": 2}.get(t.priority, 1))
        return (1, {"high": 0, "medium": 1, "low": 2}.get(t.priority, 1))

    work_tasks_all = get_tasks(db, user_id=user.id, domain="work")
    home_tasks_all = get_tasks(db, user_id=user.id, domain="home")
    all_active_tasks = sorted(work_tasks_all + home_tasks_all, key=task_sort_key)

    # ── Unified view ──────────────────────────────────────────────────────────
    st.markdown("#### Today's Full Load")

    # Meetings block — upcoming only; done ones shown collapsed below
    if meetings_upcoming_tab:
        st.markdown("**📅 Upcoming Meetings**")
        for m in meetings_upcoming_tab:
            st.markdown(
                f'<div class="plan-card" style="padding:0.7rem 1rem; margin-bottom:0.5rem;">'
                f'<span style="color:#7c3aed;font-weight:700;">{m["time"]}</span> &nbsp; {m["title"]} '
                f'<span style="color:#9ca3af;font-size:0.8rem;">({m["duration_mins"]} mins)</span>'
                f'</div>', unsafe_allow_html=True
            )
    if meetings_done_tab:
        with st.expander(f"✅ Meetings Done ({len(meetings_done_tab)})"):
            for m in meetings_done_tab:
                st.markdown(
                    f'<span style="color:#9ca3af;text-decoration:line-through;">'
                    f'{m["time"]} — {m["title"]}</span>', unsafe_allow_html=True
                )

    # Tasks block
    if all_active_tasks:
        st.markdown("**✅ Tasks**")
        # Show AI focus badge on top tasks
        top_set = set(ai_top_titles)
        for task in all_active_tasks:
            icon = domain_icons[task.domain]
            is_top = task.title.strip().lower() in top_set
            badge = ' <span style="background:#7c3aed;color:white;font-size:0.65rem;padding:1px 6px;border-radius:99px;">AI FOCUS</span>' if is_top else ""
            c1, c2, c3, c4 = st.columns([5, 1, 1, 1])
            with c1:
                st.markdown(
                    f'{priority_colors[task.priority]} {icon} **{task.title}**{badge}',
                    unsafe_allow_html=True
                )
                detail = f"Due: {task.due_date}" if task.due_date else task.category or "General"
                st.caption(f"{detail} · {task.est_mins} mins")
            with c2:
                if st.button("Done", key=f"done_{task.id}"):
                    mark_done(db, task.id)
                    st.session_state["play_sound"] = "done"
                    st.rerun()
            with c3:
                if st.button("Defer", key=f"defer_{task.id}"):
                    defer_task(db, task.id)
                    st.session_state["play_sound"] = "defer"
                    st.rerun()
            with c4:
                if st.button("✕", key=f"del_{task.id}", help="Remove task"):
                    delete_task(db, task.id)
                    st.rerun()
    else:
        st.caption("No active tasks — you're all clear!")

    # Deferred tasks
    all_deferred = get_tasks(db, user_id=user.id, domain="work", deferred=True) + get_tasks(db, user_id=user.id, domain="home", deferred=True)
    if all_deferred:
        with st.expander(f"📌 Deferred ({len(all_deferred)}) — can wait"):
            for task in all_deferred:
                c1, c2 = st.columns([8, 2])
                with c1:
                    st.write(f"{domain_icons[task.domain]} **{task.title}**")
                    # Show AI reason if available
                    if "plan" in st.session_state:
                        for dt in st.session_state["plan"].get("deferred_work_tasks", []):
                            if dt["task"].strip().lower() == task.title.strip().lower():
                                st.caption(f"Why deferred: {dt['reason']}")
                with c2:
                    if st.button("Bring Back", key=f"restore_{task.id}"):
                        restore_task(db, task.id)
                        st.rerun()

    with st.expander("+ Add Task"):
        with st.form("add_task"):
            tc1, tc2 = st.columns(2)
            with tc1:
                title  = st.text_input("Title")
                domain = st.selectbox("Type", ["work", "home"])
            with tc2:
                priority = st.selectbox("Priority", ["high", "medium", "low"])
                est_mins = st.number_input("Est. mins", min_value=5, value=30, step=5)
            due_date = st.text_input("Due date", placeholder="e.g. today, this week")
            category = st.selectbox("Category", ["", "Cooking", "Cleaning", "Errands", "Personal", "Other"])
            if st.form_submit_button("Add Task", type="primary"):
                if title:
                    add_task(db, user_id=user.id, title=title, domain=domain, priority=priority,
                             due_date=due_date, category=category, est_mins=est_mins)
                    st.success("Added!")
                    st.rerun()

# ── Tab 2: Meals ──────────────────────────────────────────────────────────────
with tab2:
    meal_sound = st.session_state.pop("meal_sound", None)
    if meal_sound == "accept":
        st.toast("Added to your menu! 🍽")
        st.markdown("""<script>
        var c=new AudioContext(),o=c.createOscillator(),g=c.createGain();
        o.connect(g);g.connect(c.destination);o.frequency.value=880;
        g.gain.setValueAtTime(0.25,c.currentTime);
        g.gain.exponentialRampToValueAtTime(0.001,c.currentTime+0.2);
        o.start(c.currentTime);o.stop(c.currentTime+0.2);
        </script>""", unsafe_allow_html=True)
    elif meal_sound == "reject":
        st.toast("Finding something better... 🔄")
        st.markdown("""<script>
        var c=new AudioContext(),o=c.createOscillator(),g=c.createGain();
        o.connect(g);g.connect(c.destination);
        o.frequency.value=500;
        o.frequency.linearRampToValueAtTime(300,c.currentTime+0.18);
        g.gain.setValueAtTime(0.2,c.currentTime);
        g.gain.exponentialRampToValueAtTime(0.001,c.currentTime+0.25);
        o.start(c.currentTime);o.stop(c.currentTime+0.25);
        </script>""", unsafe_allow_html=True)

    if "plan" in st.session_state:
        plan = st.session_state["plan"]
        meals_data = plan.get("meals", {})
        meal_ids   = st.session_state.get("latest_meal_ids", {})
        icons      = {"breakfast": "🌅", "lunch": "☀️", "dinner": "🌙"}
        labels     = {"breakfast": "Breakfast", "lunch": "Lunch", "dinner": "Dinner"}
        bcol1, bcol2, bcol3 = st.columns(3)
        meal_cols = {"breakfast": bcol1, "lunch": bcol2, "dinner": bcol3}

        for mtype in ["breakfast", "lunch", "dinner"]:
            m = meals_data.get(mtype, {})
            meal_id = meal_ids.get(mtype)
            with meal_cols[mtype]:
                st.markdown(f"**{icons[mtype]} {labels[mtype]}**")
                st.markdown(f"**{m.get('name', '—')}**")
                prep = m.get("prep_time_mins", 0)
                if prep:
                    st.caption(f"⏱ Prep: {prep} mins")
                st.write(m.get("instructions", m.get("note", "")))
                if m.get("reuse_tip"):
                    st.info(f"♻️ {m['reuse_tip']}")
                if meal_id:
                    accepted_set = {m.id for m in get_meals(db, user_id=user.id, status="accepted")}
                    is_accepted  = meal_id in accepted_set
                    r1, r2 = st.columns(2)
                    with r1:
                        if is_accepted:
                            st.markdown("✅ **Accepted**")
                        else:
                            if st.button("Accept", key=f"accept_{mtype}"):
                                update_meal_status(db, meal_id, "accepted")
                                fridge = [i.lower() for i in day["fridge_items"]]
                                all_ing = []
                                for mt2 in ["breakfast", "lunch", "dinner"]:
                                    all_ing.extend(st.session_state["plan"]["meals"].get(mt2, {}).get("ingredients_needed", []))
                                st.session_state["plan"]["grocery_list"] = list(dict.fromkeys(
                                    [i for i in all_ing if not any(f in i.lower() for f in fridge)]
                                ))
                                st.session_state["meal_sound"] = "accept"
                                st.rerun()
                    with r2:
                        if st.button("Reject", key=f"reject_{mtype}"):
                            update_meal_status(db, meal_id, "rejected")
                            st.session_state["meal_sound"] = "reject"
                            with st.spinner("Finding alternative..."):
                                rejected = get_rejected_meal_names(db, user_id=user.id)
                                new_m = suggest_meal(meal_type=mtype, rejected_meals=rejected)
                                new_saved = save_meal(db, user_id=user.id, meal_type=mtype,
                                                      name=new_m.get("name", mtype),
                                                      prep_time_mins=new_m.get("prep_time_mins", 0),
                                                      instructions=new_m.get("instructions", new_m.get("note", "")),
                                                      ingredients=new_m.get("ingredients_needed", []),
                                                      reuse_tip=new_m.get("reuse_tip", ""))
                                st.session_state["plan"]["meals"][mtype] = new_m
                                st.session_state["latest_meal_ids"][mtype] = new_saved.id
                                # Rebuild grocery list from all current meal ingredients minus fridge
                                fridge = [i.lower() for i in day["fridge_items"]]
                                all_ingredients = []
                                for mt in ["breakfast", "lunch", "dinner"]:
                                    meal_data = st.session_state["plan"]["meals"].get(mt, {})
                                    all_ingredients.extend(meal_data.get("ingredients_needed", []))
                                new_grocery = [i for i in all_ingredients
                                               if not any(f in i.lower() for f in fridge)]
                                st.session_state["plan"]["grocery_list"] = list(dict.fromkeys(new_grocery))
                            st.rerun()
        st.caption(f"*{plan.get('motivational_note', '')}*")
    else:
        st.info("💜 Ask HerDay to plan your meals — type in the chat above!")

# ── Tab 3: Grocery ────────────────────────────────────────────────────────────
with tab3:
    if "plan" in st.session_state:
        plan = st.session_state["plan"]
        st.markdown("#### 🛒 Today's Grocery List")
        if "bought_items" not in st.session_state:
            st.session_state["bought_items"] = set()
        remaining = [i for i in plan["grocery_list"] if i not in st.session_state["bought_items"]]
        if remaining:
            for item in remaining:
                if st.checkbox(item, key=f"grocery_{item}"):
                    st.session_state["bought_items"].add(item)
                    st.rerun()
        else:
            st.success("All done — everything's been picked up!")
    else:
        st.info("💜 Ask HerDay to plan your meals first to generate a grocery list!")

# ── Tab 4: Insights ───────────────────────────────────────────────────────────
with tab4:
    summary = get_weekly_summary(db)
    hrs = round(summary['total_time_saved'] / 60, 1)

    # Big metrics
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("⏱ Time Saved This Week", f"{hrs} hrs")
    with m2:
        st.metric("🍽 Meals Planned", summary["total_meals"])
    with m3:
        st.metric("✅ Tasks Done", summary["tasks_done"])

    st.markdown("---")

    # Bar chart
    st.markdown("**Mental load saved — daily (mins)**")
    st.bar_chart({l: v for l, v in zip(summary["labels"], summary["time_saved"])})

    st.markdown("---")

    # Meal acceptance
    a, r = summary["meals_accepted"], summary["meals_rejected"]
    total = a + r if (a + r) > 0 else 1
    st.markdown("**Meal hit rate**")
    st.progress(a / total, text=f"✅ Accepted: {a}  |  ❌ Rejected: {r}")

    st.markdown("---")

    # Week in review — plain text summary
    st.markdown("**Week in Review**")
    best_day_idx = summary["time_saved"].index(max(summary["time_saved"])) if any(summary["time_saved"]) else 0
    best_day = summary["labels"][best_day_idx]
    st.markdown(
        f"This week HerDay saved {profile['user']} **{hrs} hours** of mental planning across 7 days. "
        f"Her most productive day was **{best_day}**. "
        f"She planned **{summary['total_meals']} meals** and got **{summary['tasks_done']} tasks** done. "
        f"That's {hrs} hours she got back for herself and her family. 💜"
    )

    st.markdown("---")

    # Meal Favourites
    accepted_meals = get_meals(db, user_id=user.id, status="accepted")
    if accepted_meals:
        st.markdown("**⭐ Meal Favourites**")
        seen = {}
        for m in accepted_meals:
            seen[m.name] = seen.get(m.name, 0) + 1
        top_meals = sorted(seen.items(), key=lambda x: x[1], reverse=True)[:5]
        for name, count in top_meals:
            st.caption(f"• {name} {'⭐' * min(count, 3)}")
    else:
        st.markdown("**⭐ Meal Favourites**")
        st.caption("Accept some meals to build your favourites list.")

    st.markdown("---")

    # BMI-based food guidance
    h, w = profile.get("height_cm", 0), profile.get("weight_kg", 0)
    if h and w:
        bmi = round(w / ((h / 100) ** 2), 1)
        st.markdown("**🥗 Eat Smart — Based on Your BMI**")
        if bmi < 18.5:
            avoid = ["Skipping meals", "Low-calorie crash diets", "Excess tea/coffee without food"]
            prefer = ["Nuts & seeds", "Whole grains", "Protein-rich dals & eggs"]
            note = f"BMI {bmi} — Underweight. Focus on nutrient-dense meals."
        elif bmi < 25:
            avoid = ["Processed snacks", "Sugary drinks"]
            prefer = ["Balanced Indian thali", "Seasonal vegetables", "Curd & fruits"]
            note = f"BMI {bmi} — Normal. Keep up the great balance!"
        elif bmi < 30:
            avoid = ["Deep fried snacks (pakoda, puri)", "White rice in excess", "Sugary desserts", "Maida-based foods"]
            prefer = ["Millets & whole grains", "Steamed/grilled dishes", "High-fibre sabzis", "Curd instead of cream"]
            note = f"BMI {bmi} — Overweight. Small swaps make a big difference."
        else:
            avoid = ["Fried foods", "Refined carbs", "Sugary drinks", "Large dinner portions"]
            prefer = ["Vegetable-heavy meals", "Lean proteins", "Small frequent meals", "Soups & salads"]
            note = f"BMI {bmi} — High. HerDay is already suggesting lighter meals for you."

        st.caption(note)
        ic1, ic2 = st.columns(2)
        with ic1:
            st.markdown("**Avoid**")
            for item in avoid:
                st.caption(f"🚫 {item}")
        with ic2:
            st.markdown("**Prefer**")
            for item in prefer:
                st.caption(f"✅ {item}")
