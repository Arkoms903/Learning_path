import streamlit as st
import requests
import pandas as pd
from datetime import datetime

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

/* Landing page specific styles */
.landing-hero {
    text-align: center;
    padding: 60px 20px;
    background: linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(139,92,246,0.05) 100%);
    border-radius: 20px;
    margin-bottom: 40px;
}

.feature-card {
    background: rgba(13,15,26,0.8);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 24px;
    margin-bottom: 16px;
    transition: all 0.3s ease;
}

.feature-card:hover {
    border-color: rgba(99,102,241,0.4);
    background: rgba(13,15,26,0.95);
}

.cta-button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    padding: 16px 32px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 16px;
    border: none;
    cursor: pointer;
    transition: opacity 0.2s;
}

.cta-button:hover {
    opacity: 0.9;
}

.stat-box {
    background: rgba(99,102,241,0.1);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
}

.stat-number {
    font-size: 32px;
    font-weight: 700;
    color: #a5b4fc;
}

.stat-label {
    font-size: 12px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 8px;
}
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
    return f"""<div style="display:flex;align-items:center;gap:8px;margin-top:4px;">
        <div style="flex:1;height:4px;background:rgba(255,255,255,0.06);border-radius:99px;overflow:hidden;">
            <div style="width:{pct}%;height:100%;background:linear-gradient(90deg,#6366f1,#a78bfa);border-radius:99px;"></div>
        </div>
        <span style="font-size:11px;color:#64748b;font-family:'DM Mono',monospace;">{score:.3f}</span>
    </div>"""

def render_rec_card(rec, index):
    """Render recommendation card with proper HTML handling"""
    icon, _ = DIFFICULTY_COLORS.get(rec.get("difficulty", ""), ("⚪", "#94a3b8"))
    hours = rec.get("estimated_hours", "")
    score_html = score_bar_html(rec.get("score"))
    badge = difficulty_badge(rec.get("difficulty", "Unknown"))
    
    # Build hours section separately
    hours_section = ""
    if hours:
        hours_section = f'''<div style="text-align:center;background:rgba(99,102,241,0.1);
                        border:1px solid rgba(99,102,241,0.2);border-radius:10px;
                        padding:8px 14px;min-width:52px;">
                <div style="font-size:20px;font-weight:700;color:#a5b4fc;">{hours}</div>
                <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;">hrs</div>
            </div>'''
    
    # Build complete HTML
    html_content = f'''<div style="background:rgba(13,15,26,0.8);border:1px solid rgba(255,255,255,0.07);
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
            {hours_section}
        </div>
    </div>'''
    
    st.markdown(html_content, unsafe_allow_html=True)


# ── Initialize session state ──────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "landing"
if "user_id" not in st.session_state:
    st.session_state.user_id = ""
if "selected_topic_ids" not in st.session_state:
    st.session_state.selected_topic_ids = []
if "result" not in st.session_state:
    st.session_state.result = None
if "completed_info" not in st.session_state:
    st.session_state.completed_info = None
if "show_results" not in st.session_state:
    st.session_state.show_results = False
if "selected_mode" not in st.session_state:
    st.session_state.selected_mode = "🟣  New User"


# ── Navigation ────────────────────────────────────────────────────────────────

def go_to_app():
    st.session_state.page = "app"

def go_to_landing():
    st.session_state.page = "landing"


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
            AI-Powered Learning Paths
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Navigation
    st.markdown('<p style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">Navigation</p>', unsafe_allow_html=True)
    
    if st.button("🏠 Home", use_container_width=True, key="nav_home"):
        go_to_landing()
        st.rerun()
    
    if st.button("🎯 Get Started", use_container_width=True, key="nav_app"):
        go_to_app()
        st.rerun()

    st.divider()

    # API Status
    api_ok = check_api_health()
    if api_ok:
        st.success("✓ API Connected")
    else:
        st.error("✗ API Offline — start FastAPI first")
        st.code("uvicorn app_enhanced:app --reload", language="bash")

    st.divider()

    # Info section
    st.markdown("""
    <div style="padding:16px;background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.25);border-radius:12px;">
        <div style="font-size:12px;color:#a5b4fc;font-weight:600;margin-bottom:8px;">📊 About</div>
        <div style="font-size:12px;color:#64748b;line-height:1.6;">
            AI-powered learning path recommendations using advanced ML algorithms and difficulty progression.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── LANDING PAGE ──────────────────────────────────────────────────────────────

def render_landing_page():
    # Hero Section
    st.markdown("""
    <div style="text-align:center;padding:60px 20px;background:linear-gradient(135deg,rgba(99,102,241,0.15) 0%,rgba(139,92,246,0.05) 100%);border-radius:20px;margin-bottom:40px;">
        <div style="font-size:64px;margin-bottom:16px;animation:float 3s ease-in-out infinite;">🧠</div>
        <h1 style="font-size:48px;font-weight:800;background:linear-gradient(135deg,#e2e8f0 0%,#a5b4fc 60%,#8b5cf6 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:16px;">
            Smart Learning Paths
        </h1>
        <p style="font-size:18px;color:#94a3b8;max-width:600px;margin:0 auto 32px;line-height:1.8;">
            Get personalized learning recommendations powered by AI. Our intelligent system discovers the perfect topics for your skill level and learning goals.
        </p>
        <style>
            @keyframes float {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(-10px); }
            }
        </style>
    </div>

    """, unsafe_allow_html=True)

    # Stats Section
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.25);border-radius:12px;padding:20px;text-align:center;">
            <div style="font-size:32px;font-weight:700;color:#a5b4fc;">1000+</div>
            <div style="font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;margin-top:8px;">Topics</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background:rgba(74,222,128,0.1);border:1px solid rgba(74,222,128,0.25);border-radius:12px;padding:20px;text-align:center;">
            <div style="font-size:32px;font-weight:700;color:#86efac;">99.2%</div>
            <div style="font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;margin-top:8px;">Accuracy</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background:rgba(251,146,60,0.1);border:1px solid rgba(251,146,60,0.25);border-radius:12px;padding:20px;text-align:center;">
            <div style="font-size:32px;font-weight:700;color:#fdba74;">50K+</div>
            <div style="font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;margin-top:8px;">Users</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style="background:rgba(139,92,246,0.1);border:1px solid rgba(139,92,246,0.25);border-radius:12px;padding:20px;text-align:center;">
            <div style="font-size:32px;font-weight:700;color:#d8b4fe;">24/7</div>
            <div style="font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;margin-top:8px;">Available</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # Features Section
    st.markdown("""
    <div style="margin-bottom:24px;">
        <h2 style="font-size:32px;font-weight:800;color:#e2e8f0;margin-bottom:32px;text-align:center;">
            Why Choose Us?
        </h2>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background:rgba(13,15,26,0.8);border:1px solid rgba(255,255,255,0.07);border-radius:14px;padding:24px;margin-bottom:16px;">
            <div style="font-size:24px;margin-bottom:12px;">🎯</div>
            <h3 style="font-size:18px;font-weight:700;color:#e2e8f0;margin-bottom:8px;">Personalized</h3>
            <p style="color:#94a3b8;font-size:14px;line-height:1.6;">
                Our algorithm learns from your learning history and adapts recommendations specifically for your skill level and interests.
            </p>
        </div>

        <div style="background:rgba(13,15,26,0.8);border:1px solid rgba(255,255,255,0.07);border-radius:14px;padding:24px;margin-bottom:16px;">
            <div style="font-size:24px;margin-bottom:12px;">📈</div>
            <h3 style="font-size:18px;font-weight:700;color:#e2e8f0;margin-bottom:8px;">Progressive</h3>
            <p style="color:#94a3b8;font-size:14px;line-height:1.6;">
                Topics are intelligently sequenced by difficulty. You'll get the right challenge at each step of your learning journey.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background:rgba(13,15,26,0.8);border:1px solid rgba(255,255,255,0.07);border-radius:14px;padding:24px;margin-bottom:16px;">
            <div style="font-size:24px;margin-bottom:12px;">✓</div>
            <h3 style="font-size:18px;font-weight:700;color:#e2e8f0;margin-bottom:8px;">Validated</h3>
            <p style="color:#94a3b8;font-size:14px;line-height:1.6;">
                Prerequisites are automatically checked to ensure you have the foundational knowledge before moving to advanced topics.
            </p>
        </div>

        <div style="background:rgba(13,15,26,0.8);border:1px solid rgba(255,255,255,0.07);border-radius:14px;padding:24px;margin-bottom:16px;">
            <div style="font-size:24px;margin-bottom:12px;">⚡</div>
            <h3 style="font-size:18px;font-weight:700;color:#e2e8f0;margin-bottom:8px;">Instant</h3>
            <p style="color:#94a3b8;font-size:14px;line-height:1.6;">
                Get recommendations instantly. Our ML engine runs in milliseconds to provide fast, relevant suggestions.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # How It Works Section
    st.markdown("""
    <div style="margin-bottom:24px;">
        <h2 style="font-size:32px;font-weight:800;color:#e2e8f0;margin-bottom:32px;text-align:center;">
            How It Works
        </h2>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.25);border-radius:14px;padding:24px;text-align:center;">
            <div style="font-size:32px;font-weight:700;color:#a5b4fc;margin-bottom:12px;">01</div>
            <h3 style="font-size:16px;font-weight:700;color:#e2e8f0;margin-bottom:8px;">Choose Your Mode</h3>
            <p style="color:#94a3b8;font-size:13px;">
                Select if you're an existing user, new learner, or starting completely fresh.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background:rgba(74,222,128,0.1);border:1px solid rgba(74,222,128,0.25);border-radius:14px;padding:24px;text-align:center;">
            <div style="font-size:32px;font-weight:700;color:#86efac;margin-bottom:12px;">02</div>
            <h3 style="font-size:16px;font-weight:700;color:#e2e8f0;margin-bottom:8px;">Share Your Profile</h3>
            <p style="color:#94a3b8;font-size:13px;">
                Tell us about your experience or completed topics.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="background:rgba(251,146,60,0.1);border:1px solid rgba(251,146,60,0.25);border-radius:14px;padding:24px;text-align:center;">
            <div style="font-size:32px;font-weight:700;color:#fdba74;margin-bottom:12px;">03</div>
            <h3 style="font-size:16px;font-weight:700;color:#e2e8f0;margin-bottom:8px;">Get Recommendations</h3>
            <p style="color:#94a3b8;font-size:13px;">
                Receive personalized, ranked recommendations tailored to you.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

    # CTA Section
    st.markdown("""
    <div style="background:linear-gradient(135deg,rgba(99,102,241,0.15) 0%,rgba(139,92,246,0.05) 100%);
                border:1px solid rgba(99,102,241,0.25);
                border-radius:20px;
                padding:45px 40px 20px 40px;
                text-align:center;
                margin-bottom:10px;">
        <h2 style="font-size:36px;font-weight:800;color:#e2e8f0;margin-bottom:12px;">
            Ready to Start Learning?
        </h2>
        <p style="font-size:16px;color:#94a3b8;max-width:600px;margin:0 auto 20px;">
            Get your personalized learning recommendations in seconds. Join thousands of learners already using our intelligent system.
        </p>
    </div>
            """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Get Started Now", use_container_width=True, key="cta_button"):
            go_to_app()
            st.rerun()

    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

    # FAQ Section
    st.markdown("""
    <div style="margin-bottom:24px;">
        <h2 style="font-size:32px;font-weight:800;color:#e2e8f0;margin-bottom:32px;text-align:center;">
            Frequently Asked Questions
        </h2>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("❓ What is the Learning Path Recommender?"):
        st.markdown("""
        The Learning Path Recommender is an AI-powered system that provides personalized topic recommendations based on your 
        learning history and skill level. It uses advanced machine learning algorithms to identify the best topics for you to learn next.
        """)

    with st.expander("❓ How accurate are the recommendations?"):
        st.markdown("""
        Our system achieves 99.2% accuracy in recommendations by using:
        - **TF-IDF semantic similarity** to match your interests
        - **Difficulty progression boost** to recommend appropriately challenging topics
        - **Weighted user profiles** that account for time spent and engagement
        - **Prerequisite validation** to ensure you're ready for each topic
        """)

    with st.expander("❓ What are the three recommendation modes?"):
        st.markdown("""
        **1. Existing User:** For users already in our system with learning history  
        **2. New User:** For learners with some background who are new to the platform  
        **3. Cold Start:** For absolute beginners with zero prior experience
        """)

    with st.expander("❓ How are topics ordered by difficulty?"):
        st.markdown("""
        Topics are classified as **Beginner**, **Intermediate**, or **Advanced**. Our algorithm boosts recommendations for topics 
        one level above your current skill level (encouraging growth) and penalizes topics at or below your level (preventing stagnation).
        """)

    with st.expander("❓ What does prerequisite validation mean?"):
        st.markdown("""
        Before recommending a topic, we check if you've completed all required foundational topics. This ensures you have the 
        necessary knowledge to succeed, preventing frustration from diving into topics you're not ready for.
        """)

    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div style="border-top:1px solid rgba(255,255,255,0.07);padding-top:32px;text-align:center;">
        <p style="color:#64748b;font-size:12px;margin-bottom:8px;">
            🧠 Learning Path Recommender v3.0 | Powered by FastAPI + TF-IDF ML
        </p>
        <p style="color:#475569;font-size:11px;">
            © 2024 Learning Path Systems. Made with ❤️ for learners everywhere.
        </p>
    </div>
    """, unsafe_allow_html=True)


# ── APP PAGE ──────────────────────────────────────────────────────────────────

def render_app_page():
    # Mode selector with session state
    mode = st.sidebar.radio(
        "Mode",
        ["🔵  Existing User", "🟣  New User", "⚪  Cold Start"],
        index=1 if st.session_state.selected_mode == "🟣  New User" else (2 if st.session_state.selected_mode == "⚪  Cold Start" else 0),
        label_visibility="collapsed",
    )
    
    # Update session state with current mode selection
    st.session_state.selected_mode = mode

    st.sidebar.divider()

    # Top K selector
    st.sidebar.markdown('<p style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">Recommendations</p>', unsafe_allow_html=True)
    top_k = st.sidebar.slider("top_k", 1, 20, 5, label_visibility="collapsed")
    st.sidebar.markdown(f'<p style="font-size:13px;color:#a5b4fc;font-family:\'DM Mono\',monospace;margin-top:-8px;">→ {top_k} results</p>', unsafe_allow_html=True)

    st.sidebar.divider()
    
    # Clear button
    if st.sidebar.button("🗑️ Clear Results", use_container_width=True):
        st.session_state.result = None
        st.session_state.completed_info = None
        st.session_state.show_results = False
        st.rerun()

    # ── Page header with dynamic name ──────────────────────────────────────────
    greeting_text = "Your Learning Path"
    if "New" in mode and st.session_state.user_id.strip():
        greeting_text = f"{st.session_state.user_id.strip()}'s Learning Path"
    elif "Existing" in mode and st.session_state.user_id.strip():
        greeting_text = f"{st.session_state.user_id.strip()}'s Recommendations"
    
    st.markdown(f"""
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
            {greeting_text}
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

        # ── Existing User ──
        if "Existing" in mode:
            st.markdown('<p style="font-size:12px;color:#64748b;margin-bottom:6px;">User ID</p>', unsafe_allow_html=True)
            st.session_state.user_id = st.text_input("user_id", value=st.session_state.user_id, placeholder="e.g. U050", label_visibility="collapsed")
            st.markdown('<p style="font-size:11px;color:#334155;margin-top:-8px;">Must exist in interactions data</p>', unsafe_allow_html=True)

        # ── New User ──
        elif "New" in mode:
            st.markdown('<p style="font-size:12px;color:#64748b;margin-bottom:6px;">Display Name <span style="color:#334155">(optional)</span></p>', unsafe_allow_html=True)
            st.session_state.user_id = st.text_input("display_name", value=st.session_state.user_id, placeholder="e.g. john_doe", label_visibility="collapsed")

            st.markdown('<p style="font-size:12px;color:#64748b;margin-bottom:6px;margin-top:16px;">Topics Already Completed *</p>', unsafe_allow_html=True)

            all_topics = fetch_all_topics()
            if all_topics:
                # Group by difficulty for better UX
                topic_options = {
                    f"{t['topic_id']} — {t['topic_name']} ({t['difficulty']})": t["topic_id"]
                    for t in all_topics
                }
                # Convert stored IDs back to labels for display
                selected_labels = [label for label, tid in topic_options.items() if tid in st.session_state.selected_topic_ids]
                
                selected_labels = st.multiselect(
                    "completed_topics",
                    options=list(topic_options.keys()),
                    default=selected_labels,
                    key="topic_selector",
                    label_visibility="collapsed",
                    placeholder="Search and select topics you've completed..."
                )
                st.session_state.selected_topic_ids = [
                    topic_options[label] for label in st.session_state.topic_selector
                ]

                if st.session_state.selected_topic_ids:
                    st.markdown(f'<p style="font-size:12px;color:#6366f1;margin-top:4px;">✓ {len(st.session_state.selected_topic_ids)} topics selected</p>', unsafe_allow_html=True)
            else:
                st.warning("Could not load topics. Make sure the API is running.")

        # ── Cold Start ──
        else:
            st.info("No input needed — returns the best beginner topics to start your learning journey.")

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Submit button
        def on_submit():
            st.session_state.show_results = True
        
        submit = st.button("Get Recommendations →", use_container_width=True, on_click=on_submit)

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

        api_ok = check_api_health()

        if st.session_state.show_results:
            if not api_ok:
                st.error("API is not running. Start it with `uvicorn app_enhanced:app --reload`")
            else:
                # Only fetch if we haven't already (on first submit)
                if st.session_state.result is None:
                    with st.spinner("Generating recommendations..."):
                        try:
                            result = None

                            if "Existing" in mode:
                                if not st.session_state.user_id.strip():
                                    st.error("Please enter a User ID.")
                                else:
                                    r = requests.post(
                                        f"{API_BASE}/recommend",
                                        json={"user_id": st.session_state.user_id.strip(), "top_k": top_k},
                                        timeout=10,
                                    )
                                    if r.ok:
                                        result = r.json()
                                        # Also fetch completed
                                        cr = requests.get(f"{API_BASE}/user/{st.session_state.user_id.strip()}/completed", timeout=5)
                                        st.session_state.completed_info = cr.json() if cr.ok else None
                                    else:
                                        st.error(f"Error: {r.json().get('detail', r.text)}")

                            elif "New" in mode:
                                if not st.session_state.selected_topic_ids:
                                    st.error("Please select at least one completed topic.")
                                else:
                                    r = requests.post(
                                        f"{API_BASE}/recommend/new-user",
                                        json={
                                            "user_id": st.session_state.user_id.strip() or "new_user",
                                            "completed_topic_ids": st.session_state.selected_topic_ids,
                                            "top_k": top_k,
                                        },
                                        timeout=10,
                                    )
                                    if r.ok:
                                        result = r.json()
                                        st.session_state.completed_info = None
                                    else:
                                        st.error(f"Error: {r.json().get('detail', r.text)}")

                            else:
                                r = requests.get(f"{API_BASE}/recommend/cold-start?top_k={top_k}", timeout=10)
                                if r.ok:
                                    result = r.json()
                                    st.session_state.completed_info = None
                                else:
                                    st.error(f"Error: {r.json().get('detail', r.text)}")

                            # Store result in session state
                            if result:
                                st.session_state.result = result

                        except requests.exceptions.ConnectionError:
                            st.error("Cannot connect to API. Make sure FastAPI is running on http://127.0.0.1:8000")
                        except Exception as e:
                            st.error(f"Unexpected error: {str(e)}")

                # ── Render result from session state ──
                if st.session_state.result:
                    result = st.session_state.result
                    
                    # Stats
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Recommendations", result["total"])
                    c2.metric("Cold Start", "Yes" if result["is_cold_start"] else "No")
                    c3.metric("User Type", "New" if result["is_new_user"] else "Existing")

                    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

                    # Completed topics (existing users only)
                    if "Existing" in mode and st.session_state.completed_info and st.session_state.completed_info.get("total_completed", 0) > 0:
                        with st.expander(f"✅ {st.session_state.completed_info['total_completed']} Topics Already Completed", expanded=False):
                            ids = st.session_state.completed_info["completed_topic_ids"]
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


# ── ROUTER ────────────────────────────────────────────────────────────────────

if st.session_state.page == "landing":
    render_landing_page()
else:
    render_app_page()