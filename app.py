import streamlit as st
import storage
import agents
import os

# Set page configuration with a premium financial/analytics theme
st.set_page_config(
    page_title="Boost your knowledge - Multi-Agent Analytics",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# PREMIUM CUSTOM CSS INJECTION
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Space+Grotesk:wght@400;600&display=swap');
    
    /* Global Overrides */
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Header fonts */
    h1, h2, h3, .metric-label {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
    }
    
    /* Main Background styling */
    .main {
        background: linear-gradient(135deg, #0e1117 0%, #161a24 100%);
        color: #e2e8f0;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0b0d13;
        border-right: 1px solid #1f2937;
    }
    
    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 16px;
        padding: 24px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        margin-bottom: 20px;
    }
    
    /* Status Badge styling */
    .badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 100px;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 10px;
    }
    
    .badge-verified {
        background-color: rgba(16, 185, 129, 0.2);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }
    
    .badge-rumor {
        background-color: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.4);
    }
    
    .badge-mixed {
        background-color: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.4);
    }
    
    .badge-unverified {
        background-color: rgba(156, 163, 175, 0.2);
        color: #9ca3af;
        border: 1px solid rgba(156, 163, 175, 0.4);
    }
    
    .badge-bullish {
        background-color: rgba(59, 130, 246, 0.2);
        color: #3b82f6;
        border: 1px solid rgba(59, 130, 246, 0.4);
    }
    
    .badge-bearish {
        background-color: rgba(236, 72, 153, 0.2);
        color: #ec4899;
        border: 1px solid rgba(236, 72, 153, 0.4);
    }
    
    /* Metric Score Displays */
    .metric-container {
        display: flex;
        justify-content: space-around;
        align-items: center;
        margin: 20px 0;
    }
    
    .metric-box {
        text-align: center;
        padding: 15px;
        border-radius: 12px;
        min-width: 120px;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        font-family: 'Space Grotesk', sans-serif;
    }
    
    /* Takeaway highlight box */
    .takeaway-box {
        background: linear-gradient(90deg, rgba(59, 130, 246, 0.15) 0%, rgba(147, 51, 234, 0.15) 100%);
        border-left: 5px solid #3b82f6;
        padding: 18px;
        border-radius: 0 12px 12px 0;
        margin: 15px 0;
        font-size: 1.1rem;
        font-style: italic;
        line-height: 1.6;
        color: #e2e8f0;
    }
    
    /* Trigger Cards inside expander */
    .trigger-item {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
    }
    
    .trigger-title {
        font-weight: 600;
        color: #60a5fa;
        font-size: 0.95rem;
    }
    
    /* Sources Link Styling */
    .source-link {
        display: inline-flex;
        align-items: center;
        padding: 4px 8px;
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.05);
        color: #60a5fa !important;
        text-decoration: none;
        font-size: 0.85rem;
        margin-right: 8px;
        margin-bottom: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: background 0.2s ease;
    }
    .source-link:hover {
        background: rgba(96, 165, 250, 0.15);
    }
    
    /* Smooth Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .animate-fade {
        animation: fadeIn 0.5s ease forwards;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
# Try to load API key from local .env file if it exists
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    key, val = line.split("=", 1)
                    if key.strip() == "GEMINI_API_KEY":
                        # Strip potential quotes around key
                        clean_val = val.strip().strip("'").strip('"')
                        os.environ["GEMINI_API_KEY"] = clean_val
    except Exception as e:
        pass

if "api_key" not in st.session_state:
    # Try fetching from environment first (which may have been populated by .env)
    st.session_state.api_key = os.environ.get("GEMINI_API_KEY", "")
if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0


# ==========================================
# SIDEBAR: SETUP & ARCHIVE ARCHITECTURE
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/nolan/128/artificial-intelligence.png", width=70)
    st.title("FinVeritas Engine")
    st.write("A Premium Multi-Agent Platform for News Veracity & Financial Market Analysis.")
    st.markdown("---")
    
    # Secure API Key Setup
    api_key_input = st.text_input(
        "Gemini API Key", 
        value=st.session_state.api_key, 
        type="password",
        help="Get your key from Google AI Studio: https://aistudio.google.com/"
    )
    if api_key_input:
        st.session_state.api_key = api_key_input
        
    if not st.session_state.api_key:
        st.warning("⚠️ Please provide a Gemini API Key to enable the intelligence agents.")
    else:
        st.success("🔑 API Key configured and active.")
        
    st.markdown("---")
    st.subheader("📚 Handy Archive")
    st.write("Archived outputs from previous research:")
    
    # Reload button for archive
    if st.button("🔄 Refresh Archive"):
        st.rerun()
        
    archive_data = storage.load_archive()
    
    if not archive_data:
        st.info("No saved runs found in the archive yet.")
    else:
        for entry in archive_data:
            entry_type = "📰 News" if entry["type"] == "fact_check" else "📈 Market"
            btn_label = f"{entry_type} | {entry['timestamp']}\n{entry['query'][:35]}..."
            
            col1, col2 = st.columns([8, 2])
            with col1:
                # Store selection in session_state to display in detail
                if st.button(btn_label, key=f"view_{entry['id']}", use_container_width=True):
                    st.session_state.selected_archive = entry
            with col2:
                if st.button("🗑️", key=f"del_{entry['id']}", help="Delete from archive"):
                    storage.delete_from_archive(entry["id"])
                    if "selected_archive" in st.session_state and st.session_state.selected_archive["id"] == entry["id"]:
                        del st.session_state.selected_archive
                    st.toast("Report removed from archive.")
                    st.rerun()

# ==========================================
# MAIN DASHBOARD LAYOUT
# ==========================================

# Header Banner
st.markdown("""
<div class='glass-card' style='padding: 20px; background: linear-gradient(135deg, rgba(31, 41, 55, 0.4) 0%, rgba(17, 24, 39, 0.4) 100%); margin-bottom: 25px;'>
    <h1 style='margin: 0; font-size: 2.2rem; color: #60a5fa;'>🤖 FinVeritas Multi-Agent System</h1>
    <p style='margin: 5px 0 0 0; color: #9ca3af; font-size: 1.1rem;'>
        Fact-checks news credibility and analyzes financial and stock market trends using specialized cooperative web agents.
    </p>
</div>
""", unsafe_allow_html=True)

# If an archive item was clicked, display it in a special overlay
if "selected_archive" in st.session_state:
    entry = st.session_state.selected_archive
    st.markdown(f"### 📂 Displaying Archived Report ({entry['timestamp']})")
    
    if st.button("⬅️ Back to Workspace", type="primary"):
        del st.session_state.selected_archive
        st.rerun()
        
    st.markdown("---")
    
    if entry["type"] == "fact_check":
        content = entry["content"]
        verdict = content.get("verdict", "Unverified")
        
        # Color mapping for verdict
        badge_cls = "badge-verified" if verdict == "Verified" else "badge-rumor" if verdict == "Rumor/Fake" else "badge-mixed" if verdict == "Mixed" else "badge-unverified"
        
        st.markdown(f"""
        <div class='glass-card animate-fade'>
            <div class='badge {badge_cls}'>{verdict}</div>
            <h2 style='margin-top: 5px;'>News Claim Check: "{entry['query']}"</h2>
            <div class='metric-container'>
                <div class='metric-box' style='background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2);'>
                    <div class='metric-label' style='color: #10b981;'>Verified Score</div>
                    <div class='metric-value' style='color: #10b981;'>{content.get('verified_percentage', 0)}%</div>
                </div>
                <div class='metric-box' style='background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2);'>
                    <div class='metric-label' style='color: #ef4444;'>Rumor/Fake Score</div>
                    <div class='metric-value' style='color: #ef4444;'>{content.get('rumor_percentage', 0)}%</div>
                </div>
            </div>
            <div style='margin-top: 15px;'>
                <h3>📰 Rumor Details</h3>
                <p>{content.get('rumor_details', 'No rumor details specified.')}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("📝 Detailed Agent Analysis")
        st.markdown(content.get("analysis", ""))
        
        st.subheader("🔗 Sources Used for Verification")
        if content.get("sources"):
            for src in content["sources"]:
                st.markdown(f'<a href="{src["url"]}" target="_blank" class="source-link">🔗 {src["title"]}</a>', unsafe_allow_html=True)
        else:
            st.write("No sources cited.")
            
    else: # Market analysis
        content = entry["content"]
        sentiment = content.get("market_sentiment", "Neutral")
        
        badge_cls = "badge-bullish" if sentiment == "Bullish" else "badge-bearish" if sentiment == "Bearish" else "badge-mixed" if sentiment == "Highly Volatile" else "badge-unverified"
        
        st.markdown(f"""
        <div class='glass-card animate-fade'>
            <div class='badge {badge_cls}'>{sentiment} Sentiment</div>
            <h2 style='margin-top: 5px;'>Stock & Financial Intelligence: "{entry['query']}"</h2>
            <div class='takeaway-box'>
                💡 <b>Handy Takeaway:</b> {content.get('handy_takeaway', '')}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("📊 Key Market Triggers & Drivers")
        if content.get("key_triggers"):
            for item in content["key_triggers"]:
                st.markdown(f"""
                <div class='trigger-item'>
                    <div class='trigger-title'>⚡ {item.get('trigger', '')}</div>
                    <div style='color: #cbd5e1; font-size: 0.9rem; margin-top: 4px;'>{item.get('description', '')}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.write("No specific market triggers extracted.")
            
        st.subheader("📝 Detailed Analysis")
        st.markdown(content.get("summary", ""))
        
        st.subheader("🔗 Scraped Financial Sources")
        if content.get("sources"):
            for src in content["sources"]:
                st.markdown(f'<a href="{src["url"]}" target="_blank" class="source-link">🔗 {src["title"]}</a>', unsafe_allow_html=True)
        else:
            st.write("No sources cited.")
            
    st.stop() # Stop running regular tabs when displaying archive

# ==========================================
# WORKSPACE TABS
# ==========================================
tab1, tab2 = st.tabs(["📰 News Fact-Checker", "📈 Stock Market Intelligence"])

# ------------------------------------------
# TAB 1: NEWS FACT-CHECKER
# ------------------------------------------
with tab1:
    st.header("📰 News Credibility & Rumor Checker")
    st.write("Input any news article or claim below. Our collaborative Search, Scraper, and Fact-Checking agents will verify it against authentic news platforms and calculate a veracity breakdown.")
    
    claim_input = st.text_area(
        "Enter the news claim or paragraph to verify:", 
        placeholder="Example: The government has announced that it will downgrade the currency by 15% overnight and freeze all cash withdrawals.",
        height=100
    )
    
    if st.button("🔍 Run Fact-Checking Agents", type="primary"):
        if not st.session_state.api_key:
            st.error("Please configure your Gemini API Key in the sidebar first.")
        elif not claim_input.strip():
            st.warning("Please enter a claim to verify.")
        else:
            # Multi-agent simulation flow
            status_container = st.empty()
            
            with status_container.container():
                st.info("🔄 **Initializing Agent Team...**")
                
            try:
                # Step 1
                with status_container.container():
                    st.info("🧠 **[Fact-Checking Agent]** Formulating search queries and fact validation plan...")
                
                # We trigger the agent code
                with st.spinner("Analyzing claim & scraping web sources..."):
                    result = agents.run_fact_check(claim_input, st.session_state.api_key)
                
                status_container.empty()
                
                # Display Results
                verdict = result.get("verdict", "Unverified")
                badge_cls = "badge-verified" if verdict == "Verified" else "badge-rumor" if verdict == "Rumor/Fake" else "badge-mixed" if verdict == "Mixed" else "badge-unverified"
                
                st.success("✅ Analysis completed successfully!")
                
                # Visual Verdict & Scores Card
                st.markdown(f"""
                <div class='glass-card animate-fade'>
                    <div class='badge {badge_cls}'>{verdict}</div>
                    <h3 style='margin-top: 5px;'>Verdict: News is classified as <b>{verdict}</b></h3>
                    
                    <div class='metric-container'>
                        <div class='metric-box' style='background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2);'>
                            <div class='metric-label' style='color: #10b981;'>Verified Score</div>
                            <div class='metric-value' style='color: #10b981;'>{result.get('verified_percentage', 0)}%</div>
                        </div>
                        <div class='metric-box' style='background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2);'>
                            <div class='metric-label' style='color: #ef4444;'>Rumor/Fake Score</div>
                            <div class='metric-value' style='color: #ef4444;'>{result.get('rumor_percentage', 0)}%</div>
                        </div>
                    </div>
                    
                    <div style='margin-top: 15px;'>
                        <h4>📰 Rumor Aspect</h4>
                        <p>{result.get('rumor_details', 'No rumor details specified.')}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Detailed Analysis
                st.subheader("📝 Agent Detailed Analysis & Cross-Referencing")
                st.markdown(result.get("analysis", ""))
                
                # Sources
                st.subheader("🔗 Reference Sources Scraped")
                if result.get("sources"):
                    for src in result["sources"]:
                        st.markdown(f'<a href="{src["url"]}" target="_blank" class="source-link">🔗 {src["title"]}</a>', unsafe_allow_html=True)
                else:
                    st.write("No external source urls provided.")
                    
                # Save button
                if st.button("💾 Save to Handy Archive", key="save_fact_check"):
                    storage.save_to_archive("fact_check", claim_input, result, {"verdict": verdict})
                    st.toast("💾 Analysis saved to Handy Archive!")
                    
            except Exception as e:
                status_container.empty()
                st.error(f"Error running agents: {str(e)}")

# ------------------------------------------
# TAB 2: STOCK MARKET INTELLIGENCE
# ------------------------------------------
with tab2:
    st.header("📈 Stock Market & Financial Intelligence")
    st.write("Ask our specialized financial agent to search the web, scrape key economic papers/market data, extract main drivers, and give you a short, handy summary.")
    
    market_input = st.text_input(
        "Enter financial topic / question:",
        value="Why is the Indian Rupee downgrading and what is the market view?",
        placeholder="Example: Why is the Indian Rupee downgrading? OR Tesla stock analysis OR Nifty 50 market trends"
    )
    
    if st.button("🚀 Analyze Market Intelligence", type="primary"):
        if not st.session_state.api_key:
            st.error("Please configure your Gemini API Key in the sidebar first.")
        elif not market_input.strip():
            st.warning("Please enter a financial topic to analyze.")
        else:
            status_container = st.empty()
            
            with status_container.container():
                st.info("🔄 **Deploying Financial Research Agents...**")
                
            try:
                # Step 1
                with status_container.container():
                    st.info("🧠 **[Financial Analyst Agent]** Defining search metrics (Rupee status, inflation, outflows)...")
                
                with st.spinner("Gathering market intelligence and analyzing trends..."):
                    result = agents.run_market_analysis(market_input, st.session_state.api_key)
                
                status_container.empty()
                
                # Display Results
                sentiment = result.get("market_sentiment", "Neutral")
                badge_cls = "badge-bullish" if sentiment == "Bullish" else "badge-bearish" if sentiment == "Bearish" else "badge-mixed" if sentiment == "Highly Volatile" else "badge-unverified"
                
                st.success("✅ Market report generated successfully!")
                
                # Visually striking header card
                st.markdown(f"""
                <div class='glass-card animate-fade'>
                    <div class='badge {badge_cls}'>{sentiment} Sentiment</div>
                    <h3 style='margin-top: 5px;'>Financial Topic: "{result.get('topic', market_input)}"</h3>
                    
                    <div class='takeaway-box'>
                        💡 <b>Handy Takeaway (Keep for Others):</b><br/>
                        {result.get('handy_takeaway', '')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Triggers / Drivers
                st.subheader("📊 Key Market Drivers & Triggers")
                if result.get("key_triggers"):
                    for item in result["key_triggers"]:
                        st.markdown(f"""
                        <div class='trigger-item'>
                            <div class='trigger-title'>⚡ {item.get('trigger', '')}</div>
                            <div style='color: #cbd5e1; font-size: 0.9rem; margin-top: 4px;'>{item.get('description', '')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.write("No specific economic drivers extracted.")
                    
                # Full report summary
                st.subheader("📝 Full Economic Analysis & Synthesis")
                st.markdown(result.get("summary", ""))
                
                # Sources
                st.subheader("🔗 Scraped Financial News Sources")
                if result.get("sources"):
                    for src in result["sources"]:
                        st.markdown(f'<a href="{src["url"]}" target="_blank" class="source-link">🔗 {src["title"]}</a>', unsafe_allow_html=True)
                else:
                    st.write("No external source urls provided.")
                    
                # Save button
                if st.button("💾 Save to Handy Archive", key="save_market_analysis"):
                    storage.save_to_archive("market_analysis", market_input, result, {"sentiment": sentiment})
                    st.toast("💾 Market report saved to Handy Archive!")
                    
            except Exception as e:
                status_container.empty()
                st.error(f"Error running agents: {str(e)}")
