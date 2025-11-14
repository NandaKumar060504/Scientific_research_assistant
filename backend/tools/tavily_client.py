# # backend/tools/tavily_client.py
# import os
# import httpx
# from bs4 import BeautifulSoup
# import asyncio
# from typing import List, Dict

# TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "").strip()
# TAVILY_ENDPOINT = "https://api.tavily.com/search"

# async def search_tavily(query: str, num_results: int = 10, timeout: int = 15) -> List[Dict]:
#     """
#     Query Tavily (async). Returns a list of dicts: {title, snippet, url, published}.
#     If TAVILY_API_KEY is missing, falls back to a lightweight GitHub-trending scrape
#     for a few results to avoid total failure.
#     """
#     if not TAVILY_API_KEY:
#         # fallback: GitHub trending scraping (synchronous via httpx)
#         return await _fallback_github_trending(query, num_results, timeout)

#     # Tavily API requires POST with JSON body
#     payload = {
#         "api_key": TAVILY_API_KEY,
#         "query": query,
#         "max_results": num_results,
#         "search_depth": "basic",  # or "advanced" for more thorough results
#         "include_answer": False,
#         "include_raw_content": False
#     }
    
#     async with httpx.AsyncClient(timeout=timeout) as client:
#         try:
#             resp = await client.post(TAVILY_ENDPOINT, json=payload)
#             resp.raise_for_status()
#             data = resp.json()
            
#             # Tavily returns results in data['results']
#             results = []
#             items = data.get("results", [])
            
#             for it in items[:num_results]:
#                 results.append({
#                     "title": it.get("title", ""),
#                     "snippet": it.get("content", "") or it.get("snippet", ""),
#                     "url": it.get("url", ""),
#                     "published": it.get("published_date") or it.get("date") or None
#                 })
#             return results
#         except Exception as e:
#             # on failure, fallback gracefully
#             print(f"[tavily_client] Tavily request failed: {e} — falling back to GitHub trending.")
#             return await _fallback_github_trending(query, num_results, timeout)


# async def _fallback_github_trending(query: str, num_results: int, timeout: int):
#     """
#     Very small fallback: search GitHub trending page and return repo titles as 'results'.
#     This is *not* a replacement for Tavily but prevents the agent from crashing.
#     """
#     url = "https://github.com/trending"
#     async with httpx.AsyncClient(timeout=timeout) as client:
#         try:
#             r = await client.get(url, follow_redirects=True)
#             r.raise_for_status()
#             soup = BeautifulSoup(r.text, "html.parser")
#             results = []
            
#             # GitHub trending uses article.Box-row for each repo
#             items = soup.select("article.Box-row")[:num_results * 2]  # get more to filter
            
#             for it in items:
#                 try:
#                     # Find the repo title link
#                     title_link = it.select_one("h2 a")
#                     if not title_link:
#                         continue
                    
#                     title = title_link.get_text(strip=True).replace("\n", "").replace("  ", " ")
#                     href = "https://github.com" + title_link.get("href", "")
                    
#                     # Get description
#                     desc_tag = it.select_one("p")
#                     snippet = desc_tag.get_text(strip=True) if desc_tag else ""
                    
#                     results.append({
#                         "title": title,
#                         "snippet": snippet,
#                         "url": href,
#                         "published": None
#                     })
#                 except Exception as item_error:
#                     # Skip individual items that fail
#                     continue
            
#             # Filter results based on query
#             if query and results:
#                 qtokens = [t.lower() for t in query.split() if len(t) > 2][:4]
#                 filtered = [
#                     r for r in results 
#                     if any(q in (r["title"] + " " + r["snippet"]).lower() for q in qtokens)
#                 ]
#                 # Return filtered if we have enough results, otherwise return all
#                 return (filtered[:num_results] if len(filtered) >= 3 else results[:num_results])
            
#             return results[:num_results]
            
#         except Exception as e:
#             print(f"[tavily_client] Fallback GitHub scraping failed: {e}")
#             # Return some generic research-related results as last resort
#             return [
#                 {
#                     "title": "AI Research Trends 2024",
#                     "snippet": "Emerging research in artificial intelligence and machine learning",
#                     "url": "https://github.com/topics/research",
#                     "published": None
#                 },
#                 {
#                     "title": "Scientific Computing",
#                     "snippet": "Scientific research and computational methods",
#                     "url": "https://github.com/topics/scientific-computing",
#                     "published": None
#                 }
#             ]


# backend/tools/tavily_client.py
import os
import httpx
from bs4 import BeautifulSoup
import asyncio
from typing import List, Dict

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "").strip()
TAVILY_ENDPOINT = "https://api.tavily.com/search"

async def search_tavily(query: str, num_results: int = 10, timeout: int = 15) -> List[Dict]:
    """
    Query Tavily (async). Returns a list of dicts: {title, snippet, url, published}.
    If TAVILY_API_KEY is missing, falls back to a lightweight GitHub-trending scrape
    for a few results to avoid total failure.
    """
    if not TAVILY_API_KEY:
        # fallback: GitHub trending scraping (synchronous via httpx)
        return await _fallback_github_trending(query, num_results, timeout)

    # Tavily API requires POST with JSON body
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "max_results": num_results,
        "search_depth": "basic",  # or "advanced" for more thorough results
        "include_answer": False,
        "include_raw_content": False
    }
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(TAVILY_ENDPOINT, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            # Tavily returns results in data['results']
            results = []
            items = data.get("results", [])
            
            for it in items[:num_results]:
                results.append({
                    "title": it.get("title", ""),
                    "snippet": it.get("content", "") or it.get("snippet", ""),
                    "url": it.get("url", ""),
                    "published": it.get("published_date") or it.get("date") or None
                })
            return results
        except Exception as e:
            # on failure, fallback gracefully
            print(f"[tavily_client] Tavily request failed: {e} — falling back to GitHub trending.")
            return await _fallback_github_trending(query, num_results, timeout)


async def _fallback_github_trending(query: str, num_results: int, timeout: int):
    """
    Very small fallback: search GitHub trending page and return repo titles as 'results'.
    This is *not* a replacement for Tavily but prevents the agent from crashing.
    """
    url = "https://github.com/trending"
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            r = await client.get(url, follow_redirects=True)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            results = []
            
            # GitHub trending uses article.Box-row for each repo
            items = soup.select("article.Box-row")[:num_results * 2]  # get more to filter
            
            for it in items:
                try:
                    # Find the repo title link
                    title_link = it.select_one("h2 a")
                    if not title_link:
                        continue
                    
                    title = title_link.get_text(strip=True).replace("\n", "").replace("  ", " ")
                    href = "https://github.com" + title_link.get("href", "")
                    
                    # Get description
                    desc_tag = it.select_one("p")
                    snippet = desc_tag.get_text(strip=True) if desc_tag else ""
                    
                    results.append({
                        "title": title,
                        "snippet": snippet,
                        "url": href,
                        "published": None
                    })
                except Exception as item_error:
                    # Skip individual items that fail
                    continue
            
            # Filter results based on query
            if query and results:
                qtokens = [t.lower() for t in query.split() if len(t) > 2][:4]
                filtered = [
                    r for r in results 
                    if any(q in (r["title"] + " " + r["snippet"]).lower() for q in qtokens)
                ]
                # Return filtered if we have enough results, otherwise return all
                return (filtered[:num_results] if len(filtered) >= 3 else results[:num_results])
            
            return results[:num_results]
            
        except Exception as e:
            print(f"[tavily_client] Fallback GitHub scraping failed: {e}")
            # Return some generic research-related results as last resort
            return [
                {
                    "title": "AI Research Trends 2024",
                    "snippet": "Emerging research in artificial intelligence and machine learning",
                    "url": "https://github.com/topics/research",
                    "published": None
                },
                {
                    "title": "Scientific Computing",
                    "snippet": "Scientific research and computational methods",
                    "url": "https://github.com/topics/scientific-computing",
                    "published": None
                }
            ]