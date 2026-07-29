import os
import re
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
        # Fallback to search query scraping if DDG API fails (a simple simulation/stub or empty)
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
        
        # Limit to 3500 characters to prevent overloading agent's context window
        return cleaned_text[:3500]
    except Exception as e:
        return f"Error scraping page: {str(e)}"

# ==========================================
# UTILITY: JSON PARSING FROM LLM
# ==========================================

def extract_json(text):
    """Extracts and parses JSON object from LLM response text."""
    # Find block of ```json ... ```
    match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception as e:
            print(f"[Parser] Failed parsing json block: {e}")
            
    # Try parsing the whole text
    try:
        return json.loads(text)
    except Exception:
        pass
        
    # Find start and end brackets
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end+1])
        except Exception as e:
            print(f"[Parser] Failed parsing bracket range: {e}")
            
    raise ValueError("Could not parse a valid JSON payload from the Agent output.")

# ==========================================
# AGENTS AND WORKFLOWS
# ==========================================

def run_fact_check(claim, api_key):
    """Orchestrates fact-checking agents to verify a news claim.
    
    Returns:
        dict: Containing verification scores, verdict, reasoning, and sources.
    """
    if not api_key:
        raise ValueError("Please configure your Gemini API Key in the sidebar.")
        
    genai.configure(api_key=api_key)
    
    # ----------------------------------------------------
    # Step 1: Fact-Checker suggests Search Queries
    # ----------------------------------------------------
    planner_prompt = f"""You are a Fact-Checking Analyst. A user has requested verification of this claim:
"{claim}"

Draft 2 highly effective search queries to find debunking articles, verified facts, or authentic reports about this claim. 
Format your output strictly as a JSON list of strings.
Example:
[
  "claim topic fact check",
  "is claim topic true rumor"
]
Do not write anything else besides the JSON block.
"""
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(planner_prompt)
    
    try:
        queries = extract_json(response.text)
        if not isinstance(queries, list):
            queries = [claim]
    except Exception:
        queries = [claim]
        
    print(f"[Fact-Checker] Planned Search Queries: {queries}")
    
    # ----------------------------------------------------
    # Step 2: Search & Gather Links
    # ----------------------------------------------------
    all_links = []
    for query in queries:
        results = search_web(query, max_results=3)
        for r in results:
            if r["url"] and r["url"] not in [link["url"] for link in all_links]:
                all_links.append(r)
                
    if not all_links:
        # Fallback to direct claim search
        results = search_web(claim, max_results=4)
        all_links = results
        
    # ----------------------------------------------------
    # Step 3: Scraping top links (up to 3)
    # ----------------------------------------------------
    scraped_data = []
    # Prioritize URLs containing 'fact' or known news agencies if possible
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
            
    # ----------------------------------------------------
    # Step 4: Analysis & Score Compilation
    # ----------------------------------------------------
    scraping_context = ""
    for idx, item in enumerate(scraped_data):
        scraping_context += f"--- SOURCE {idx+1}: {item['title']} ({item['url']}) ---\n{item['text']}\n\n"
        
    analysis_prompt = f"""You are a Fact-Checking & Rumor-Detection Agent.
Your task is to analyze the claim: "{claim}"
Cross-reference this claim against the scraped search results provided below.

=== SCRAPED WEB SOURCES ===
{scraping_context if scraped_data else "No live web pages could be scraped. Rely on your general knowledge but state that no live source was available."}
==========================

Determine:
1. What percentage this news is verified from authentic news websites (0% to 100%).
2. How much this news is rumors/fake (0% to 100%).
3. A clear Verdict: 'Verified' (mostly true), 'Rumor/Fake' (mostly false), 'Mixed' (partially true/misleading), or 'Unverified' (lack of evidence).
4. A detailed markdown analysis explaining the facts, what the rumor says, and why the scores were given.
5. List of URLs used for verification.

You MUST format your output strictly as a JSON object with the following schema:
{{
  "verified_percentage": <int, e.g. 85>,
  "rumor_percentage": <int, e.g. 15>,
  "verdict": "<Verdict String>",
  "analysis": "<Markdown analysis detailing why>",
  "rumor_details": "<Brief description of what the rumor states>",
  "sources": [
    {{"title": "Source Page Title", "url": "https://sourceurl.com"}}
  ]
}}

Keep the analysis concise, factual, and professional. Return only the JSON.
"""
    
    response = model.generate_content(analysis_prompt)
    try:
        analysis_result = extract_json(response.text)
        # Ensure fallback sources if empty
        if not analysis_result.get("sources") and scraped_data:
            analysis_result["sources"] = [{"title": item["title"], "url": item["url"]} for item in scraped_data]
        return analysis_result
    except Exception as e:
        print(f"[Fact-Checker] Error compiling analysis: {e}")
        # Return fallback dictionary
        return {
            "verified_percentage": 0,
            "rumor_percentage": 100,
            "verdict": "Unverified",
            "analysis": f"Failed to parse agent response automatically. Raw Response:\n\n{response.text}",
            "rumor_details": "Error in agent communication.",
            "sources": [{"title": item["title"], "url": item["url"]} for item in scraped_data] if scraped_data else []
        }

def run_market_analysis(topic, api_key):
    """Orchestrates financial agents to search, scrape, and analyze stock/market news.
    
    Returns:
        dict: Structured financial report.
    """
    if not api_key:
        raise ValueError("Please configure your Gemini API Key in the sidebar.")
        
    genai.configure(api_key=api_key)
    
    # ----------------------------------------------------
    # Step 1: Financial Planner plans Search Queries
    # ----------------------------------------------------
    planner_prompt = f"""You are a Senior Financial Market Planner. The user wants an analysis of:
"{topic}"

Define 2 search queries to get the most recent, valid points, and market opinions (e.g. Rupee downgrades, stock index trends, market movements, economic drivers).
Format your output strictly as a JSON list of strings.
Example:
[
  "query 1",
  "query 2"
]
Do not write anything else besides the JSON.
"""
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(planner_prompt)
    
    try:
        queries = extract_json(response.text)
        if not isinstance(queries, list):
            queries = [topic]
    except Exception:
        queries = [topic]
        
    print(f"[Financial Analyst] Planned Search Queries: {queries}")
    
    # ----------------------------------------------------
    # Step 2: Search & Gather Links
    # ----------------------------------------------------
    all_links = []
    for query in queries:
        results = search_web(query, max_results=3)
        for r in results:
            if r["url"] and r["url"] not in [link["url"] for link in all_links]:
                all_links.append(r)
                
    if not all_links:
        all_links = search_web(topic, max_results=4)
        
    # ----------------------------------------------------
    # Step 3: Scraping top financial sources (up to 3)
    # ----------------------------------------------------
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
            
    # ----------------------------------------------------
    # Step 4: Synthesize Analysis & Handy Summary
    # ----------------------------------------------------
    scraping_context = ""
    for idx, item in enumerate(scraped_data):
        scraping_context += f"--- SOURCE {idx+1}: {item['title']} ({item['url']}) ---\n{item['text']}\n\n"
        
    analysis_prompt = f"""You are an Expert Stock Market and Financial Analyst.
Analyze the user's topic: "{topic}"
Using the scraped news/market content below:

=== SCRAPED WEB SOURCES ===
{scraping_context if scraped_data else "No live web pages could be scraped. Analyze based on your current knowledge of market trends."}
==========================

Task:
1. Write a short, understandable, and high-value summary of the topic.
2. Outline key drivers/triggers (e.g. interest rates, global oil prices, foreign portfolio outflows, company earnings, inflation).
3. State current Market Sentiment: 'Bullish', 'Bearish', 'Neutral', or 'Highly Volatile'.
4. Synthesize a "Handy Takeaway" - a very short, crisp, 1-2 sentence message keeping the summary handy for others.

Format your output strictly as a JSON object with the following schema:
{{
  "topic": "{topic}",
  "market_sentiment": "<Sentiment String>",
  "summary": "<Markdown formatted detailed summary>",
  "key_triggers": [
    {{"trigger": "Trigger Title", "description": "Short explanation of impact"}}
  ],
  "handy_takeaway": "<Crisp 1-2 sentence message>",
  "sources": [
    {{"title": "Source Page Title", "url": "https://sourceurl.com"}}
  ]
}}

Ensure all points are valid, readable, and economically sound. Do not return anything else except the JSON.
"""
    
    response = model.generate_content(analysis_prompt)
    try:
        analysis_result = extract_json(response.text)
        if not analysis_result.get("sources") and scraped_data:
            analysis_result["sources"] = [{"title": item["title"], "url": item["url"]} for item in scraped_data]
        return analysis_result
    except Exception as e:
        print(f"[Financial Analyst] Error compiling market report: {e}")
        return {
            "topic": topic,
            "market_sentiment": "Neutral",
            "summary": f"Failed to automatically compile the market report. Raw Response:\n\n{response.text}",
            "key_triggers": [],
            "handy_takeaway": "Error processing market intelligence.",
            "sources": [{"title": item["title"], "url": item["url"]} for item in scraped_data] if scraped_data else []
        }
