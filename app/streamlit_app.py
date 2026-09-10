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

from src.agentic_finance_dashboard.tools import get_stock_data_with_indicators, search_stock_news, get_stock_data
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
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []

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
    
    section[data-testid="stSidebar"] {
        background: rgba(15, 15, 30, 0.98);
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    
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
    
    .news-card {
        background: rgba(255,255,255,0.02);
        border-radius: 8px;
        padding: 0.8rem 1rem;
        border: 1px solid rgba(255,255,255,0.05);
        transition: all 0.3s ease;
        margin-bottom: 0.5rem;
    }
    
    .news-card:hover {
        background: rgba(255,255,255,0.04);
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
    
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
        padding: 0.5rem 1rem !important;
    }
    
    .footer {
        margin-top: 2.5rem;
        padding: 1rem 0;
        border-top: 1px solid rgba(255,255,255,0.04);
        color: rgba(255,255,255,0.15);
        font-size: 0.7rem;
        text-align: center;
    }
    
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
# Apply Theme (Light/Dark)
# ============================================================================

if st.session_state.get('theme', 'Dark') == "Light":
    st.markdown("""
    <style>
        .stApp { background: #f0f2f5 !important; }
        
        section[data-testid="stSidebar"] {
            background: #ffffff !important;
            border-right: 1px solid #e0e0e0 !important;
        }
        
        section[data-testid="stSidebar"] * {
            color: #1a1a2e !important;
        }
        
        .dashboard-header {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%) !important;
            border: 1px solid #e0e0e0 !important;
        }
        
        .dashboard-title { color: #1a1a2e !important; }
        .dashboard-subtitle { color: #666 !important; }
        
        .metric-card {
            background: #ffffff !important;
            border: 1px solid #e0e0e0 !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        }
        
        .metric-card:hover {
            background: #f8f9fa !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        }
        
        .metric-label { color: #666 !important; }
        .metric-value { color: #1a1a2e !important; }
        
        .analysis-card {
            background: #ffffff !important;
            border: 1px solid #e0e0e0 !important;
            color: #1a1a2e !important;
        }
        
        .analysis-card strong { color: #0077ff !important; }
        
        .news-card {
            background: #ffffff !important;
            border: 1px solid #e0e0e0 !important;
        }
        
        .news-title { color: #1a1a2e !important; }
        .news-snippet { color: #555 !important; }
        .news-source { color: #999 !important; }
        
        .welcome-box {
            background: #ffffff !important;
            border: 1px solid #e0e0e0 !important;
        }
        
        .welcome-title { color: #666 !important; }
        .welcome-title-main { color: #1a1a2e !important; }
        .welcome-text { color: #666 !important; }
        .welcome-tag { background: #f0f2f5 !important; color: #333 !important; }
        
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p {
            color: #1a1a2e !important;
        }
        
        .stTextInput > div > div > input {
            background: #ffffff !important;
            border: 1px solid #d0d0d0 !important;
            color: #1a1a2e !important;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            background: #e8eaed !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            color: #666 !important;
        }
        
        .stTabs [aria-selected="true"] {
            background: #ffffff !important;
            color: #1a1a2e !important;
        }
        
        .footer {
            color: #999 !important;
            border-top: 1px solid #e0e0e0 !important;
        }
        
        .stCaption, [data-testid="stCaptionContainer"] {
            color: #888 !important;
        }
        
        .streamlit-expanderHeader {
            color: #333 !important;
        }
        
        /* Text in sidebar */
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label {
            color: #1a1a2e !important;
        }
        
        /* System status card */
        section[data-testid="stSidebar"] > div > div > div[style*="background: rgba(255,255,255,0.02)"] {
            background: #f8f9fa !important;
            border-color: #e0e0e0 !important;
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
        
        fig.update_xaxes(gridcolor="rgba(255,255,255,0.04)")
        fig.update_yaxes(gridcolor="rgba(255,255,255,0.04)")
        
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
    price_str = f"${price:.2f}" if isinstance(price, (int, float)) else str(price)
    
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

CRITICAL INSTRUCTION: Your response MUST be in plain text format with NO HTML tags.
DO NOT use any HTML tags. ONLY use plain text.

Format your response EXACTLY like this:
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
        
        # Clean HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        content = re.sub(r'&[a-z]+;', '', content)
        
        overview = ""
        financials = ""
        technical = ""
        recommendation = ""
        rec_type = "HOLD"
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            upper_line = line.upper()
            if upper_line.startswith("OVERVIEW:"):
                overview = line.replace("OVERVIEW:", "").replace("overview:", "").strip()
            elif upper_line.startswith("FINANCIALS:"):
                financials = line.replace("FINANCIALS:", "").replace("financials:", "").strip()
            elif upper_line.startswith("TECHNICAL:"):
                technical = line.replace("TECHNICAL:", "").replace("technical:", "").strip()
            elif upper_line.startswith("RECOMMENDATION:"):
                rec_text = line.replace("RECOMMENDATION:", "").replace("recommendation:", "").strip()
                if "BUY" in rec_text.upper():
                    rec_type = "BUY"
                elif "SELL" in rec_text.upper():
                    rec_type = "SELL"
                else:
                    rec_type = "HOLD"
                recommendation = rec_text
        
        # Fallback if parsing failed
        if not overview and not financials and not technical and not recommendation:
            overview = content[:300]
        
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
    
    # Watchlist
    st.markdown('<p style="color: rgba(255,255,255,0.4); font-size: 0.7rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.3rem;">Watchlist</p>', unsafe_allow_html=True)
    
    if st.session_state.analyzed:
        if st.button("Add to Watchlist", use_container_width=True):
            if st.session_state.symbol not in st.session_state.watchlist:
                st.session_state.watchlist.append(st.session_state.symbol)
                st.success(f"{st.session_state.symbol} added!")
    
    if st.session_state.watchlist:
        for ws in st.session_state.watchlist:
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(ws, key=f"watch_{ws}", use_container_width=True):
                    st.session_state.symbol = ws
                    st.session_state.analyzed = True
                    st.rerun()
            with col2:
                if st.button("X", key=f"remove_{ws}"):
                    st.session_state.watchlist.remove(ws)
                    st.rerun()
    else:
        st.caption("No stocks in watchlist")
    
    st.markdown("---")
    
    # Comparison Mode
    st.markdown('<p style="color: rgba(255,255,255,0.4); font-size: 0.7rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.3rem;">Compare Mode</p>', unsafe_allow_html=True)
    
    compare_mode = st.checkbox("Enable Comparison", value=False)
    compare_symbols = ""
    
    if compare_mode:
        compare_symbols = st.text_input(
            "Compare with",
            value="MSFT, GOOGL",
            placeholder="e.g., MSFT, GOOGL"
        )
    
    st.markdown("---")
    
     # Theme Toggle
      
    st.markdown('<p style="color: rgba(255,255,255,0.4); font-size: 0.7rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.3rem;">Theme</p>', unsafe_allow_html=True)
    
    # Initialize theme in session state (only once)
    if 'theme' not in st.session_state:
        st.session_state.theme = "Dark"
    
    # Radio button with key
    theme = st.radio(
        "Theme",
        ["Dark", "Light"],
        index=0 if st.session_state.theme == "Dark" else 1,
        label_visibility="collapsed",
        horizontal=True,
        key="theme_radio"
    )
    
    # Update session state if changed
    if theme != st.session_state.theme:
        st.session_state.theme = theme
        st.rerun()
    
    if theme == "Light":
        st.markdown("""
        <style>
            /* Main background */
            .stApp {
                background: #f0f2f5 !important;
            }
            
            /* Sidebar */
            section[data-testid="stSidebar"] {
                background: #ffffff !important;
                border-right: 1px solid #e0e0e0 !important;
            }
            
            section[data-testid="stSidebar"] * {
                color: #1a1a2e !important;
            }
            
            /* Header */
            .dashboard-header {
                background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%) !important;
                border: 1px solid #e0e0e0 !important;
            }
            
            .dashboard-title {
                color: #1a1a2e !important;
            }
            
            .dashboard-subtitle {
                color: #666 !important;
            }
            
            /* Metric Cards */
            .metric-card {
                background: #ffffff !important;
                border: 1px solid #e0e0e0 !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
            }
            
            .metric-card:hover {
                background: #f8f9fa !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
            }
            
            .metric-label {
                color: #666 !important;
            }
            
            .metric-value {
                color: #1a1a2e !important;
            }
            
            /* Analysis Card */
            .analysis-card {
                background: #ffffff !important;
                border: 1px solid #e0e0e0 !important;
                color: #1a1a2e !important;
            }
            
            .analysis-card strong {
                color: #0077ff !important;
            }
            
            /* News Cards */
            .news-card {
                background: #ffffff !important;
                border: 1px solid #e0e0e0 !important;
            }
            
            .news-title {
                color: #1a1a2e !important;
            }
            
            .news-snippet {
                color: #555 !important;
            }
            
            .news-source {
                color: #999 !important;
            }
            
            /* Welcome Screen */
            .welcome-box {
                background: #ffffff !important;
                border: 1px solid #e0e0e0 !important;
            }
            
            .welcome-title {
                color: #666 !important;
            }
            
            .welcome-title-main {
                color: #1a1a2e !important;
            }
            
            .welcome-text {
                color: #666 !important;
            }
            
            .welcome-tag {
                background: #f0f2f5 !important;
                color: #333 !important;
            }
            
            /* Text elements */
            h1, h2, h3, h4, h5, h6, p, span, div {
                color: #1a1a2e;
            }
            
            /* Input fields */
            .stTextInput > div > div > input {
                background: #ffffff !important;
                border: 1px solid #d0d0d0 !important;
                color: #1a1a2e !important;
            }
            
            .stTextInput > div > div > input:focus {
                border-color: #0077ff !important;
                box-shadow: 0 0 0 2px rgba(0, 119, 255, 0.15) !important;
            }
            
            /* Buttons */
            .stButton > button {
                background: linear-gradient(135deg, #0077ff 0%, #0055cc 100%) !important;
                color: #ffffff !important;
            }
            
            /* Tabs */
            .stTabs [data-baseweb="tab-list"] {
                background: #e8eaed !important;
            }
            
            .stTabs [data-baseweb="tab"] {
                color: #666 !important;
            }
            
            .stTabs [aria-selected="true"] {
                background: #ffffff !important;
                color: #1a1a2e !important;
            }
            
            /* Expander */
            .streamlit-expanderHeader {
                color: #333 !important;
                background: #ffffff !important;
            }
            
            /* Selectbox */
            .stSelectbox > div > div {
                background: #ffffff !important;
                color: #1a1a2e !important;
            }
            
            /* Radio buttons */
            .stRadio > div {
                color: #1a1a2e !important;
            }
            
            /* Checkbox */
            .stCheckbox > div {
                color: #1a1a2e !important;
            }
            
            /* Caption text */
            .stCaption, caption {
                color: #888 !important;
            }
            
            /* Footer */
            .footer {
                color: #999 !important;
                border-top: 1px solid #e0e0e0 !important;
            }
            
            /* Fix for sidebar text */
            section[data-testid="stSidebar"] h1,
            section[data-testid="stSidebar"] h2,
            section[data-testid="stSidebar"] h3,
            section[data-testid="stSidebar"] p,
            section[data-testid="stSidebar"] span,
            section[data-testid="stSidebar"] div,
            section[data-testid="stSidebar"] label {
                color: #1a1a2e !important;
            }
            
            /* Fix for metric cards in light mode */
            .metric-card .metric-value {
                color: #1a1a2e !important;
            }
            
            .metric-card .metric-label {
                color: #666 !important;
            }
            
            /* Badge colors remain same */
            .badge-buy {
                background: rgba(0, 180, 130, 0.15) !important;
                color: #00a080 !important;
            }
            
            .badge-hold {
                background: rgba(200, 150, 0, 0.15) !important;
                color: #b8860b !important;
            }
            
            .badge-sell {
                background: rgba(220, 50, 50, 0.15) !important;
                color: #cc3333 !important;
            }
        </style>
        """, unsafe_allow_html=True)
        st.markdown("""
        <style>
            .stApp { background: #f5f5f7 !important; }
            .metric-card { background: #ffffff !important; border-color: #e0e0e0 !important; }
            .metric-value { color: #1a1a2e !important; }
            .metric-label { color: #666 !important; }
            .dashboard-header { background: #ffffff !important; }
            .dashboard-title { color: #1a1a2e !important; }
            .news-card { background: #ffffff !important; }
            .news-title { color: #1a1a2e !important; }
        </style>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # System Status
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.02); border-radius: 8px; padding: 0.8rem 1rem; border: 1px solid rgba(255,255,255,0.05);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: rgba(255,255,255,0.3); font-size: 0.7rem;">Status</span>
            <span style="color: #00d4aa; font-size: 0.7rem;">
                <span style="display: inline-block; width: 6px; height: 6px; background: #00d4aa; border-radius: 50%; margin-right: 4px;"></span>
                Online
            </span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.3rem;">
            <span style="color: rgba(255,255,255,0.3); font-size: 0.7rem;">Data</span>
            <span style="color: rgba(255,255,255,0.5); font-size: 0.7rem;">Yahoo Finance</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.3rem;">
            <span style="color: rgba(255,255,255,0.3); font-size: 0.7rem;">AI Model</span>
            <span style="color: rgba(255,255,255,0.5); font-size: 0.7rem;">Groq Qwen 27B</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.3rem;">
            <span style="color: rgba(255,255,255,0.3); font-size: 0.7rem;">Updated</span>
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
        
        # Fetch data with indicators
        result = get_stock_data_with_indicators(symbol, "1mo")
        data_source = "Global Markets"
        
        if "error" in result:
            st.error(f"Data error: {result['error']}")
            st.stop()
        
        metrics = result.get('metrics', {})
        candles = result.get('candles', [])
        price_history = result.get('price_history', [])
        indicators = result.get('indicators', {})
        
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
        price_display = f"${price:.2f}" if isinstance(price, (int, float)) else str(price)
        
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
                mc_display = f"${mc/1e12:.2f}T" if mc > 1e12 else f"${mc/1e9:.2f}B" if mc > 1e9 else f"${mc/1e6:.2f}M"
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
            high_display = f"{high:.2f}" if isinstance(high, (int, float)) else str(high)
            low_display = f"{low:.2f}" if isinstance(low, (int, float)) else str(low)
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
        # COMPARISON SECTION (if enabled)
        # ================================================================
        
        if compare_mode and compare_symbols:
            compare_list = [s.strip().upper() for s in compare_symbols.split(",") if s.strip()]
            
            if compare_list:
                st.markdown("---")
                st.markdown(f"### Comparison: {symbol} vs {', '.join(compare_list)}")
                
                compare_data = {}
                for comp_symbol in compare_list[:3]:
                    comp_result = get_stock_data(comp_symbol, "1mo")
                    if "error" not in comp_result:
                        compare_data[comp_symbol] = comp_result
                
                if compare_data:
                    # Comparison Chart
                    fig = go.Figure()
                    
                    if candles:
                        df_main = pd.DataFrame(candles)
                        df_main['date'] = pd.to_datetime(df_main['date'])
                        base = df_main['close'].iloc[0]
                        df_main['normalized'] = (df_main['close'] / base) * 100
                        
                        fig.add_trace(go.Scatter(
                            x=df_main['date'],
                            y=df_main['normalized'],
                            mode='lines',
                            name=symbol,
                            line=dict(color='#00b4ff', width=2)
                        ))
                    
                    colors = ['#00d4aa', '#ffc107', '#ff6b6b']
                    for i, (comp_symbol, comp_result) in enumerate(compare_data.items()):
                        comp_candles = comp_result.get('candles', [])
                        if comp_candles:
                            df_comp = pd.DataFrame(comp_candles)
                            df_comp['date'] = pd.to_datetime(df_comp['date'])
                            base = df_comp['close'].iloc[0]
                            df_comp['normalized'] = (df_comp['close'] / base) * 100
                            
                            fig.add_trace(go.Scatter(
                                x=df_comp['date'],
                                y=df_comp['normalized'],
                                mode='lines',
                                name=comp_symbol,
                                line=dict(color=colors[i % len(colors)], width=2)
                            ))
                    
                    fig.update_layout(
                        template="plotly_dark",
                        height=400,
                        title="Normalized Performance (Base = 100)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=20, r=20, t=40, b=20),
                        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Comparison Table
                    comparison_data = [{
                        "Symbol": symbol,
                        "Price": f"${metrics.get('current_price', 0):.2f}" if isinstance(metrics.get('current_price'), (int, float)) else "N/A",
                        "Change": f"{metrics.get('change_percent', 0):+.2f}%",
                        "P/E": metrics.get('pe_ratio', 'N/A'),
                        "Market Cap": f"${metrics.get('market_cap', 0)/1e9:.2f}B" if isinstance(metrics.get('market_cap'), (int, float)) else "N/A",
                    }]
                    
                    for comp_symbol, comp_result in compare_data.items():
                        comp_metrics = comp_result.get('metrics', {})
                        comparison_data.append({
                            "Symbol": comp_symbol,
                            "Price": f"${comp_metrics.get('current_price', 0):.2f}" if isinstance(comp_metrics.get('current_price'), (int, float)) else "N/A",
                            "Change": f"{comp_metrics.get('change_percent', 0):+.2f}%",
                            "P/E": comp_metrics.get('pe_ratio', 'N/A'),
                            "Market Cap": f"${comp_metrics.get('market_cap', 0)/1e9:.2f}B" if isinstance(comp_metrics.get('market_cap'), (int, float)) else "N/A",
                        })
                    
                    st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)
        
        # ================================================================
        # TABS
        # ================================================================
        
        tab1, tab2, tab3, tab4 = st.tabs(["Chart", "Analysis", "News", "Indicators"])
        
        with tab1:
            chart_shown = False
            
            if candles and len(candles) > 1:
                fig = create_candlestick_chart(candles, symbol)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                    chart_shown = True
            
            if not chart_shown and price_history and len(price_history) > 1:
                df = pd.DataFrame(price_history)
                date_col = 'Date' if 'Date' in df.columns else 'date'
                price_col = 'Close' if 'Close' in df.columns else 'close'
                df[date_col] = pd.to_datetime(df[date_col])
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df[date_col], y=df[price_col], mode='lines', line=dict(color='#00b4ff', width=2)))
                fig.update_layout(
                    template="plotly_dark",
                    height=400,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=20, b=20),
                )
                st.plotly_chart(fig, use_container_width=True)
                chart_shown = True
            
            if not chart_shown:
                st.info("No historical price data available for this symbol")
        
        with tab2:
            if ai_result:
                overview = ai_result.get("overview", "N/A")
                financials = ai_result.get("financials", "N/A")
                technical = ai_result.get("technical", "N/A")
                recommendation = ai_result.get("recommendation", "N/A")
                
                st.markdown(f"### {symbol} - Investment Analysis")
                st.divider()
                
                st.markdown("**Overview**")
                st.write(overview)
                
                st.markdown("**Financial Health**")
                st.write(financials)
                
                st.markdown("**Technical Position**")
                st.write(technical)
                
                st.markdown("**Recommendation**")
                st.write(recommendation)
                
                st.divider()
                st.caption(f"Analysis generated by AI • Data source: {data_source}")
                
                # Export Buttons
                st.markdown("---")
                st.markdown("**Export Report**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    csv_data = f"""Symbol,{symbol}
Price,{metrics.get('current_price', 'N/A')}
Change,{metrics.get('change', 0)}
Change Percent,{metrics.get('change_percent', 0)}
P/E Ratio,{metrics.get('pe_ratio', 'N/A')}
Market Cap,{metrics.get('market_cap', 'N/A')}
52-Week High,{metrics.get('52_week_high', 'N/A')}
52-Week Low,{metrics.get('52_week_low', 'N/A')}
Sector,{metrics.get('sector', 'N/A')}
Industry,{metrics.get('industry', 'N/A')}

Analysis
Overview,{overview}
Financials,{financials}
Technical,{technical}
Recommendation,{recommendation}
"""
                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name=f"{symbol}_analysis.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col2:
                    report_text = f"""
{'='*60}
{symbol} - INVESTMENT ANALYSIS REPORT
{'='*60}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

KEY METRICS
{'-'*40}
Price: ${metrics.get('current_price', 'N/A')}
Change: {metrics.get('change', 0):+.2f} ({metrics.get('change_percent', 0):+.2f}%)
P/E Ratio: {metrics.get('pe_ratio', 'N/A')}
Market Cap: ${metrics.get('market_cap', 0)/1e9:.2f}B
52-Week Range: ${metrics.get('52_week_low', 'N/A')} - ${metrics.get('52_week_high', 'N/A')}
Sector: {metrics.get('sector', 'N/A')}
Industry: {metrics.get('industry', 'N/A')}

INVESTMENT ANALYSIS
{'-'*40}

OVERVIEW:
{overview}

FINANCIAL HEALTH:
{financials}

TECHNICAL POSITION:
{technical}

RECOMMENDATION:
{recommendation}

{'='*60}
Analysis generated by AI
Data source: {data_source}
{'='*60}
"""
                    st.download_button(
                        label="Download Report",
                        data=report_text,
                        file_name=f"{symbol}_report.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
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
        
        with tab4:
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
                if macd and macd.get('macd') is not None:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("MACD", f"{macd.get('macd', 0):.4f}")
                    with col2:
                        st.metric("Signal", f"{macd.get('signal', 0):.4f}" if macd.get('signal') else "N/A")
                    with col3:
                        hist = macd.get('histogram', 0)
                        hist_color = "#00d4aa" if hist and hist > 0 else "#ff6b6b"
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Histogram</div>
                            <div class="metric-value" style="color: {hist_color};">{hist:.4f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Bollinger Bands
                bbands = indicators.get('bollinger', {})
                if bbands and bbands.get('upper') is not None:
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
                            <div class="metric-value" style="color: #ff6b6b;">${bbands.get('upper', 0):.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Middle (MA20)</div>
                            <div class="metric-value" style="color: #ffc107;">${bbands.get('middle', 0):.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Lower Band</div>
                            <div class="metric-value" style="color: #00d4aa;">${bbands.get('lower', 0):.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("Technical indicators not available. Install ta library: pip install ta")
        
        # Raw data expander
        with st.expander("Raw Data"):
            st.json(result)

else:
    # Welcome Screen
    st.markdown("""
    <div class="welcome-container">
        <div class="welcome-box">
            <h1 class="welcome-title">Welcome to</h1>
            <h1 class="welcome-title-main">Market Intelligence</h1>
            <p class="welcome-text">Enter a stock symbol in the sidebar to get started.</p>
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