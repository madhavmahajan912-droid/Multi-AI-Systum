import streamlit as st
import storage
import streamlit as st
import storage
import agents
import os
import json
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="FinVeritas Engine",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="collapsed" # Collapses sidebar by default
)

# ==========================================
# PREMIUM ANIMATED CSS
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
    
    /* Global Typography & Deep Gradient Background */
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at 15% 50%, rgba(20, 25, 40, 1), rgba(10, 12, 16, 1) 100%);
        color: #f8fafc;
    }

    /* COMPLETELY HIDE SIDEBAR & DEFAULT HEADER */
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    header[data-testid="stHeader"] { background: transparent !important; }

    /* Animations */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes glow {
        0% { box-shadow: 0 0 15px rgba(59, 130, 246, 0.2); }
        50% { box-shadow: 0 0 25px rgba(59, 130, 246, 0.4); }
        100% { box-shadow: 0 0 15px rgba(59, 130, 246, 0.2); }
    }

    /* Hero Text Gradient */
    .hero-header {
        background: linear-gradient(90deg, #60a5fa 0%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        margin-top: 2rem;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
        animation: fadeInUp 0.8s ease-out;
    }
    .hero-sub {
        text-align: center;
        color: #94a3b8;
        font-size: 1.2rem;
        margin-bottom: 3rem;
        animation: fadeInUp 1s ease-out;
    }

    /* Premium Glassmorphism Cards with Hover Effects */
    .glass-card {
        background: rgba(20, 25, 35, 0.4);
        border-radius: 16px;
        padding: 30px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        margin-bottom: 25px;
        transition: all 0.4s ease;
        animation: fadeInUp 0.8s ease-out;
    }
    
    .glass-card:hover {
        transform: translateY(-5px);
        border: 1px solid rgba(96, 165, 250, 0.3);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4), 0 0 20px rgba(59, 130, 246, 0.1);
    }

    /* Input Fields Styling */
    .stTextInput input, .stTextArea textarea {
        background: rgba(15, 20, 30, 0.6) !important;
        color: #fff !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 15px !important;
        font-size: 1.05rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #60a5fa !important;
        box-shadow: 0 0 15px rgba(96, 165, 250, 0.2) !important;
    }

    /* Primary Button Animation */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        padding: 10px 20px !important;
        transition: all 0.3s ease !important;
        animation: glow 3s infinite;
    }
    .stButton > button[kind="primary"]:hover {
        transform: scale(1.02);
        filter: brightness(1.1);
    }

    /* Metric Grid Settings */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin: 25px 0;
    }
    .metric-card {
        background: rgba(10, 15, 25, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 25px;
        border-radius: 12px;
        text-align: center;
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: scale(1.05);
    }
    .metric-val {
        font-size: 3.5rem;
        font-weight: 800;
        margin: 10px 0 0 0;
        line-height: 1;
    }

    /* Status Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 8px 16px;
        border-radius: 30px;
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 20px;
    }
    .badge-verified { background: rgba(16, 185, 129, 0.1); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); }
    .badge-rumor { background: rgba(239, 68, 68, 0.1); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.3); }
    .badge-bullish { background: rgba(59, 130, 246, 0.1); color: #60a5fa; border: 1px solid rgba(96, 165, 250, 0.3); }
    .badge-bearish { background: rgba(236, 72, 153, 0.1); color: #f472b6; border: 1px solid rgba(244, 114, 182, 0.3); }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SESSION STATE
# ==========================================
if "api_key" not in st.session_state:
    st.session_state.api_key = os.getenv("GEMINI_API_KEY", "")
if "viewing_archive" not in st.session_state:
    st.session_state.viewing_archive = False

# ==========================================
# MAIN HEADER
# ==========================================
st.markdown("<div class='hero-header'>FinVeritas</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-sub'>Autonomous Multi-Agent Intelligence Network</div>", unsafe_allow_html=True)

# ==========================================
# SETTINGS & ARCHIVE PANEL (Top Expander)
# ==========================================
with st.expander("⚙️ System Configuration & Archives", expanded=not bool(st.session_state.api_key)):
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### Authentication")
        st.session_state.api_key = st.text_input(
            "Gemini API Key", 
            value=st.session_state.api_key, 
            type="password",
            placeholder="Paste your API key here..."
        )
        if st.session_state.api_key:
            st.success("API Key is actively connected.", icon="⚡")
            
    with col2:
        st.markdown("#### Recent Archives")
        archive_data = storage.load_archive()
        if not archive_data:
            st.caption("No reports saved yet.")
        else:
            for entry in archive_data[:3]: # Show top 3
                icon = "📰" if entry["type"] == "fact_check" else "📈"
                if st.button(f"{icon} {entry['query'][:35]}...", key=f"hist_{entry['id']}", use_container_width=True):
                    st.session_state.selected_archive = entry
                    st.session_state.viewing_archive = True
                    st.rerun()
            if st.button("Clear All Archives", type="secondary"):
                # Fast way to clear local JSON for this demo
                with open(storage.ARCHIVE_FILE, 'w') as f: f.write("[]")
                st.rerun()

st.divider()

# ==========================================
# ARCHIVE VIEWER MODE
# ==========================================
if st.session_state.viewing_archive and "selected_archive" in st.session_state:
    entry = st.session_state.selected_archive
    if st.button("← Close Archive & Return to Workspace", type="primary"):
        st.session_state.viewing_archive = False
        del st.session_state.selected_archive
        st.rerun()
        
    st.markdown(f"### 🗄️ Archived Report: {entry['timestamp']}")
    st.json(entry['content']) 
    st.stop()

# ==========================================
# LIVE WORKSPACE (TABS)
# ==========================================
tab1, tab2 = st.tabs(["🔍 Global Fact-Checker", "📊 Market Intelligence"])

# ------------------------------------------
# TAB 1: FACT-CHECKER
# ------------------------------------------
with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    claim_input = st.text_area("Enter a news claim, rumor, or article snippet to verify:", height=120)
    
    if st.button("Deploy Fact-Check Agents", type="primary", use_container_width=True):
        if not st.session_state.api_key:
            st.error("Authentication Error: Please provide an API key in the configuration panel above.")
        elif not claim_input:
            st.warning("Input required to begin analysis.")
        else:
            with st.spinner("Initiating autonomous agents. Searching global networks..."):
                result = agents.run_fact_check(claim_input, st.session_state.api_key)
                
                verdict = result.get("verdict", "Unverified")
                badge_color = "badge-verified" if verdict == "Verified" else "badge-rumor" if verdict == "Rumor/Fake" else "badge-mixed"
                
                st.markdown(f"""
                <div class='glass-card'>
                    <span class='badge {badge_color}'>{verdict}</span>
                    <h2 style='margin-bottom: 20px;'>Verification Analysis</h2>
                    
                    <div class='metric-grid'>
                        <div class='metric-card' style='border-top: 3px solid #34d399;'>
                            <div style='color: #94a3b8; font-size: 0.85rem; font-weight: 700; letter-spacing: 1px;'>AUTHENTICITY</div>
                            <div class='metric-val' style='color: #34d399;'>{result.get('verified_percentage', 0)}%</div>
                        </div>
                        <div class='metric-card' style='border-top: 3px solid #f87171;'>
                            <div style='color: #94a3b8; font-size: 0.85rem; font-weight: 700; letter-spacing: 1px;'>FABRICATION</div>
                            <div class='metric-val' style='color: #f87171;'>{result.get('rumor_percentage', 0)}%</div>
                        </div>
                    </div>
                    
                    <h4 style='margin-top: 30px; color: #cbd5e1;'>Agent Synthesis</h4>
                    <p style='color: #94a3b8; line-height: 1.7; font-size: 1.05rem;'>{result.get('analysis', '')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                storage.save_to_archive("fact_check", claim_input, result, {"verdict": verdict})

# ------------------------------------------
# TAB 2: MARKET INTELLIGENCE
# ------------------------------------------
with tab2:
    st.markdown("<br>", unsafe_allow_html=True)
    market_input = st.text_input("Enter an economic trend, asset, or financial event:")
    
    if st.button("Deploy Financial Agents", type="primary", use_container_width=True):
        if not st.session_state.api_key:
            st.error("Authentication Error: Please provide an API key in the configuration panel above.")
        elif not market_input:
            st.warning("Input required to begin analysis.")
        else:
            with st.spinner("Compiling market sentiment and extracting economic drivers..."):
                result = agents.run_market_analysis(market_input, st.session_state.api_key)
                
                sentiment = result.get("market_sentiment", "Neutral")
                badge_color = "badge-bullish" if sentiment == "Bullish" else "badge-bearish" if sentiment == "Bearish" else "badge-neutral"
                
                st.markdown(f"""
                <div class='glass-card'>
                    <span class='badge {badge_color}'>{sentiment} Trend</span>
                    <h2 style='margin-bottom: 25px;'>Intelligence Report: {result.get('topic', market_input)}</h2>
                    
                    <div style='background: rgba(59, 130, 246, 0.05); border-left: 4px solid #3b82f6; padding: 20px; border-radius: 0 12px 12px 0; margin: 25px 0;'>
                        <h4 style='margin-top: 0; color: #60a5fa;'>💡 Key Strategic Takeaway</h4>
                        <p style='margin-bottom: 0; font-size: 1.1rem; line-height: 1.6;'>{result.get('handy_takeaway', '')}</p>
                    </div>
                    
                    <h4 style='color: #cbd5e1;'>Executive Summary</h4>
                    <p style='color: #94a3b8; line-height: 1.7; font-size: 1.05rem;'>{result.get('summary', '')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                storage.save_to_archive("market_analysis", market_input, result, {"sentiment": sentiment})