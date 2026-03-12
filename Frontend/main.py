import streamlit as st
import requests
import pandas as pd

API_BASE = "http://127.0.0.1:8000"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Learning Path Recommender",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=DM+Mono&display=swap');

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
}

/* Dark background */
.stApp {
    background: #070910;
    color: #e2e8f0;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0d0f1a !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
}

/* Hide default streamlit header */
#MainMenu, footer{ visibility: hidden; }

/* Metric cards */
[data-testid="metric-container"] {
    background: rgba(13,15,26,0.9);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 16px !important;
}
[data-testid="metric-container"] label {
    color: #64748b !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #a5b4fc !important;
    font-size: 28px !important;
    font-weight: 700 !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 28px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    font-family: 'Outfit', sans-serif !important;
    width: 100%;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* Inputs */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 14px !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: rgba(99,102,241,0.6) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.12) !important;
}

/* Multiselect */
.stMultiSelect > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
}
.stMultiSelect span[data-baseweb="tag"] {
    background: rgba(99,102,241,0.25) !important;
    border: 1px solid rgba(99,102,241,0.4) !important;
    color: #a5b4fc !important;
    border-radius: 6px !important;
}

/* Slider */
.stSlider > div > div > div > div {
    background: #6366f1 !important;
}

/* Radio */
.stRadio > div {
    gap: 8px !important;
}
.stRadio label {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    padding: 10px 16px !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
}
.stRadio label:hover {
    border-color: rgba(99,102,241,0.4) !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: rgba(13,15,26,0.8) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 12px !important;
    color: #94a3b8 !important;
}
.streamlit-expanderContent {
    background: rgba(7,9,16,0.9) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-top: none !important;
}

/* Divider */
hr { border-color: rgba(255,255,255,0.07) !important; }

/* Success / error / info */
.stSuccess { background: rgba(74,222,128,0.08) !important; border: 1px solid rgba(74,222,128,0.25) !important; border-radius: 12px !important; color: #86efac !important; }
.stError   { background: rgba(248,113,113,0.08) !important; border: 1px solid rgba(248,113,113,0.25) !important; border-radius: 12px !important; color: #fca5a5 !important; }
.stInfo    { background: rgba(99,102,241,0.08)  !important; border: 1px solid rgba(99,102,241,0.25)  !important; border-radius: 12px !important; color: #a5b4fc  !important; }
.stWarning { background: rgba(251,191,36,0.08)  !important; border: 1px solid rgba(251,191,36,0.25)  !important; border-radius: 12px !important; color: #fde68a  !important; }

/* DataFrame */
.stDataFrame { border-radius: 14px !important; overflow: hidden; }
[data-testid="stDataFrameResizable"] { background: rgba(13,15,26,0.9) !important; }

/* Spinner */
.stSpinner > div { border-top-color: #6366f1 !important; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

DIFFICULTY_COLORS = {
    "Beginner":     ("🟢", "#4ade80"),
    "Intermediate": ("🟠", "#fb923c"),
    "Advanced":     ("🔴", "#f87171"),
}

@st.cache_data(ttl=300)
def fetch_all_topics():
    try:
        r = requests.get(f"{API_BASE}/topics", timeout=5)
        if r.ok:
            return r.json().get("topics", [])
    except Exception:
        pass
    return []

def check_api_health():
    try:
        r = requests.get(f"{API_BASE}/health", timeout=3)
        return r.ok
    except Exception:
        return False

def difficulty_badge(difficulty):
    icon, _ = DIFFICULTY_COLORS.get(difficulty, ("⚪", "#94a3b8"))
    colors = {"Beginner": "#166534,#dcfce7", "Intermediate": "#7c2d12,#ffedd5", "Advanced": "#7f1d1d,#fee2e2"}
    bg, fg = colors.get(difficulty, "#1e293b,#94a3b8").split(",")
    return f'<span style="background:{bg};color:{fg};padding:2px 10px;border-radius:99px;font-size:12px;font-weight:600;">{icon} {difficulty}</span>'

def score_bar_html(score):
    if score is None:
        return ""
    pct = min(int(score * 500), 100)
    return f"""
    <div style="display:flex;align-items:center;gap:8px;margin-top:4px;">
        <div style="flex:1;height:4px;background:rgba(255,255,255,0.06);border-radius:99px;overflow:hidden;">
            <div style="width:{pct}%;height:100%;background:linear-gradient(90deg,#6366f1,#a78bfa);border-radius:99px;"></div>
        </div>
        <span style="font-size:11px;color:#64748b;font-family:'DM Mono',monospace;">{score:.3f}</span>
    </div>"""

def render_rec_card(rec, index):
    icon, _ = DIFFICULTY_COLORS.get(rec.get("difficulty", ""), ("⚪", "#94a3b8"))
    hours = rec.get("estimated_hours", "")
    score_html = score_bar_html(rec.get("score"))
    badge = difficulty_badge(rec.get("difficulty", "Unknown"))
    st.markdown(f"""
    <div style="background:rgba(13,15,26,0.8);border:1px solid rgba(255,255,255,0.07);
                border-radius:14px;padding:18px 20px;margin-bottom:10px;
                transition:border-color 0.2s;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">
            <div style="flex:1;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                    <span style="font-family:'DM Mono',monospace;font-size:11px;color:#475569;">
                        {rec.get("topic_id","")}
                    </span>
                    {badge}
                </div>
                <div style="font-size:17px;font-weight:700;color:#e2e8f0;font-family:'Outfit',sans-serif;">
                    {rec.get("topic_name","")}
                </div>
                {score_html}
            </div>
            {"" if not hours else f'''
            <div style="text-align:center;background:rgba(99,102,241,0.1);
                        border:1px solid rgba(99,102,241,0.2);border-radius:10px;
                        padding:8px 14px;min-width:52px;">
                <div style="font-size:20px;font-weight:700;color:#a5b4fc;">{hours}</div>
                <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;">hrs</div>
            </div>'''}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    # Logo / title
    st.markdown("""
    <div style="padding:8px 0 24px;">
        <div style="font-size:28px;margin-bottom:6px;">🧠</div>
        <div style="font-size:20px;font-weight:800;color:#e2e8f0;line-height:1.2;">
            Learning Path<br/>Recommender
        </div>
        <div style="font-size:12px;color:#475569;margin-top:6px;">
            ML-Powered · TF-IDF + Cosine Similarity
        </div>
    </div>
    """, unsafe_allow_html=True)

    # API Status
    api_ok = check_api_health()
    if api_ok:
        st.success("✓ API Connected")
    else:
        st.error("✗ API Offline — start FastAPI first")
        st.code("uvicorn app:app --reload", language="bash")

    st.divider()

    # Mode
    st.markdown('<p style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">Mode</p>', unsafe_allow_html=True)
    mode = st.radio(
        "mode",
        ["🔵  Existing User", "🟣  New User", "⚪  Cold Start"],
        label_visibility="collapsed",
    )

    st.divider()

    # Top K
    st.markdown('<p style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">Recommendations</p>', unsafe_allow_html=True)
    top_k = st.slider("top_k", 1, 20, 5, label_visibility="collapsed")
    st.markdown(f'<p style="font-size:13px;color:#a5b4fc;font-family:\'DM Mono\',monospace;margin-top:-8px;">→ {top_k} results</p>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<p style="font-size:11px;color:#334155;text-align:center;">Powered by FastAPI + scikit-learn</p>', unsafe_allow_html=True)


# ── Main layout ───────────────────────────────────────────────────────────────

# Page header
st.markdown("""
<div style="margin-bottom:32px;">
    <div style="display:inline-flex;align-items:center;gap:8px;
                background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.25);
                border-radius:99px;padding:5px 14px;font-size:12px;color:#a5b4fc;
                letter-spacing:0.06em;text-transform:uppercase;margin-bottom:16px;">
        <span style="width:6px;height:6px;border-radius:50%;background:#6366f1;display:inline-block;"></span>
        Personalized Recommendations
    </div>
    <h1 style="font-size:36px;font-weight:800;
               background:linear-gradient(135deg,#e2e8f0 0%,#a5b4fc 60%,#8b5cf6 100%);
               -webkit-background-clip:text;-webkit-text-fill-color:transparent;
               margin-bottom:8px;">
        Your Learning Path
    </h1>
    <p style="color:#475569;font-size:15px;max-width:500px;line-height:1.6;">
        Get AI-powered topic recommendations based on your learning history and prerequisites.
    </p>
</div>
""", unsafe_allow_html=True)

left_col, right_col = st.columns([1, 1.6], gap="large")

# ── LEFT: Input form ──────────────────────────────────────────────────────────
with left_col:
    st.markdown('<p style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:16px;">Configure Request</p>', unsafe_allow_html=True)

    user_id = ""
    selected_topic_ids = []

    # ── Existing User ──
    if "Existing" in mode:
        st.markdown('<p style="font-size:12px;color:#64748b;margin-bottom:6px;">User ID</p>', unsafe_allow_html=True)
        user_id = st.text_input("user_id", placeholder="e.g. U050", label_visibility="collapsed")
        st.markdown('<p style="font-size:11px;color:#334155;margin-top:-8px;">Must exist in interactions data</p>', unsafe_allow_html=True)

    # ── New User ──
    elif "New" in mode:
        st.markdown('<p style="font-size:12px;color:#64748b;margin-bottom:6px;">Display Name <span style="color:#334155">(optional)</span></p>', unsafe_allow_html=True)
        user_id = st.text_input("display_name", placeholder="e.g. john_doe", label_visibility="collapsed")

        st.markdown('<p style="font-size:12px;color:#64748b;margin-bottom:6px;margin-top:16px;">Topics Already Completed *</p>', unsafe_allow_html=True)

        all_topics = fetch_all_topics()
        if all_topics:
            # Group by difficulty for better UX
            topic_options = {
                f"{t['topic_id']} — {t['topic_name']} ({t['difficulty']})": t["topic_id"]
                for t in all_topics
            }
            selected_labels = st.multiselect(
                "completed_topics",
                options=list(topic_options.keys()),
                label_visibility="collapsed",
                placeholder="Search and select topics you've completed...",
            )
            selected_topic_ids = [topic_options[l] for l in selected_labels]

            if selected_topic_ids:
                st.markdown(f'<p style="font-size:12px;color:#6366f1;margin-top:4px;">✓ {len(selected_topic_ids)} topics selected</p>', unsafe_allow_html=True)
        else:
            st.warning("Could not load topics. Make sure the API is running.")

    # ── Cold Start ──
    else:
        st.info("No input needed — returns the best beginner topics to start your learning journey.")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Submit button
    submit = st.button("Get Recommendations →", use_container_width=True)

    # Quick tips
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    with st.expander("💡 Tips", expanded=False):
        st.markdown("""
        <div style="color:#64748b;font-size:13px;line-height:1.8;">
        <b style="color:#94a3b8;">Existing User</b><br/>
        Use IDs like <code style="color:#a5b4fc">U001</code> → <code style="color:#a5b4fc">U050</code>
        from your interactions data.<br/><br/>
        <b style="color:#94a3b8;">New User</b><br/>
        Select topics you've already mastered. The system builds your profile from these
        and finds the best next steps.<br/><br/>
        <b style="color:#94a3b8;">Cold Start</b><br/>
        Perfect for absolute beginners — returns beginner-level topics with no prerequisites.
        </div>
        """, unsafe_allow_html=True)


# ── RIGHT: Results ────────────────────────────────────────────────────────────
with right_col:
    st.markdown('<p style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:16px;">Results</p>', unsafe_allow_html=True)

    if submit:
        if not api_ok:
            st.error("API is not running. Start it with `uvicorn app:app --reload`")
        else:
            with st.spinner("Generating recommendations..."):
                try:
                    result = None

                    if "Existing" in mode:
                        if not user_id.strip():
                            st.error("Please enter a User ID.")
                        else:
                            r = requests.post(
                                f"{API_BASE}/recommend",
                                json={"user_id": user_id.strip(), "top_k": top_k},
                                timeout=10,
                            )
                            if r.ok:
                                result = r.json()
                                # Also fetch completed
                                cr = requests.get(f"{API_BASE}/user/{user_id.strip()}/completed", timeout=5)
                                completed_info = cr.json() if cr.ok else None
                            else:
                                st.error(f"Error: {r.json().get('detail', r.text)}")

                    elif "New" in mode:
                        if not selected_topic_ids:
                            st.error("Please select at least one completed topic.")
                        else:
                            r = requests.post(
                                f"{API_BASE}/recommend/new-user",
                                json={
                                    "user_id": user_id.strip() or "new_user",
                                    "completed_topic_ids": selected_topic_ids,
                                    "top_k": top_k,
                                },
                                timeout=10,
                            )
                            if r.ok:
                                result = r.json()
                                completed_info = None
                            else:
                                st.error(f"Error: {r.json().get('detail', r.text)}")

                    else:
                        r = requests.get(f"{API_BASE}/recommend/cold-start?top_k={top_k}", timeout=10)
                        if r.ok:
                            result = r.json()
                            completed_info = None
                        else:
                            st.error(f"Error: {r.json().get('detail', r.text)}")

                    # ── Render result ──
                    if result:
                        # Stats
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Recommendations", result["total"])
                        c2.metric("Cold Start", "Yes" if result["is_cold_start"] else "No")
                        c3.metric("User Type", "New" if result["is_new_user"] else "Existing")

                        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

                        # Completed topics (existing users only)
                        if "Existing" in mode and completed_info and completed_info.get("total_completed", 0) > 0:
                            with st.expander(f"✅ {completed_info['total_completed']} Topics Already Completed", expanded=False):
                                ids = completed_info["completed_topic_ids"]
                                cols = st.columns(4)
                                for i, tid in enumerate(ids):
                                    cols[i % 4].markdown(
                                        f'<span style="background:rgba(74,222,128,0.08);border:1px solid rgba(74,222,128,0.2);color:#86efac;border-radius:6px;padding:3px 8px;font-size:12px;font-family:\'DM Mono\',monospace;">{tid}</span>',
                                        unsafe_allow_html=True
                                    )

                            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

                        # Recommendation cards
                        for i, rec in enumerate(result["recommendations"]):
                            render_rec_card(rec, i)

                        # Download as CSV
                        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                        df = pd.DataFrame(result["recommendations"])
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="⬇ Download as CSV",
                            data=csv,
                            file_name=f"recommendations_{result['user_id']}.csv",
                            mime="text/csv",
                            use_container_width=True,
                        )

                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to API. Make sure FastAPI is running on http://127.0.0.1:8000")
                except Exception as e:
                    st.error(f"Unexpected error: {str(e)}")

    else:
        # Empty state
        st.markdown("""
        <div style="border:1px dashed rgba(255,255,255,0.07);border-radius:16px;
                    padding:48px 24px;text-align:center;color:#334155;">
            <div style="font-size:40px;margin-bottom:12px;">⟡</div>
            <div style="font-size:15px;font-weight:600;color:#475569;margin-bottom:6px;">
                No recommendations yet
            </div>
            <div style="font-size:13px;line-height:1.6;">
                Fill in the form and click<br/>
                <span style="color:#6366f1;">Get Recommendations →</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Browse all topics section
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        all_topics = fetch_all_topics()
        if all_topics:
            with st.expander("📚 Browse All Topics", expanded=False):
                df_topics = pd.DataFrame(all_topics)
                diff_filter = st.multiselect(
                    "Filter by difficulty",
                    ["Beginner", "Intermediate", "Advanced"],
                    default=["Beginner", "Intermediate", "Advanced"],
                    key="diff_filter",
                )
                filtered = df_topics[df_topics["difficulty"].isin(diff_filter)]
                st.dataframe(
                    filtered[["topic_id", "topic_name", "difficulty", "estimated_hours"]],
                    use_container_width=True,
                    hide_index=True,
                )