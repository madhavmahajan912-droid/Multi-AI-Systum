import os
import json
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import google.generativeai as genai

# ==========================================
# WEB SEARCH AND SCRAPING TOOLS
# ==========================================

def search_web(query, max_results=4):
    """Queries DuckDuckGo search for the given query and returns list of results."""
    print(f"[Search Agent] Searching web for: '{query}'")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return [
                {
                    "title": r.get("title", "No Title"),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")
                }
                for r in results
            ]
    except Exception as e:
        print(f"[Search Agent] Error searching: {e}")
        return []

def scrape_url(url):
    """Scrapes content of a webpage and returns cleaned body text."""
    if not url:
        return ""
    print(f"[Scraper Agent] Scraping page: {url}")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code != 200:
            return f"Failed to fetch content, status code: {response.status_code}"
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove non-textual tags
        for element in soup(["script", "style", "header", "footer", "nav", "iframe", "noscript"]):
            element.decompose()
            
        # Get raw text
        text = soup.get_text()
        
        # Clean lines and spacing
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        cleaned_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Limit context size
        return cleaned_text[:3500]
    except Exception as e:
        return f"Error scraping page: {str(e)}"

# ==========================================
# AGENTS AND WORKFLOWS
# ==========================================

def run_fact_check(claim, api_key):
    """Orchestrates fact-checking agents to verify a news claim."""
    if not api_key:
        raise ValueError("Please configure your Gemini API Key in the sidebar.")
        
    genai.configure(api_key=api_key)
    json_model = genai.GenerativeModel(
        'gemini-3.5-flash',
        generation_config={"response_mime_type": "application/json"}
    )
    
    # Step 1: Fact-Checker suggests Search Queries
    planner_prompt = f"""You are a Fact-Checking Analyst. A user has requested verification of this claim:
"{claim}"

Draft 2 highly effective search queries to find debunking articles, verified facts, or authentic reports about this claim. 
Format your output strictly as a JSON list of strings.
Example:
[
  "claim topic fact check",
  "is claim topic true rumor"
]
"""
    response = json_model.generate_content(planner_prompt)
    try:
        queries = json.loads(response.text)
        if not isinstance(queries, list):
            queries = [claim]
    except Exception:
        queries = [claim]
        
    print(f"[Fact-Checker] Planned Search Queries: {queries}")
    
    # Step 2: Search & Gather Links
    all_links = []
    for query in queries:
        results = search_web(query, max_results=3)
        for r in results:
            if r["url"] and r["url"] not in [link["url"] for link in all_links]:
                all_links.append(r)
                
    if not all_links:
        all_links = search_web(claim, max_results=4)
        
    # Step 3: Scraping top links
    scraped_data = []
    sorted_links = sorted(
        all_links, 
        key=lambda k: 0 if any(x in k["url"].lower() for x in ["fact", "check", "news", "pib", "alt", "boom", "reuters", "apnews"]) else 1
    )
    
    for item in sorted_links[:3]:
        content = scrape_url(item["url"])
        if content and not content.startswith("Error") and not content.startswith("Failed"):
            scraped_data.append({
                "title": item["title"],
                "url": item["url"],
                "text": content
            })
            
    # Step 4: Analysis & Score Compilation
    scraping_context = ""
    for idx, item in enumerate(scraped_data):
        scraping_context += f"--- SOURCE {idx+1}: {item['title']} ({item['url']}) ---\n{item['text']}\n\n"
        
    analysis_prompt = f"""You are a Fact-Checking & Rumor-Detection Agent.
Analyze the claim: "{claim}"
Cross-reference this claim against the scraped search results provided below.

=== SCRAPED WEB SOURCES ===
{scraping_context if scraped_data else "No live web pages could be scraped. Rely on general knowledge but state no live sources were available."}
==========================

Return a JSON object matching this schema:
{{
  "verified_percentage": <int, 0 to 100>,
  "rumor_percentage": <int, 0 to 100>,
  "verdict": "'Verified' or 'Rumor/Fake' or 'Mixed' or 'Unverified'",
  "analysis": "<Markdown detailed analysis>",
  "rumor_details": "<Brief description of what the rumor states>",
  "sources": [
    {{"title": "Source Page Title", "url": "https://sourceurl.com"}}
  ]
}}
"""
    response = json_model.generate_content(analysis_prompt)
    try:
        analysis_result = json.loads(response.text)
        if not analysis_result.get("sources") and scraped_data:
            analysis_result["sources"] = [{"title": item["title"], "url": item["url"]} for item in scraped_data]
        return analysis_result
    except Exception as e:
        print(f"[Fact-Checker] Error compiling analysis: {e}")
        return {
            "verified_percentage": 0,
            "rumor_percentage": 100,
            "verdict": "Unverified",
            "analysis": f"Failed to parse analysis payload: {e}",
            "rumor_details": "Error in processing response.",
            "sources": [{"title": item["title"], "url": item["url"]} for item in scraped_data] if scraped_data else []
        }


def run_market_analysis(topic, api_key):
    """Orchestrates financial agents to search, scrape, and analyze stock/market news."""
    if not api_key:
        raise ValueError("Please configure your Gemini API Key in the sidebar.")
        
    genai.configure(api_key=api_key)
    json_model = genai.GenerativeModel(
        'gemini-3.5-flash',
        generation_config={"response_mime_type": "application/json"}
    )
    
    # Step 1: Financial Planner plans Search Queries
    planner_prompt = f"""You are a Senior Financial Market Planner. The user wants an analysis of:
"{topic}"

Define 2 search queries to get recent market trends or economic drivers.
Format output strictly as a JSON list of strings.
Example:
[
  "query 1",
  "query 2"
]
"""
    response = json_model.generate_content(planner_prompt)
    try:
        queries = json.loads(response.text)
        if not isinstance(queries, list):
            queries = [topic]
    except Exception:
        queries = [topic]
        
    print(f"[Financial Analyst] Planned Search Queries: {queries}")
    
    # Step 2: Search & Gather Links
    all_links = []
    for query in queries:
        results = search_web(query, max_results=3)
        for r in results:
            if r["url"] and r["url"] not in [link["url"] for link in all_links]:
                all_links.append(r)
                
    if not all_links:
        all_links = search_web(topic, max_results=4)
        
    # Step 3: Scraping top financial sources
    scraped_data = []
    sorted_links = sorted(
        all_links, 
        key=lambda k: 0 if any(x in k["url"].lower() for x in ["moneycontrol", "livemint", "bloomberg", "reuters", "economictimes", "financialexpress"]) else 1
    )
    
    for item in sorted_links[:3]:
        content = scrape_url(item["url"])
        if content and not content.startswith("Error") and not content.startswith("Failed"):
            scraped_data.append({
                "title": item["title"],
                "url": item["url"],
                "text": content
            })
            
    # Step 4: Synthesize Analysis
    scraping_context = ""
    for idx, item in enumerate(scraped_data):
        scraping_context += f"--- SOURCE {idx+1}: {item['title']} ({item['url']}) ---\n{item['text']}\n\n"
        
    analysis_prompt = f"""You are an Expert Stock Market and Financial Analyst.
Analyze topic: "{topic}"
Using scraped content:

=== SCRAPED WEB SOURCES ===
{scraping_context if scraped_data else "No live web pages could be scraped. Analyze based on current knowledge."}
==========================

Return a JSON object matching this schema:
{{
  "topic": "{topic}",
  "market_sentiment": "'Bullish' or 'Bearish' or 'Neutral' or 'Highly Volatile'",
  "summary": "<Markdown formatted detailed summary>",
  "key_triggers": [
    {{"trigger": "Trigger Title", "description": "Short explanation"}}
  ],
  "handy_takeaway": "<Crisp 1-2 sentence message>",
  "sources": [
    {{"title": "Source Page Title", "url": "https://sourceurl.com"}}
  ]
}}
"""
    response = json_model.generate_content(analysis_prompt)
    try:
        analysis_result = json.loads(response.text)
        if not analysis_result.get("sources") and scraped_data:
            analysis_result["sources"] = [{"title": item["title"], "url": item["url"]} for item in scraped_data]
        return analysis_result
    except Exception as e:
        print(f"[Financial Analyst] Error compiling market report: {e}")
        return {
            "topic": topic,
            "market_sentiment": "Neutral",
            "summary": f"Failed to compile report: {e}",
            "key_triggers": [],
            "handy_takeaway": "Error processing market intelligence.",
            "sources": [{"title": item["title"], "url": item["url"]} for item in scraped_data] if scraped_data else []
        }
