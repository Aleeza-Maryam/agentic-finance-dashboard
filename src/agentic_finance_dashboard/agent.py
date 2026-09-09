"""
LangGraph Agent for Financial Analysis
"""

import json
from typing import TypedDict, Annotated, List
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import tools_condition

from .config import GROQ_API_KEY
from .tools import get_stock_data, search_stock_news

# === 1. State Definition ===
class AgentState(TypedDict):
    messages: Annotated[List, add_messages]
    symbol: str
    stock_data: dict
    news_data: list
    analysis: str

# === 2. Tools Define Karein ===
from langchain_core.tools import tool

@tool
def fetch_stock_data(symbol: str) -> str:
    """Fetch stock data for a given symbol. Returns price, fundamentals, and key metrics."""
    result = get_stock_data(symbol)
    if "error" in result:
        return f"Error: {result['error']}"
    return json.dumps(result, default=str)

@tool
def fetch_news(symbol: str) -> str:
    """Fetch latest news and sentiment for a stock."""
    result = search_stock_news(symbol)
    if not result or "error" in result[0]:
        return f"Error: {result[0].get('error', 'Unknown')}"
    return json.dumps(result, default=str)

llm = ChatGroq(
    model="qwen/qwen3.8-27b",  # ✅ Tool calling supported
    api_key=GROQ_API_KEY,
    temperature=0.3,
    max_tokens=512,  # ✅ Reduced to avoid rate limits
)
tools = [fetch_stock_data, fetch_news]
llm_with_tools = llm.bind_tools(tools)

# === 4. Agent Nodes ===
def agent_node(state: AgentState):
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def stock_data_node(state: AgentState):
    last_message = state['messages'][-1]
    tool_calls = last_message.tool_calls
    
    tool_messages = []
    for call in tool_calls:
        if call['name'] == 'fetch_stock_data':
            symbol = call['args']['symbol']
            data = get_stock_data(symbol)
            state['symbol'] = symbol
            state['stock_data'] = data
            tool_messages.append(
                ToolMessage(
                    content=json.dumps(data, default=str),
                    tool_call_id=call['id']
                )
            )
    return {"messages": tool_messages}

def news_node(state: AgentState):
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
    import json
    
    symbol = state.get('symbol', 'Unknown')
    stock_data = state.get('stock_data', {})
    news_data = state.get('news_data', [])
    
    # Fallback: messages se data extract
    if not stock_data:
        for msg in state['messages']:
            if isinstance(msg, ToolMessage) and 'fetch_stock_data' in str(msg):
                try:
                    content = json.loads(msg.content)
                    if isinstance(content, dict) and 'metrics' in content:
                        stock_data = content
                        break
                except:
                    pass
    
    if not news_data:
        for msg in state['messages']:
            if isinstance(msg, ToolMessage) and 'fetch_news' in str(msg):
                try:
                    content = json.loads(msg.content)
                    if isinstance(content, list):
                        news_data = content
                        break
                except:
                    pass
    
    # Safe formatting
    metrics = stock_data.get('metrics', {})
    market_cap = metrics.get('market_cap', 'N/A')
    if isinstance(market_cap, (int, float)):
        market_cap_str = f"{market_cap:,}"
    else:
        market_cap_str = str(market_cap)
    
    current_price = metrics.get('current_price', 'N/A')
    if isinstance(current_price, (int, float)):
        price_str = f"${current_price:.2f}"
    else:
        price_str = str(current_price)
    
    analysis_prompt = f"""
Financial Analysis for {symbol}:

Current Price: {price_str}
Market Cap: {market_cap_str}
P/E Ratio: {metrics.get('pe_ratio', 'N/A')}
52-Week Range: ${metrics.get('52_week_low', 'N/A')} - ${metrics.get('52_week_high', 'N/A')}
Sector: {metrics.get('sector', 'N/A')}
Industry: {metrics.get('industry', 'N/A')}

News Found: {len(news_data)} articles

Please provide:
1. Brief company overview (what they do)
2. Key financial insights from the data above
3. Investment recommendation (Buy/Hold/Sell) with clear justification

Keep it concise and professional (max 250 words).
"""

    messages = state['messages'] + [HumanMessage(content=analysis_prompt)]
    response = llm.invoke(messages)
    state['analysis'] = response.content
    return {"messages": [response], "analysis": response.content}

# === 5. Graph Construction ===
def create_agent():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent", agent_node)
    workflow.add_node("fetch_stock", stock_data_node)
    workflow.add_node("fetch_news", news_node)
    workflow.add_node("analysis", analysis_node)
    
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        tools_condition,
        {"tools": "fetch_stock", "__end__": "analysis"}
    )
    workflow.add_edge("fetch_stock", "agent")
    workflow.add_edge("fetch_news", "agent")
    workflow.add_edge("analysis", END)
    
    return workflow.compile()

# === 6. Main Function ===
def analyze_stock(symbol: str) -> dict:
    print(f"\n🔍 Analyzing {symbol}...\n" + "="*50)
    agent = create_agent()
    
    result = agent.invoke({
        "messages": [HumanMessage(content=f"Analyze stock {symbol}")],
        "symbol": symbol,
        "stock_data": {},
        "news_data": [],
        "analysis": ""
    })
    
    return {
        "symbol": symbol,
        "analysis": result.get("analysis", "No analysis generated"),
    }

# === 7. Test ===
if __name__ == "__main__":
    print("="*60)
    print("🤖 Agentic Finance Dashboard - LangGraph Agent Test")
    print("="*60)
    
    for symbol in ["AAPL", "TSLA", "NVDA"]:
        print(f"\n{'='*60}")
        print(f"📊 Analyzing {symbol}")
        print("="*60)
        
        try:
            result = analyze_stock(symbol)
            print(f"\n📝 Investment Summary for {symbol}:")
            print("-"*50)
            print(result['analysis'])
            
            cont = input("\nPress Enter to continue, or type 'stop': ")
            if cont.lower() == 'stop':
                break
        except Exception as e:
            print(f"❌ Error: {str(e)}")