"""
LangGraph Agent for Financial Analysis
Yeh agent stocks ka analysis karta hai using tools (yfinance + Tavily)
"""

import json
from typing import TypedDict, Annotated, List, Literal
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from .config import GROQ_API_KEY
from .tools import get_stock_data, search_stock_news

# === 1. State Definition ===
# Agent ka "memory" - har step ke baad update hota hai

class AgentState(TypedDict):
    messages: Annotated[List, add_messages]  # Conversation history
    symbol: str                               # Stock symbol
    stock_data: dict                          # Stock data
    news_data: list                           # News articles
    analysis: str                             # Final analysis

# === 2. Tools Define Karein ===
# Yeh tools agent ko available honge

@tool
def fetch_stock_data(symbol: str) -> str:
    """
    Fetch stock data for a given symbol.
    Returns price, fundamentals, and key metrics.
    """
    result = get_stock_data(symbol)
    if "error" in result:
        return f"Error fetching data: {result['error']}"
    
    # Important metrics extract karein
    metrics = result['metrics']
    summary = f"""
Stock: {metrics['symbol']}
Current Price: ${metrics['current_price']}
Market Cap: {metrics['market_cap']:,}
P/E Ratio: {metrics['pe_ratio']}
52-Week High/Low: ${metrics['52_week_high']} / ${metrics['52_week_low']}
Sector: {metrics['sector']}
Industry: {metrics['industry']}
Description: {metrics['description'][:150]}...
"""
    return summary

@tool
def fetch_news(symbol: str) -> str:
    """
    Fetch latest news and sentiment for a stock.
    """
    result = search_stock_news(symbol)
    if not result or "error" in result[0]:
        return f"Error fetching news: {result[0].get('error', 'Unknown error')}"
    
    # News summary prepare karein
    news_summary = f"Latest News for {symbol}:\n"
    for i, article in enumerate(result[:3]):
        if article.get('type') == 'summary':
            news_summary += f"\n📊 AI Summary: {article['content'][:200]}...\n"
        else:
            news_summary += f"\n{i+1}. {article['title']}\n   {article['content'][:150]}...\n"
    
    return news_summary

# === 3. LLM Initialize Karein ===

llm = ChatGroq(
    model="llama-3.3-70b-versatile",  # Ya "mixtral-8x7b-32768", "gemma2-9b-it"
    api_key=GROQ_API_KEY,
    temperature=0.3,
)

# Tools ko LLM ke saath bind karein
tools = [fetch_stock_data, fetch_news]
llm_with_tools = llm.bind_tools(tools)

# === 4. Agent Nodes ===

def agent_node(state: AgentState):
    """
    Agent decides which tool to call based on user input.
    """
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def stock_data_node(state: AgentState):
    """
    Fetch stock data when tool is called.
    """
    # Tool call extract karein
    last_message = state['messages'][-1]
    tool_calls = last_message.tool_calls
    
    result = {}
    for call in tool_calls:
        if call['name'] == 'fetch_stock_data':
            symbol = call['args']['symbol']
            data = get_stock_data(symbol)
            result[symbol] = data
            
            # Stock data state mein store karein
            state['symbol'] = symbol
            state['stock_data'] = data
    
    # ToolMessage return karein
    tool_messages = []
    for call in tool_calls:
        if call['name'] == 'fetch_stock_data':
            symbol = call['args']['symbol']
            data = get_stock_data(symbol)
            tool_messages.append(
                ToolMessage(
                    content=json.dumps(data, default=str),
                    tool_call_id=call['id']
                )
            )
    
    return {"messages": tool_messages}

def news_node(state: AgentState):
    """
    Fetch news when tool is called.
    """
    last_message = state['messages'][-1]
    tool_calls = last_message.tool_calls
    
    tool_messages = []
    for call in tool_calls:
        if call['name'] == 'fetch_news':
            symbol = call['args']['symbol']
            news = search_stock_news(symbol)
            state['news_data'] = news
            
            tool_messages.append(
                ToolMessage(
                    content=json.dumps(news, default=str),
                    tool_call_id=call['id']
                )
            )
    
    return {"messages": tool_messages}

def analysis_node(state: AgentState):
    """
    Generate final investment summary using all data.
    """
    symbol = state.get('symbol', 'Unknown')
    stock_data = state.get('stock_data', {})
    news_data = state.get('news_data', [])
    
    # Analysis prompt
    analysis_prompt = f"""
You are a financial analyst. Based on the following data, provide an investment summary.

STOCK: {symbol}

FUNDAMENTALS:
- Current Price: ${stock_data.get('metrics', {}).get('current_price', 'N/A')}
- Market Cap: {stock_data.get('metrics', {}).get('market_cap', 'N/A')}
- P/E Ratio: {stock_data.get('metrics', {}).get('pe_ratio', 'N/A')}
- 52-Week Range: ${stock_data.get('metrics', {}).get('52_week_low', 'N/A')} - ${stock_data.get('metrics', {}).get('52_week_high', 'N/A')}
- Sector: {stock_data.get('metrics', {}).get('sector', 'N/A')}

LATEST NEWS:
{json.dumps(news_data[:3], indent=2, default=str) if news_data else 'No recent news available'}

Please provide:
1. Summary of the company
2. Key financial metrics explained
3. Recent news sentiment
4. Technical outlook (based on current price relative to 52-week range)
5. Investment recommendation (Strong Buy, Buy, Hold, Sell, Strong Sell)

Keep it concise but informative.
"""

    messages = state['messages'] + [HumanMessage(content=analysis_prompt)]
    response = llm.invoke(messages)
    
    state['analysis'] = response.content
    
    return {"messages": [response], "analysis": response.content}

# === 5. Graph Construction ===

def create_agent():
    """
    LangGraph workflow create karein
    """
    # Graph build karein
    workflow = StateGraph(AgentState)
    
    # Nodes add karein
    workflow.add_node("agent", agent_node)
    workflow.add_node("fetch_stock", stock_data_node)
    workflow.add_node("fetch_news", news_node)
    workflow.add_node("analysis", analysis_node)
    
    # Edges define karein
    workflow.set_entry_point("agent")
    
    # Conditional edges - agent decides kaun sa tool call kare
    workflow.add_conditional_edges(
        "agent",
        tools_condition,
        {
            "tools": "fetch_stock",  # Tool call detect ho toh
            "__end__": "analysis",   # No tools call ho toh direct analysis
        }
    )
    
    # Tool nodes se agent par wapas jaayein
    workflow.add_edge("fetch_stock", "agent")
    workflow.add_edge("fetch_news", "agent")
    
    # Analysis final node hai
    workflow.add_edge("analysis", END)
    
    return workflow.compile()

# === 6. Main Function ===

def analyze_stock(symbol: str) -> dict:
    """
    Main function to analyze any stock
    """
    print(f"\n🔍 Analyzing {symbol}...\n" + "="*50)
    
    # Agent create karein
    agent = create_agent()
    
    # Initial message
    initial_message = f"Analyze stock {symbol}. Fetch the stock data and latest news, then give an investment recommendation."
    
    # Agent run karein
    result = agent.invoke({
        "messages": [HumanMessage(content=initial_message)],
        "symbol": symbol,
        "stock_data": {},
        "news_data": [],
        "analysis": ""
    })
    
    return {
        "symbol": symbol,
        "analysis": result.get("analysis", "No analysis generated"),
        "stock_data": result.get("stock_data", {}),
        "news_data": result.get("news_data", [])
    }

# === 7. Test ===

if __name__ == "__main__":
    print("="*60)
    print(" Agentic Finance Dashboard - LangGraph Agent Test")
    print("="*60)
    
    # Test stocks
    stocks = ["AAPL", "TSLA", "NVDA"]
    
    for symbol in stocks:
        print(f"\n{'='*60}")
        print(f" Analyzing {symbol}")
        print("="*60)
        
        try:
            result = analyze_stock(symbol)
            print(f"\n Investment Summary for {symbol}:")
            print("-"*50)
            print(result['analysis'])
            
            # User se next ka poochhein
            cont = input(f"\nPress Enter to continue, or type 'stop' to exit: ")
            if cont.lower() == 'stop':
                break
                
        except Exception as e:
            print(f" Error analyzing {symbol}: {str(e)}")