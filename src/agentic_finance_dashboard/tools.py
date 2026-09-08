"""
Tools for the Agentic Finance Dashboard
Yeh tools agent ko stock data fetch karne, news search karne,
aur technical analysis karne ki capability dete hain
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json

def get_stock_data(symbol: str, period: str = "1mo") -> dict:
    """
    Yahoo Finance se stock data fetch karta hai
    
    Args:
        symbol: Stock ticker (e.g., "AAPL", "TSLA")
        period: Time period ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
    
    Returns:
        Dictionary with stock data including price, fundamentals, and metrics
    """
    try:
        print(f" Fetching data for {symbol}...")
        
        # Stock object create karein
        stock = yf.Ticker(symbol)
        
        # Historical data fetch karein
        hist = stock.history(period=period)
        
        # Fundamentals fetch karein
        info = stock.info
        
        # Current price
        current_price = hist['Close'].iloc[-1] if not hist.empty else None
        
        # Key metrics extract karein
        metrics = {
            "symbol": symbol,
            "current_price": current_price,
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
        
        # Price history ko DataFrame mein convert karein (JSON serializable)
        price_history = hist[['Close']].reset_index()
        price_history['Date'] = price_history['Date'].astype(str)
        price_data = price_history.to_dict('records')
        
        result = {
            "metrics": metrics,
            "price_history": price_data,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        print(f" Data fetched successfully for {symbol}")
        return result
        
    except Exception as e:
        print(f"Error fetching data for {symbol}: {str(e)}")
        return {"error": str(e), "symbol": symbol}

def get_multiple_stocks(symbols: list, period: str = "1mo") -> dict:
    """
    Multiple stocks ka data ek saath fetch karta hai
    
    Args:
        symbols: List of stock tickers
        period: Time period
    
    Returns:
        Dictionary with data for all symbols
    """
    results = {}
    for symbol in symbols:
        results[symbol] = get_stock_data(symbol, period)
    return results

# Test function
if __name__ == "__main__":
    # Test run
    print("=" * 50)
    print("Testing Stock Data Tool")
    print("=" * 50)
    
    # Ek stock test karein
    data = get_stock_data("AAPL", "5d")
    if "error" not in data:
        print(f"\n{data['metrics']['symbol']} Data:")
        print(f"   Current Price: ${data['metrics']['current_price']}")
        print(f"   Market Cap: {data['metrics']['market_cap']}")
        print(f"   P/E Ratio: {data['metrics']['pe_ratio']}")
        print(f"   52-Week High: ${data['metrics']['52_week_high']}")
        print(f"   52-Week Low: ${data['metrics']['52_week_low']}")
        print(f"   Sector: {data['metrics']['sector']}")
        print(f"\n   Last {len(data['price_history'])} days of price data available")
    else:
        print(f"Error: {data['error']}")


# === NEWS SEARCH TOOL (Tavily) ===

from tavily import TavilyClient
from .config import TAVILY_API_KEY

def search_news(query: str, max_results: int = 5) -> list:
    """
    Tavily API se news aur articles search karta hai
    
    Args:
        query: Search query (e.g., "Apple stock news")
        max_results: Maximum number of results
    
    Returns:
        List of news articles with title, content, url, and date
    """
    try:
        print(f" Searching news for: {query}")
        
        if not TAVILY_API_KEY:
            print(" TAVILY_API_KEY not found")
            return [{"error": "TAVILY_API_KEY not configured"}]
        
        client = TavilyClient(api_key=TAVILY_API_KEY)
        
        # Search query execute karein
        response = client.search(
            query=query,
            search_depth="basic",  # "basic" ya "advanced"
            max_results=max_results,
            include_answer=True,
            include_raw_content=False
        )
        
        articles = []
        
        # Results extract karein
        if "answer" in response and response["answer"]:
            articles.append({
                "title": "AI Summary",
                "content": response["answer"],
                "url": "",
                "type": "summary"
            })
        
        # Individual articles add karein
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
        print(f" Error searching news: {str(e)}")
        return [{"error": str(e)}]

def search_stock_news(symbol: str, max_results: int = 5) -> list:
    """
    Kisi specific stock ke liye news search karta hai
    """
    query = f"{symbol} stock news financial analysis"
    return search_news(query, max_results)

# Test function update karein
if __name__ == "__main__":
    print("=" * 50)
    print("Testing All Tools")
    print("=" * 50)
    
    # 1. Stock data test
    print("\nTesting Stock Data Tool...")
    data = get_stock_data("AAPL", "5d")
    if "error" not in data:
        print(f" Stock data fetched: ${data['metrics']['current_price']}")
    else:
        print(f"Error: {data['error']}")
    
    # 2. News search test
    print("\n Testing News Search Tool...")
    news = search_stock_news("AAPL", 3)
    if news and "error" not in news[0]:
        print(f" Found {len(news)} news items")
        for i, article in enumerate(news[:2]):
            print(f"   {i+1}. {article['title'][:50]}...")
    else:
        print(" Error searching news")