"""
Tools for the Agentic Finance Dashboard
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json
from tavily import TavilyClient
from .config import TAVILY_API_KEY

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
        
        # Get current and previous close prices
        current_price = float(hist['Close'].iloc[-1])
        
        # Calculate change from previous day
        if len(hist) >= 2:
            prev_close = float(hist['Close'].iloc[-2])
            change = current_price - prev_close
            change_percent = (change / prev_close) * 100 if prev_close != 0 else 0
        else:
            change = 0.0
            change_percent = 0.0
        
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

def search_news(query: str, max_results: int = 5) -> list:
    """Tavily API se news search"""
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
    """Stock ke liye news search"""
    query = f"{symbol} stock news financial analysis"
    return search_news(query, max_results)

if __name__ == "__main__":
    # Test
    print("="*50)
    print("Testing Tools")
    print("="*50)
    
    data = get_stock_data("AAPL", "5d")
    if "error" not in data:
        metrics = data['metrics']
        print(f"\nSymbol: {metrics['symbol']}")
        print(f"Price: ${metrics['current_price']:.2f}")
        print(f"Change: {metrics['change']:+.2f} ({metrics['change_percent']:+.2f}%)")
        print(f"Candles: {len(data['candles'])} days")
    else:
        print(f"Error: {data['error']}")