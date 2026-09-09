"""
Pakistan Stock Exchange (PSX) Data Tools - FIXED
"""

import yfinance as yf
import pandas as pd
import json
import time

# PSX Symbol Mapping - Verified working symbols
PSX_SYMBOLS = {
    # KSE-100 Index
    "KSE100": "^KSE100",
    
    # Banking Sector
    "UBL": "UBL.PK",
    "HBL": "HBL.PK", 
    "MCB": "MCB.PK",
    "ABL": "ABL.PK",
    "BAHL": "BAHL.PK",
    "MEBL": "MEBL.PK",
    
    # Oil & Gas
    "PPL": "PPL.PK",
    "OGDC": "OGDC.PK",
    "POL": "POL.PK",
    "PRL": "PRL.PK",
    "ATRL": "ATRL.PK",
    
    # Fertilizer
    "FFC": "FFC.PK",
    "ENGRO": "ENGRO.PK",
    "EFERT": "EFERT.PK",
    
    # Cement
    "LUCK": "LUCK.PK",
    "DGKC": "DGKC.PK",
    "PIOC": "PIOC.PK",
    "CHCC": "CHCC.PK",
    "KOHC": "KOHC.PK",
    
    # Textile
    "NML": "NML.PK",
    "NISHAT": "NISHAT.PK",
    "GATM": "GATM.PK",
    
    # Technology
    "SYS": "SYS.PK",
    "TRG": "TRG.PK",
    "NETSOL": "NETSOL.PK",
    
    # Power
    "KEL": "KEL.PK",
    "HUBC": "HUBC.PK",
    "KAPCO": "KAPCO.PK",
    
    # Pharma
    "SEARL": "SEARL.PK",
    "GLAXO": "GLAXO.PK",
}

def get_psx_data(symbol: str, period: str = "1mo") -> dict:
    """
    Fetch Pakistan Stock Exchange data with better error handling
    """
    try:
        symbol = symbol.upper()
        
        # Get yfinance symbol
        yf_symbol = PSX_SYMBOLS.get(symbol, f"{symbol}.PK")
        
        print(f" Fetching PSX data for {symbol} -> {yf_symbol}")
        
        # Fetch with timeout
        stock = yf.Ticker(yf_symbol)
        hist = stock.history(period=period, timeout=10)
        
        if hist.empty:
            # Try alternative format
            alt_symbol = symbol + ".PK"
            stock = yf.Ticker(alt_symbol)
            hist = stock.history(period=period, timeout=10)
            
            if hist.empty:
                return {"error": f"No data found for {symbol}. Try using US stocks like AAPL, MSFT."}
        
        info = stock.info
        
        # Get current values
        current_price = float(hist['Close'].iloc[-1])
        prev_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_price
        
        # Get 52-week data from info or calculate from history
        fifty_two_high = info.get("fiftyTwoWeekHigh", float(hist['High'].max()))
        fifty_two_low = info.get("fiftyTwoWeekLow", float(hist['Low'].min()))
        
        # Market cap
        market_cap = info.get("marketCap", "N/A")
        if isinstance(market_cap, (int, float)):
            market_cap_str = f"{market_cap:,.0f}"
        else:
            market_cap_str = "N/A"
        
        metrics = {
            "symbol": symbol,
            "name": info.get("longName", info.get("shortName", symbol)),
            "current_price": current_price,
            "change": float(current_price - prev_close),
            "change_percent": float(((current_price - prev_close) / prev_close * 100)) if prev_close != 0 else 0,
            "volume": int(hist['Volume'].iloc[-1]) if not pd.isna(hist['Volume'].iloc[-1]) else 0,
            "high": float(hist['High'].iloc[-1]),
            "low": float(hist['Low'].iloc[-1]),
            "open": float(hist['Open'].iloc[-1]),
            "market_cap": market_cap_str,
            "pe_ratio": info.get("trailingPE", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "currency": "PKR",
            "52_week_high": float(fifty_two_high),
            "52_week_low": float(fifty_two_low),
            "exchange": "PSX",
        }
        
        # Candlestick data
        candles = []
        for idx, row in hist.iterrows():
            candles.append({
                "date": idx.strftime("%Y-%m-%d"),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close']),
                "volume": int(row['Volume']) if not pd.isna(row['Volume']) else 0
            })
        
        return {
            "metrics": metrics,
            "candles": candles,
        }
        
    except Exception as e:
        print(f" Error: {str(e)}")
        return {"error": f"Error fetching data: {str(e)}"}

def get_kse100():
    """
    Get KSE-100 index data
    """
    try:
        index = yf.Ticker("^KSE100")
        hist = index.history(period="1d")
        
        if hist.empty:
            return {"error": "KSE-100 data unavailable"}
        
        current = float(hist['Close'].iloc[-1])
        prev = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current
        
        return {
            "current": current,
            "change": current - prev,
            "change_percent": ((current - prev) / prev * 100) if prev != 0 else 0,
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Test Pakistan stocks
    print("="*50)
    print("Testing PSX Tools")
    print("="*50)
    
    test_symbols = ["UBL", "OGDC", "LUCK", "KSE100"]
    
    for sym in test_symbols:
        print(f"\nTesting {sym}...")
        data = get_psx_data(sym, "5d")
        if "error" in data:
            print(f" Error: {data['error']}")
        else:
            metrics = data['metrics']
            print(f" {metrics['name']}")
            print(f"   Price: {metrics['current_price']:.2f} {metrics['currency']}")
            print(f"   Change: {metrics['change']:+.2f} ({metrics['change_percent']:+.2f}%)")
            print(f"   Candles: {len(data['candles'])} days")