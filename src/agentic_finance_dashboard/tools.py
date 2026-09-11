"""
Tools for the Agentic Finance Dashboard
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
import json
from tavily import TavilyClient
from .config import TAVILY_API_KEY

# Try to import ta library (installed via pip install ta)
try:
    import ta as ta_lib
    USE_TA_LIB = True
    print("Using ta library for technical indicators")
except ImportError:
    try:
        import pandas_ta as ta
        USE_TA_LIB = False
        print("Using pandas-ta library for technical indicators")
    except ImportError:
        ta_lib = None
        ta = None
        USE_TA_LIB = False
        print("Technical indicators library not installed. Install with: pip install ta")
def get_tavily_key():
    """Get Tavily API key from secrets or env"""
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and "TAVILY_API_KEY" in st.secrets:
            return st.secrets["TAVILY_API_KEY"]
    except Exception:
        pass
    
    from .config import TAVILY_API_KEY
    return TAVILY_API_KEY
def get_stock_data(symbol: str, period: str = "1mo") -> dict:
    """
    Yahoo Finance se stock data fetch karta hai
    """
    try:
        print(f"Fetching data for {symbol}...")
        
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)
        
        if hist.empty:
            return {"error": f"No data found for {symbol}"}
        
        info = stock.info
        
        # Current and previous close
        current_price = float(hist['Close'].iloc[-1])
        prev_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_price
        
        # Calculate change
        change = current_price - prev_close
        change_percent = (change / prev_close * 100) if prev_close != 0 else 0
        
        # Candlestick data
        candles = []
        for idx, row in hist.iterrows():
            candles.append({
                "date": idx.strftime("%Y-%m-%d"),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close']),
                "volume": float(row['Volume'])
            })
        
        metrics = {
            "symbol": symbol,
            "current_price": current_price,
            "change": change,
            "change_percent": change_percent,
            "market_cap": info.get("marketCap", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "forward_pe": info.get("forwardPE", "N/A"),
            "dividend_yield": info.get("dividendYield", "N/A"),
            "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
            "volume": info.get("volume", "N/A"),
            "avg_volume": info.get("averageVolume", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "description": info.get("longBusinessSummary", "N/A")[:200] + "...",
        }
        
        price_history = hist[['Close']].reset_index()
        price_history['Date'] = price_history['Date'].astype(str)
        price_data = price_history.to_dict('records')
        
        result = {
            "metrics": metrics,
            "candles": candles,
            "price_history": price_data,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        print(f"Data fetched successfully for {symbol}")
        print(f"Price: ${current_price:.2f}, Change: {change:+.2f} ({change_percent:+.2f}%)")
        return result
        
    except Exception as e:
        print(f"Error fetching data for {symbol}: {str(e)}")
        return {"error": str(e), "symbol": symbol}

def calculate_technical_indicators(hist: pd.DataFrame) -> dict:
    """
    Calculate RSI, MACD, and Bollinger Bands using ta library
    """
    if hist.empty or len(hist) < 20:
        return {}
    
    df = hist.copy()
    indicators = {}
    
    try:
        if USE_TA_LIB and ta_lib is not None:
            # Using ta library (installed via pip install ta)
            
            # RSI
            rsi_indicator = ta_lib.momentum.RSIIndicator(df['Close'], window=14)
            rsi_values = rsi_indicator.rsi()
            if not rsi_values.empty and not pd.isna(rsi_values.iloc[-1]):
                indicators['rsi'] = float(rsi_values.iloc[-1])
                indicators['rsi_history'] = [float(x) if not pd.isna(x) else None for x in rsi_values.tail(20).tolist()]
            
            # MACD
            macd_indicator = ta_lib.trend.MACD(df['Close'])
            macd_values = macd_indicator.macd()
            signal_values = macd_indicator.macd_signal()
            histogram_values = macd_indicator.macd_diff()
            
            if not macd_values.empty and not pd.isna(macd_values.iloc[-1]):
                indicators['macd'] = {
                    'macd': float(macd_values.iloc[-1]) if not pd.isna(macd_values.iloc[-1]) else None,
                    'signal': float(signal_values.iloc[-1]) if not pd.isna(signal_values.iloc[-1]) else None,
                    'histogram': float(histogram_values.iloc[-1]) if not pd.isna(histogram_values.iloc[-1]) else None,
                }
            
            # Bollinger Bands
            bbands_indicator = ta_lib.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
            upper = bbands_indicator.bollinger_hband()
            middle = bbands_indicator.bollinger_mavg()
            lower = bbands_indicator.bollinger_lband()
            
            if not upper.empty and not pd.isna(upper.iloc[-1]):
                indicators['bollinger'] = {
                    'upper': float(upper.iloc[-1]) if not pd.isna(upper.iloc[-1]) else None,
                    'middle': float(middle.iloc[-1]) if not pd.isna(middle.iloc[-1]) else None,
                    'lower': float(lower.iloc[-1]) if not pd.isna(lower.iloc[-1]) else None,
                }
            
            print("Technical indicators calculated using ta library")
            
        elif not USE_TA_LIB and ta is not None:

            
            # RSI
            rsi = ta.rsi(df['Close'], length=14)
            if rsi is not None and not rsi.empty and not pd.isna(rsi.iloc[-1]):
                indicators['rsi'] = float(rsi.iloc[-1])
            
            # MACD
            macd = ta.macd(df['Close'], fast=12, slow=26, signal=9)
            if macd is not None and not macd.empty:
                indicators['macd'] = {
                    'macd': float(macd.iloc[-1]['MACD_12_26_9']) if not pd.isna(macd.iloc[-1]['MACD_12_26_9']) else None,
                    'signal': float(macd.iloc[-1]['MACDs_12_26_9']) if not pd.isna(macd.iloc[-1]['MACDs_12_26_9']) else None,
                    'histogram': float(macd.iloc[-1]['MACDh_12_26_9']) if not pd.isna(macd.iloc[-1]['MACDh_12_26_9']) else None,
                }
            
            # Bollinger Bands
            bbands = ta.bbands(df['Close'], length=20, std=2)
            if bbands is not None and not bbands.empty:
                indicators['bollinger'] = {
                    'upper': float(bbands.iloc[-1]['BBU_20_2.0']) if not pd.isna(bbands.iloc[-1]['BBU_20_2.0']) else None,
                    'middle': float(bbands.iloc[-1]['BBM_20_2.0']) if not pd.isna(bbands.iloc[-1]['BBM_20_2.0']) else None,
                    'lower': float(bbands.iloc[-1]['BBL_20_2.0']) if not pd.isna(bbands.iloc[-1]['BBL_20_2.0']) else None,
                }
            
            print("Technical indicators calculated using pandas-ta library")
        
        else:
            print("No technical indicators library available")
        
        return indicators
        
    except Exception as e:
        print(f"Error calculating indicators: {str(e)}")
        return {}

def get_stock_data_with_indicators(symbol: str, period: str = "1mo") -> dict:
    """
    Get stock data with technical indicators
    """
    # Get base data
    result = get_stock_data(symbol, period)
    
    if "error" in result:
        return result
    
    # Add technical indicators
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)
        
        if not hist.empty and len(hist) >= 20:
            indicators = calculate_technical_indicators(hist)
            result['indicators'] = indicators
        else:
            result['indicators'] = {}
            
    except Exception as e:
        print(f"Error adding indicators: {str(e)}")
        result['indicators'] = {}
    
    return result

def search_news(query: str, max_results: int = 5) -> list:
    """
    Tavily API se news aur articles search karta hai
    """
    try:
        print(f"Searching news for: {query}")
        
        if not TAVILY_API_KEY:
            print("TAVILY_API_KEY not found")
            return [{"error": "TAVILY_API_KEY not configured"}]
        
        client = TavilyClient(api_key=TAVILY_API_KEY)
        
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=max_results,
            include_answer=True,
            include_raw_content=False
        )
        
        articles = []
        
        if "answer" in response and response["answer"]:
            articles.append({
                "title": "AI Summary",
                "content": response["answer"],
                "url": "",
                "type": "summary"
            })
        
        for result in response.get("results", []):
            articles.append({
                "title": result.get("title", "No Title"),
                "content": result.get("content", "No Content")[:500] + "...",
                "url": result.get("url", ""),
                "score": result.get("score", 0),
                "type": "article"
            })
        
        print(f"Found {len(articles)} news articles")
        return articles
        
    except Exception as e:
        print(f"Error searching news: {str(e)}")
        return [{"error": str(e)}]

def search_stock_news(symbol: str, max_results: int = 5) -> list:
    """
    Kisi specific stock ke liye news search karta hai
    """
    query = f"{symbol} stock news financial analysis"
    return search_news(query, max_results)

if __name__ == "__main__":
    # Test
    print("="*50)
    print("Testing Tools with Technical Indicators")
    print("="*50)
    
    data = get_stock_data_with_indicators("AAPL", "1mo")
    if "error" not in data:
        metrics = data['metrics']
        indicators = data.get('indicators', {})
        
        print(f"\nSymbol: {metrics['symbol']}")
        print(f"Price: ${metrics['current_price']:.2f}")
        print(f"Change: {metrics['change']:+.2f} ({metrics['change_percent']:+.2f}%)")
        print(f"Candles: {len(data['candles'])} days")
        
        if indicators:
            print(f"\nTechnical Indicators:")
            if 'rsi' in indicators:
                print(f"  RSI: {indicators['rsi']:.2f}")
            if 'macd' in indicators:
                macd = indicators['macd']
                print(f"  MACD: {macd.get('macd', 'N/A')}")
                print(f"  Signal: {macd.get('signal', 'N/A')}")
            if 'bollinger' in indicators:
                bb = indicators['bollinger']
                print(f"  Bollinger Upper: ${bb.get('upper', 'N/A')}")
                print(f"  Bollinger Middle: ${bb.get('middle', 'N/A')}")
                print(f"  Bollinger Lower: ${bb.get('lower', 'N/A')}")
        else:
            print("\n  No indicators available")
    else:
        print(f"Error: {data['error']}")