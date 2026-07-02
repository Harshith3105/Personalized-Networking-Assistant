import streamlit as st
import httpx
import logging
from typing import List, Dict, Any

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("frontend.app")

# Backend API URL
API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Personalized Networking Assistant",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling using CSS injection
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    /* Global styles */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Gradient Title */
    .title-gradient {
        background: linear-gradient(135deg, #FF6B6B 0%, #4D96FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.8rem !important;
        margin-bottom: 0.5rem;
        letter-spacing: -0.05rem;
    }
    
    .subtitle {
        color: #B2B2B2;
        font-size: 1.15rem;
        font-weight: 300;
        margin-bottom: 2rem;
    }
    
    /* Custom cards for starters */
    .starter-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .starter-card:hover {
        transform: translateY(-2px);
        border-color: #4D96FF;
    }
    
    .starter-text {
        font-size: 1.15rem;
        font-weight: 400;
        line-height: 1.5;
        color: #F3F4F6;
        font-style: italic;
    }
    
    /* Theme badges */
    .theme-badge {
        display: inline-block;
        background: linear-gradient(135deg, #4D96FF 0%, #6BCB77 100%);
        color: #FFFFFF;
        border-radius: 100px;
        padding: 0.25rem 0.8rem;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    .interest-badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.1);
        color: #D1D5DB;
        border-radius: 100px;
        padding: 0.25rem 0.8rem;
        font-size: 0.85rem;
        font-weight: 500;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    
    /* Fact sheet card */
    .fact-card {
        background: rgba(77, 150, 255, 0.08);
        border-left: 5px solid #4D96FF;
        border-radius: 4px 12px 12px 4px;
        padding: 1.5rem;
        margin-top: 1rem;
        margin-bottom: 1.5rem;
    }
    
    .fact-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #4D96FF;
        margin-bottom: 0.5rem;
    }
    
    .fact-summary {
        font-size: 1rem;
        line-height: 1.6;
        color: #E5E7EB;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to query backend api
def call_api(endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> Any:
    url = f"{API_URL}{endpoint}"
    try:
        if method == "POST":
            response = httpx.post(url, json=data, timeout=120.0)  # long timeout for initial model loads
        else:
            response = httpx.get(url, timeout=30.0)
            
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API Error ({response.status_code}): {response.text}")
            st.error(f"API Error ({response.status_code}): {response.json().get('detail', 'Unknown error')}")
            return None
    except httpx.ConnectError:
        st.error("Failed to connect to backend server. Make sure the FastAPI backend is running on http://127.0.0.1:8000")
        return None
    except Exception as e:
        logger.error(f"Network error calling {endpoint}: {e}")
        st.error(f"Network error: {str(e)}")
        return None

# Sidebar Content
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #4D96FF;'>🤝 Assistant Hub</h2>", unsafe_allow_html=True)
    st.write("Welcome to your Personalized Networking Assistant!")
    st.write("This tool uses:")
    st.markdown("- **DistilBERT** for Theme Extraction")
    st.markdown("- **GPT-2** for Starter Generation")
    st.markdown("- **Wikipedia API** for Fact Verification")
    st.markdown("- **JSON storage** for History Logging")
    st.markdown("---")
    
    # Show stats in sidebar
    history_data = call_api("/history")
    if history_data:
        st.markdown("### 📊 Your Activity")
        total_sessions = len(history_data)
        total_starters = sum(len(h.get("starters", [])) for h in history_data)
        
        feedbacks = []
        for h in history_data:
            for s in h.get("starters", []):
                if s.get("feedback"):
                    feedbacks.append(s["feedback"])
                    
        thumbs_up = feedbacks.count("up")
        thumbs_down = feedbacks.count("down")
        
        st.metric(label="Events Analyzed", value=total_sessions)
        st.metric(label="Starters Generated", value=total_starters)
        
        col1, col2 = st.columns(2)
        col1.metric(label="👍 Useful", value=thumbs_up)
        col2.metric(label="👎 Not Useful", value=thumbs_down)

# Header Section
st.markdown("<h1 class='title-gradient'>Personalized Networking Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Generate smart, context-aware conversation starters and fact-check event topics in real-time.</p>", unsafe_allow_html=True)

# Tabs Navigation
tab_starter, tab_fact, tab_history = st.tabs([
    "🤝 Generate Smart Starters",
    "🔍 Quick Fact Verification",
    "📜 Review Past Strategies"
])

# ================= TAB 1: SMART STARTER GENERATOR =================
with tab_starter:
    st.subheader("Scenario 1: Generate Smart Starters")
    
    col_input, col_output = st.columns([1, 1])
    
    with col_input:
        st.markdown("#### **Step 1: Input Event Details**")
        event_desc = st.text_area(
            "Event Description", 
            placeholder="e.g. AI for Sustainable Cities. Discussing the potential of artificial intelligence to optimize urban transport networks, reduce power grids carbon footprints, and manage traffic congestion.",
            height=120,
            value="AI for Sustainable Cities"
        )
        
        interests_input = st.text_input(
            "Your Interests (comma-separated)",
            placeholder="e.g. climate change, urban planning, self-driving cars",
            value="climate change, urban planning"
        )
        
        generate_btn = st.button("🚀 Analyze Event & Generate Starters", use_container_width=True)
        
    with col_output:
        if generate_btn:
            if not event_desc.strip():
                st.warning("Please enter an event description.")
            elif not interests_input.strip():
                st.warning("Please enter at least one interest label.")
            else:
                interests_list = [i.strip() for i in interests_input.split(",") if i.strip()]
                
                with st.spinner("Analyzing event themes using DistilBERT..."):
                    theme_response = call_api("/analyze-event", method="POST", data={
                        "event_description": event_desc,
                        "interests": interests_list
                    })
                
                if theme_response:
                    themes = theme_response.get("themes", [])
                    st.markdown("#### **Step 2: Extracted Themes (DistilBERT)**")
                    
                    badge_html = ""
                    for theme in themes:
                        badge_html += f'<span class="theme-badge">{theme}</span>'
                    for interest in interests_list:
                        if interest not in themes:
                            badge_html += f'<span class="interest-badge">{interest}</span>'
                            
                    st.markdown(badge_html, unsafe_allow_html=True)
                    st.write("")
                    
                    with st.spinner("Generating smart conversation starters using GPT-2..."):
                        starters_response = call_api("/generate-conversation", method="POST", data={
                            "event_description": event_desc,
                            "themes": themes,
                            "interests": interests_list
                        })
                    
                    if starters_response:
                        st.markdown("#### **Step 3: Tailored Conversation Starters**")
                        st.session_state.current_generation = starters_response
                        st.session_state.feedbacks = {} # reset feed
                        
        if "current_generation" in st.session_state:
            gen = st.session_state.current_generation
            st.markdown(f"**Event Context:** *{gen['event_description']}*")
            
            for idx, starter in enumerate(gen.get("starters", [])):
                starter_id = starter["id"]
                st.markdown(f"""
                <div class="starter-card">
                    <p class="starter-text">"{starter['text']}"</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Feedback buttons in Streamlit
                feedback_state = st.session_state.feedbacks.get(starter_id, starter.get("feedback"))
                
                col_up, col_down, col_space = st.columns([0.15, 0.15, 0.7])
                
                up_btn_label = "👍 Useful" if feedback_state != "up" else "👍 Applied"
                down_btn_label = "👎 Not Useful" if feedback_state != "down" else "👎 Flagged"
                
                if col_up.button(up_btn_label, key=f"up_{starter_id}"):
                    call_api("/feedback", method="POST", data={"starter_id": starter_id, "feedback": "up"})
                    st.session_state.feedbacks[starter_id] = "up"
                    st.rerun()
                    
                if col_down.button(down_btn_label, key=f"down_{starter_id}"):
                    call_api("/feedback", method="POST", data={"starter_id": starter_id, "feedback": "down"})
                    st.session_state.feedbacks[starter_id] = "down"
                    st.rerun()
                
                st.markdown("<hr style='margin: 10px 0; border:0; border-top:1px solid rgba(255,255,255,0.05);'/>", unsafe_allow_html=True)

# ================= TAB 2: QUICK FACT VERIFICATION =================
with tab_fact:
    st.subheader("Scenario 2: Quick Fact Verification")
    st.write("Preparing to attend an event? Do a quick query to fetch reliable fact sheets from Wikipedia.")
    
    fact_query = st.text_input(
        "Concept or Topic to Fact-Check",
        placeholder="e.g. blockchain in healthcare, zero-knowledge proofs, smart grid",
        value="blockchain in healthcare"
    )
    
    verify_btn = st.button("🔍 Run Fact Verification", use_container_width=True)
    
    if verify_btn:
        if not fact_query.strip():
            st.warning("Please enter a concept to fact-check.")
        else:
            with st.spinner("Querying Wikipedia API..."):
                fact_response = call_api("/fact-check", method="POST", data={"query": fact_query})
                
            if fact_response:
                if fact_response.get("success"):
                    st.markdown(f"""
                    <div class="fact-card">
                        <div class="fact-title">{fact_response.get('title')}</div>
                        <div class="fact-summary">{fact_response.get('summary')}</div>
                        <br/>
                        <a href="{fact_response.get('url')}" target="_blank" style="color: #4D96FF; text-decoration: underline; font-weight: 600;">Read full Wikipedia Article</a>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(fact_response.get("error", "Failed to retrieve summary from Wikipedia."))

# ================= TAB 3: REVIEW PAST STRATEGIES =================
with tab_history:
    st.subheader("Scenario 3: History & Strategies")
    st.write("Review your previously generated networking prompts. The ones marked 👍 (thumbs up) help keep track of your successful interactions.")
    
    # Reload history from API
    history_logs = call_api("/history")
    
    if not history_logs:
        st.info("No history logs found. Start by generating starters in the first tab!")
    else:
        # Display list of logs
        for entry in history_logs:
            # Format title
            date_parsed = entry.get("timestamp", "").split("T")[0]
            event_title = entry.get("event_description", "")
            if len(event_title) > 60:
                event_title = event_title[:60] + "..."
            
            with st.expander(f"📅 {date_parsed} | Event: {event_title}"):
                st.markdown(f"**Full Event Description:** {entry.get('event_description')}")
                
                # Show badges
                st.markdown("**Themes / Interests:**")
                badges_str = ""
                for theme in entry.get("themes", []):
                    badges_str += f'<span class="theme-badge">{theme}</span>'
                for interest in entry.get("interests", []):
                    if interest not in entry.get("themes", []):
                        badges_str += f'<span class="interest-badge">{interest}</span>'
                st.markdown(badges_str, unsafe_allow_html=True)
                
                st.markdown("**Generated Starters & Feedback:**")
                for s in entry.get("starters", []):
                    fb_icon = "⚪ No feedback"
                    if s.get("feedback") == "up":
                        fb_icon = "👍 Marked Useful"
                    elif s.get("feedback") == "down":
                        fb_icon = "👎 Marked Not Useful"
                        
                    st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.02); padding: 10px; border-radius: 6px; margin-bottom: 5px; border-left: 3px solid rgba(255,255,255,0.2);">
                        <p style="margin: 0; font-style: italic; color: #E5E7EB;">"{s['text']}"</p>
                        <span style="font-size: 0.8rem; color: #9CA3AF;">Status: {fb_icon}</span>
                    </div>
                    """, unsafe_allow_html=True)
