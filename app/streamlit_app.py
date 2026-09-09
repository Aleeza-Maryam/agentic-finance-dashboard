
"""
Market Intelligence Dashboard
Professional Financial Analysis Platform
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import sys
import os
import re
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agentic_finance_dashboard.tools import get_stock_data_with_indicators, search_stock_news
from src.agentic_finance_dashboard.config import GROQ_API_KEY
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
# Page Configuration
st.set_page_config(
    page_title="Market Intelligence Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'symbol' not in st.session_state:
    st.session_state.symbol = "AAPL"
if 'analyzed' not in st.session_state:
    st.session_state.analyzed = False

# CSS - Professional Dashboard Design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: #0a0a12;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(15, 15, 30, 0.98);
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    
    section[data-testid="stSidebar"] .stSelectbox > div > div {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
    }
    
    /* Header */
    .dashboard-header {
        background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 100%);
        padding: 1.2rem 2rem;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.06);
        margin-bottom: 1.5rem;
    }
    
    .dashboard-title {
        font-size: 1.6rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    .dashboard-subtitle {
        color: rgba(255,255,255,0.4);
        font-size: 0.85rem;
        margin: 0;
    }
    
    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        background: #00d4aa;
        border-radius: 50%;
        margin-right: 6px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
    
    /* Metric Cards */
    .metric-card {
        background: rgba(255,255,255,0.02);
        border-radius: 10px;
        padding: 1rem 1.2rem;
        border: 1px solid rgba(255,255,255,0.05);
        transition: all 0.3s ease;
        animation: slideUp 0.5s ease;
        animation-fill-mode: both;
    }
    
    .metric-card:hover {
        background: rgba(255,255,255,0.04);
        border-color: rgba(255,255,255,0.1);
        transform: translateY(-2px);
    }
    
    .metric-label {
        color: rgba(255,255,255,0.4);
        font-size: 0.7rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        color: #ffffff;
        font-size: 1.4rem;
        font-weight: 600;
        margin: 0.15rem 0;
    }
    
    .metric-change-positive {
        color: #00d4aa;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .metric-change-negative {
        color: #ff6b6b;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    /* Recommendation Badges */
    .badge-buy {
        display: inline-block;
        background: rgba(0, 212, 170, 0.15);
        color: #00d4aa;
        padding: 0.3rem 1rem;
        border-radius: 16px;
        font-weight: 600;
        font-size: 0.8rem;
        border: 1px solid rgba(0, 212, 170, 0.2);
    }
    
    .badge-hold {
        display: inline-block;
        background: rgba(255, 193, 7, 0.15);
        color: #ffc107;
        padding: 0.3rem 1rem;
        border-radius: 16px;
        font-weight: 600;
        font-size: 0.8rem;
        border: 1px solid rgba(255, 193, 7, 0.2);
    }
    
    .badge-sell {
        display: inline-block;
        background: rgba(255, 107, 107, 0.15);
        color: #ff6b6b;
        padding: 0.3rem 1rem;
        border-radius: 16px;
        font-weight: 600;
        font-size: 0.8rem;
        border: 1px solid rgba(255, 107, 107, 0.2);
    }
    
    /* Analysis Card */
    .analysis-card {
        background: rgba(255,255,255,0.02);
        border-radius: 10px;
        padding: 1.5rem;
        border: 1px solid rgba(255,255,255,0.06);
        animation: slideUp 0.6s ease;
        line-height: 1.8;
        color: rgba(255,255,255,0.85);
    }
    
    .analysis-card strong {
        color: #00b4ff;
    }
    
    .analysis-card hr {
        border-color: rgba(255,255,255,0.06);
    }
    
    /* News Cards */
    .news-card {
        background: rgba(255,255,255,0.02);
        border-radius: 8px;
        padding: 0.8rem 1rem;
        border: 1px solid rgba(255,255,255,0.05);
        transition: all 0.3s ease;
        margin-bottom: 0.5rem;
        animation: slideUp 0.5s ease;
        animation-fill-mode: both;
    }
    
    .news-card:hover {
        background: rgba(255,255,255,0.04);
        border-color: rgba(255,255,255,0.08);
    }
    
    .news-title {
        color: #ffffff;
        font-size: 0.9rem;
        font-weight: 500;
        margin-bottom: 0.2rem;
    }
    
    .news-snippet {
        color: rgba(255,255,255,0.5);
        font-size: 0.8rem;
    }
    
    .news-source {
        color: rgba(255,255,255,0.25);
        font-size: 0.7rem;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00b4ff 0%, #0077ff 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 119, 255, 0.3);
    }
    
    /* Quick buttons in sidebar */
    .quick-btn {
        background: rgba(255,255,255,0.05) !important;
        color: rgba(255,255,255,0.7) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 6px !important;
        padding: 0.3rem 0 !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    
    .quick-btn:hover {
        background: rgba(255,255,255,0.1) !important;
        color: #ffffff !important;
        border-color: rgba(0, 180, 255, 0.3) !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background: rgba(255,255,255,0.02);
        border-radius: 8px;
        padding: 0.2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        padding: 0.4rem 1rem;
        color: rgba(255,255,255,0.4);
        font-weight: 500;
        font-size: 0.85rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(255,255,255,0.06) !important;
        color: #ffffff !important;
    }
    
    /* Inputs */
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
        padding: 0.5rem 1rem !important;
        font-size: 1rem !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #00b4ff !important;
        box-shadow: 0 0 0 2px rgba(0, 180, 255, 0.15) !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        color: rgba(255,255,255,0.5) !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
    }
    
    /* Footer */
    .footer {
        margin-top: 2.5rem;
        padding: 1rem 0;
        border-top: 1px solid rgba(255,255,255,0.04);
        color: rgba(255,255,255,0.15);
        font-size: 0.7rem;
        text-align: center;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes slideUp {
        from { 
            opacity: 0;
            transform: translateY(20px);
        }
        to { 
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Loading spinner */
    .stSpinner > div {
        border-color: #00b4ff !important;
    }
    
    /* Welcome Screen */
    .welcome-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 4rem 2rem;
        text-align: center;
    }
    
    .welcome-box {
        background: rgba(255,255,255,0.02);
        border-radius: 16px;
        padding: 3rem;
        max-width: 600px;
        border: 1px solid rgba(255,255,255,0.05);
        animation: fadeIn 0.8s ease;
    }
    
    .welcome-title {
        color: rgba(255,255,255,0.6);
        font-size: 2rem;
        font-weight: 300;
        margin: 0;
    }
    
    .welcome-title-main {
        color: #ffffff;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0.2rem 0;
    }
    
    .welcome-text {
        color: rgba(255,255,255,0.4);
        font-size: 1rem;
        margin: 1rem 0;
    }
    
    .welcome-tag {
        background: rgba(255,255,255,0.05);
        padding: 0.3rem 0.8rem;
        border-radius: 4px;
        color: rgba(255,255,255,0.3);
        font-size: 0.8rem;
        display: inline-block;
        margin: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# LLM Initialization
# ============================================================================

@st.cache_resource
def get_llm():
    try:
        return ChatGroq(
            model="qwen/qwen3.8-27b",
            api_key=GROQ_API_KEY,
            temperature=0.3,
            max_tokens=512,
        )
    except Exception as e:
        st.error(f"LLM initialization error: {str(e)}")
        return None

# ============================================================================
# Chart Functions
# ============================================================================

def create_candlestick_chart(candles, symbol):
    if not candles or len(candles) < 2:
        return None
    
    try:
        df = pd.DataFrame(candles)
        df['date'] = pd.to_datetime(df['date'])
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.dropna()
        
        if len(df) < 2:
            return None
        
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.04,
            row_heights=[0.7, 0.3],
            subplot_titles=(f"{symbol} - Price Action", "Volume")
        )
        
        fig.add_trace(
            go.Candlestick(
                x=df['date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name="Price",
                increasing_line_color="#00d4aa",
                decreasing_line_color="#ff6b6b",
                line=dict(width=1),
            ),
            row=1, col=1
        )
        
        if len(df) >= 20:
            df['MA20'] = df['close'].rolling(window=20).mean()
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=df['MA20'],
                    name="MA20",
                    line=dict(color="rgba(0, 180, 255, 0.5)", width=1.5),
                ),
                row=1, col=1
            )
        
        if len(df) >= 50:
            df['MA50'] = df['close'].rolling(window=50).mean()
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=df['MA50'],
                    name="MA50",
                    line=dict(color="rgba(255, 193, 7, 0.5)", width=1.5),
                ),
                row=1, col=1
            )
        
        colors = ['#00d4aa' if close >= open_ else '#ff6b6b' 
                  for close, open_ in zip(df['close'], df['open'])]
        
        fig.add_trace(
            go.Bar(
                x=df['date'],
                y=df['volume'],
                name="Volume",
                marker_color=colors,
                opacity=0.6,
                showlegend=False,
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            template="plotly_dark",
            height=480,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color="rgba(255,255,255,0.5)", size=11),
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_rangeslider_visible=False,
            hovermode='x unified',
            margin=dict(l=20, r=20, t=40, b=20),
        )
        
        fig.update_xaxes(
            gridcolor="rgba(255,255,255,0.04)",
            tickfont=dict(color="rgba(255,255,255,0.3)", size=10),
            showgrid=True,
        )
        
        fig.update_yaxes(
            gridcolor="rgba(255,255,255,0.04)",
            tickfont=dict(color="rgba(255,255,255,0.3)", size=10),
            showgrid=True,
            row=1, col=1
        )
        
        fig.update_yaxes(
            gridcolor="rgba(255,255,255,0.04)",
            tickfont=dict(color="rgba(255,255,255,0.3)", size=10),
            showgrid=True,
            row=2, col=1
        )
        
        return fig
        
    except Exception as e:
        print(f"Chart error: {e}")
        return None

# ============================================================================
# AI Analysis Function
# ============================================================================

def analyze_stock_ai(symbol: str, stock_data: dict, news: list):
    if not stock_data or "error" in stock_data:
        return None
    
    metrics = stock_data.get('metrics', {})
    
    price = metrics.get('current_price', 'N/A')
    if isinstance(price, (int, float)):
        price_str = f"${price:.2f}"
    else:
        price_str = str(price)
    
    market_cap = metrics.get('market_cap', 'N/A')
    if isinstance(market_cap, (int, float)):
        if market_cap > 1e12:
            market_cap_str = f"${market_cap/1e12:.2f}T"
        elif market_cap > 1e9:
            market_cap_str = f"${market_cap/1e9:.2f}B"
        else:
            market_cap_str = f"${market_cap/1e6:.2f}M"
    else:
        market_cap_str = str(market_cap)
    
    news_summary = "No recent news available"
    if news and len(news) > 0:
        titles = [n.get('title', '') for n in news[:3] if n.get('title')]
        news_summary = " | ".join(titles) if titles else "No recent news"
    
    prompt = f"""
You are a professional financial analyst. Provide a concise investment analysis.

STOCK: {symbol}
CURRENT PRICE: {price_str}
MARKET CAP: {market_cap_str}
P/E RATIO: {metrics.get('pe_ratio', 'N/A')}
52-WEEK RANGE: {metrics.get('52_week_low', 'N/A')} - {metrics.get('52_week_high', 'N/A')}
SECTOR: {metrics.get('sector', 'N/A')}
INDUSTRY: {metrics.get('industry', 'N/A')}

LATEST NEWS: {news_summary}

Provide analysis in this exact format with NO HTML tags:
OVERVIEW: [2-3 sentences]
FINANCIALS: [2-3 sentences]
TECHNICAL: [1-2 sentences]
RECOMMENDATION: [BUY/HOLD/SELL] - [justification]
"""
    
    llm = get_llm()
    if not llm:
        return None
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        content = re.sub(r'<[^>]+>', '', content)
        
        overview = ""
        financials = ""
        technical = ""
        recommendation = ""
        rec_type = "HOLD"
        
        for line in content.split('\n'):
            line = line.strip()
            if line.upper().startswith("OVERVIEW:"):
                overview = line.replace("OVERVIEW:", "").strip()
            elif line.upper().startswith("FINANCIALS:"):
                financials = line.replace("FINANCIALS:", "").strip()
            elif line.upper().startswith("TECHNICAL:"):
                technical = line.replace("TECHNICAL:", "").strip()
            elif line.upper().startswith("RECOMMENDATION:"):
                rec_text = line.replace("RECOMMENDATION:", "").strip()
                if "BUY" in rec_text.upper():
                    rec_type = "BUY"
                elif "SELL" in rec_text.upper():
                    rec_type = "SELL"
                else:
                    rec_type = "HOLD"
                recommendation = rec_text
        
        return {
            "overview": overview,
            "financials": financials,
            "technical": technical,
            "recommendation": recommendation,
            "rec_type": rec_type,
        }
    except Exception as e:
        print(f"AI Error: {e}")
        return None

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("""
    <div style="padding: 0.5rem 0 0.5rem 0;">
        <h2 style="color: #ffffff; font-size: 1.2rem; font-weight: 600; margin: 0;">Market Intelligence</h2>
        <p style="color: rgba(255,255,255,0.3); font-size: 0.7rem; margin: 0;">AI-Powered Analysis Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Symbol Input
    st.markdown('<p style="color: rgba(255,255,255,0.4); font-size: 0.7rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.2rem;">Symbol</p>', unsafe_allow_html=True)
    symbol_input = st.text_input(
        "",
        value=st.session_state.symbol,
        placeholder="Enter symbol...",
        label_visibility="collapsed"
    )
    
    # Analyze Button
    analyze_clicked = st.button("Analyze", use_container_width=True)
    
    if analyze_clicked:
        st.session_state.symbol = symbol_input.upper().strip()
        st.session_state.analyzed = True
        st.rerun()
    
    st.markdown("---")
    
    # Quick Picks
    st.markdown('<p style="color: rgba(255,255,255,0.4); font-size: 0.7rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.3rem;">Quick Picks</p>', unsafe_allow_html=True)
    
    quick_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "AMZN", "META", "NFLX"]
    
    col1, col2 = st.columns(2)
    for i, qs in enumerate(quick_symbols):
        if i < 4:
            with col1:
                if st.button(qs, key=f"quick_{qs}", use_container_width=True):
                    st.session_state.symbol = qs
                    st.session_state.analyzed = True
                    st.rerun()
        else:
            with col2:
                if st.button(qs, key=f"quick_{qs}_2", use_container_width=True):
                    st.session_state.symbol = qs
                    st.session_state.analyzed = True
                    st.rerun()
    
    st.markdown("---")
    
    # System Status
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.02); border-radius: 8px; padding: 0.8rem 1rem; border: 1px solid rgba(255,255,255,0.05);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: rgba(255,255,255,0.3); font-size: 0.7rem;">System Status</span>
            <span style="color: #00d4aa; font-size: 0.7rem;">
                <span style="display: inline-block; width: 6px; height: 6px; background: #00d4aa; border-radius: 50%; margin-right: 4px; animation: pulse 2s infinite;"></span>
                Online
            </span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.3rem;">
            <span style="color: rgba(255,255,255,0.3); font-size: 0.7rem;">Data Source</span>
            <span style="color: rgba(255,255,255,0.5); font-size: 0.7rem;">Yahoo Finance</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.3rem;">
            <span style="color: rgba(255,255,255,0.3); font-size: 0.7rem;">AI Model</span>
            <span style="color: rgba(255,255,255,0.5); font-size: 0.7rem;">Groq Qwen 27B</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.3rem;">
            <span style="color: rgba(255,255,255,0.3); font-size: 0.7rem;">Last Updated</span>
            <span style="color: rgba(255,255,255,0.5); font-size: 0.7rem;">{datetime.now().strftime("%H:%M")}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# MAIN CONTENT
# ============================================================================

# Header
st.markdown(f"""
<div class="dashboard-header">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div>
            <h1 class="dashboard-title">Market Intelligence Dashboard</h1>
            <p class="dashboard-subtitle">Real-time financial analysis powered by artificial intelligence</p>
        </div>
        <div style="display: flex; gap: 0.5rem; align-items: center;">
            <span style="display: flex; align-items: center; color: rgba(255,255,255,0.3); font-size: 0.7rem;">
                <span class="status-dot"></span> Live
            </span>
            <span style="color: rgba(255,255,255,0.2);">|</span>
            <span style="color: rgba(255,255,255,0.3); font-size: 0.7rem;">{datetime.now().strftime("%d %b %Y")} • {datetime.now().strftime("%H:%M")} UTC</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# Analysis Execution
# ============================================================================

if st.session_state.analyzed:
    symbol = st.session_state.symbol
    
    with st.spinner(f"Analyzing {symbol}..."):
        
        # Fetch data
        result = get_stock_data_with_indicators(symbol, "1mo")
        data_source = "Global Markets"
        
        if "error" in result:
            st.error(f"Data error: {result['error']}")
            st.stop()
        
        metrics = result.get('metrics', {})
        candles = result.get('candles', [])
        price_history = result.get('price_history', [])
        
        # Fetch news
        news = []
        try:
            news = search_stock_news(symbol)
        except Exception as e:
            print(f"News error: {e}")
        
        # AI Analysis
        ai_result = analyze_stock_ai(symbol, result, news)
        
        # ================================================================
        # METRICS ROW
        # ================================================================
        
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <h2 style="color: #ffffff; font-size: 1.2rem; font-weight: 600; margin: 0;">{symbol} - Key Metrics</h2>
            <span style="color: rgba(255,255,255,0.3); font-size: 0.7rem;">{data_source}</span>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        # Price
        price = metrics.get('current_price', 'N/A')
        if isinstance(price, (int, float)):
            price_display = f"${price:.2f}"
        else:
            price_display = str(price)
        
        change = metrics.get('change', 0)
        change_pct = metrics.get('change_percent', 0)
        
        with col1:
            change_class = "metric-change-positive" if change >= 0 else "metric-change-negative"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Price</div>
                <div class="metric-value">{price_display}</div>
                <div class="{change_class}">{change:+.2f} ({change_pct:+.2f}%)</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            pe = metrics.get('pe_ratio', 'N/A')
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">P/E Ratio</div>
                <div class="metric-value">{pe if pe != 'N/A' else '--'}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            mc = metrics.get('market_cap', 'N/A')
            if isinstance(mc, (int, float)):
                if mc > 1e12:
                    mc_display = f"${mc/1e12:.2f}T"
                elif mc > 1e9:
                    mc_display = f"${mc/1e9:.2f}B"
                else:
                    mc_display = f"${mc/1e6:.2f}M"
            else:
                mc_display = str(mc)
            
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Market Cap</div>
                <div class="metric-value">{mc_display}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            high = metrics.get('52_week_high', 'N/A')
            low = metrics.get('52_week_low', 'N/A')
            
            if isinstance(high, (int, float)):
                high_display = f"{high:.2f}"
            else:
                high_display = str(high)
            
            if isinstance(low, (int, float)):
                low_display = f"{low:.2f}"
            else:
                low_display = str(low)
            
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">52-Week Range</div>
                <div class="metric-value" style="font-size: 0.9rem;">{low_display} - {high_display}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            rec_type = ai_result.get('rec_type', 'HOLD') if ai_result else 'HOLD'
            badge_class = f"badge-{rec_type.lower()}"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Recommendation</div>
                <div style="margin-top: 0.2rem;">
                    <span class="{badge_class}">{rec_type}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # ================================================================
        # TABS: Chart | Analysis | News
        # ================================================================
        
        tab1, tab2, tab3, tab4 = st.tabs(["Chart", "Analysis", "News", "Indicators"])
        
        with tab1:
            chart_shown = False
            
            if candles and len(candles) > 1:
                fig = create_candlestick_chart(candles, symbol)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                    chart_shown = True
            
            if not chart_shown and candles and len(candles) > 1:
                df = pd.DataFrame(candles)
                df['date'] = pd.to_datetime(df['date'])
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df['date'],
                    y=df['close'],
                    mode='lines',
                    name='Price',
                    line=dict(color='#00b4ff', width=2)
                ))
                fig.update_layout(
                    template="plotly_dark",
                    height=400,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=20, b=20),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                )
                st.plotly_chart(fig, use_container_width=True)
                chart_shown = True
            
            if not chart_shown and price_history and len(price_history) > 1:
                df = pd.DataFrame(price_history)
                date_col = 'Date' if 'Date' in df.columns else 'date'
                price_col = 'Close' if 'Close' in df.columns else 'close'
                df[date_col] = pd.to_datetime(df[date_col])
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df[date_col],
                    y=df[price_col],
                    mode='lines',
                    name='Price',
                    line=dict(color='#00b4ff', width=2)
                ))
                fig.update_layout(
                    template="plotly_dark",
                    height=400,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=20, b=20),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                )
                st.plotly_chart(fig, use_container_width=True)
                chart_shown = True
            
            if not chart_shown:
                st.info("No historical price data available for this symbol")
        
        with tab2:
            if ai_result:
                overview = ai_result.get('overview', 'N/A')
                financials = ai_result.get('financials', 'N/A')
                technical = ai_result.get('technical', 'N/A')
                recommendation = ai_result.get('recommendation', 'N/A')
                
                st.markdown(f"""
                <div class="analysis-card">
                    <h3 style="font-size: 1.1rem; font-weight: 600; color: #ffffff; margin-bottom: 0.5rem;">{symbol} - Investment Analysis</h3>
                    <hr>
                    
                    <p><strong style="color: #00b4ff;">Overview</strong><br>{overview}</p>
                    
                    <p><strong style="color: #00b4ff;">Financial Health</strong><br>{financials}</p>
                    
                    <p><strong style="color: #00b4ff;">Technical Position</strong><br>{technical}</p>
                    
                    <p><strong style="color: #00b4ff;">Recommendation</strong><br>{recommendation}</p>
                    
                    <hr>
                    <p style="color: rgba(255,255,255,0.2); font-size: 0.7rem;">
                        Analysis generated by AI  •  Data source: {data_source}
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("AI analysis not available for this symbol")
        
        with tab3:
            if news and len(news) > 0:
                for i, article in enumerate(news[:6]):
                    st.markdown(f"""
                    <div class="news-card">
                        <div class="news-title">{article.get('title', 'No Title')}</div>
                        <div class="news-snippet">{article.get('content', '')[:200]}...</div>
                        <div class="news-source">
                            {article.get('source', 'Unknown')}  •  {article.get('date', 'Recent')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No recent news available for this symbol")
        
        # Raw data expander
        with st.expander("Raw Data"):
            st.json(result)

        with tab4:
          indicators = result.get('indicators', {})
    
        if indicators:
               st.markdown("""
               <h3 style="color: #ffffff; font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">Technical Indicators</h3>
               """, unsafe_allow_html=True)
        
        # RSI
        rsi = indicators.get('rsi')
        if rsi is not None:
            rsi_status = "Oversold" if rsi < 30 else "Overbought" if rsi > 70 else "Neutral"
            rsi_color = "#00d4aa" if rsi < 30 else "#ff6b6b" if rsi > 70 else "#ffc107"
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">RSI (14)</div>
                    <div class="metric-value" style="color: {rsi_color};">{rsi:.2f}</div>
                    <div style="color: {rsi_color}; font-size: 0.8rem;">{rsi_status}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # MACD
        macd = indicators.get('macd', {})
        if macd:
            macd_value = macd.get('macd')
            signal = macd.get('signal')
            histogram = macd.get('histogram')
            
            if macd_value is not None:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("MACD", f"{macd_value:.4f}")
                with col2:
                    st.metric("Signal", f"{signal:.4f}" if signal else "N/A")
                with col3:
                    hist_color = "#00d4aa" if histogram and histogram > 0 else "#ff6b6b"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Histogram</div>
                        <div class="metric-value" style="color: {hist_color};">{histogram:.4f}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Bollinger Bands
        bbands = indicators.get('bollinger', {})
        if bbands:
            upper = bbands.get('upper')
            middle = bbands.get('middle')
            lower = bbands.get('lower')
            
            if upper is not None and middle is not None and lower is not None:
                st.markdown("""
                <div style="margin: 0.5rem 0;">
                    <h4 style="color: rgba(255,255,255,0.6); font-size: 0.8rem; font-weight: 500;">Bollinger Bands (20,2)</h4>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Upper Band</div>
                        <div class="metric-value" style="color: #ff6b6b;">${upper:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Middle (MA20)</div>
                        <div class="metric-value" style="color: #ffc107;">${middle:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Lower Band</div>
                        <div class="metric-value" style="color: #00d4aa;">${lower:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
          st.info("Technical indicators not available. Install pandas-ta: pip install pandas-ta")

else:
    # Welcome Screen
    st.markdown("""
    <div class="welcome-container">
        <div class="welcome-box">
            <h1 class="welcome-title">Welcome to</h1>
            <h1 class="welcome-title-main">Market Intelligence</h1>
            <p class="welcome-text">
                Enter a stock symbol in the sidebar to get started.
            </p>
            <div style="display: flex; gap: 0.3rem; justify-content: center; flex-wrap: wrap; margin-top: 1rem;">
                <span class="welcome-tag">AAPL</span>
                <span class="welcome-tag">MSFT</span>
                <span class="welcome-tag">GOOGL</span>
                <span class="welcome-tag">TSLA</span>
                <span class="welcome-tag">NVDA</span>
                <span class="welcome-tag">AMZN</span>
                <span class="welcome-tag">META</span>
                <span class="welcome-tag">NFLX</span>
            </div>
            <div style="margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid rgba(255,255,255,0.05);">
                <p style="color: rgba(255,255,255,0.15); font-size: 0.7rem;">
                    Powered by Groq AI • LangChain • Yahoo Finance
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("""
<div class="footer">
    Market Intelligence Platform  •  AI-Powered Analysis  •  Real-Time Data  •  Global Markets
</div>
""", unsafe_allow_html=True)