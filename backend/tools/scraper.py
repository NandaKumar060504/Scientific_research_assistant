# # backend/tools/scraper.py
# import os
# import httpx
# from bs4 import BeautifulSoup
# import asyncio
# from typing import List, Dict
# from urllib.parse import urljoin, urlparse
# from datetime import datetime, timedelta
# import random
# import re


# HEADERS = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
#     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
#     "Accept-Language": "en-US,en;q=0.5",
#     "Accept-Encoding": "gzip, deflate",
#     "Connection": "keep-alive",
#     "Upgrade-Insecure-Requests": "1"
# }


# # Rate limiter class for arXiv API
# class AsyncRateLimiter:
#     def __init__(self, calls_per_minute: int = 20):
#         self.calls_per_minute = calls_per_minute
#         self.calls = []
    
#     async def wait_if_needed(self):
#         now = datetime.now()
#         # Remove calls older than 1 minute
#         self.calls = [call_time for call_time in self.calls 
#                       if now - call_time < timedelta(minutes=1)]
        
#         if len(self.calls) >= self.calls_per_minute:
#             sleep_time = 60 - (now - self.calls[0]).total_seconds()
#             if sleep_time > 0:
#                 print(f"[RateLimiter] Waiting {sleep_time:.2f}s to respect rate limits...")
#                 await asyncio.sleep(sleep_time)
        
#         self.calls.append(now)


# # Create global rate limiter for arXiv (max 1 request per 3 seconds = 20 per minute)
# arxiv_limiter = AsyncRateLimiter(calls_per_minute=20)


# def clean_search_query(query: str) -> str:
#     """
#     Clean search query by removing prefixes like 'Fallback Q1:', 'Fallback Q2:', etc.
#     """
#     # Remove "Fallback Q[number]:" pattern
#     query = re.sub(r'Fallback\s+Q\d+:\s*', '', query, flags=re.IGNORECASE)
#     # Remove extra whitespace
#     query = ' '.join(query.split())
#     return query.strip()


# async def http_get(url: str, timeout: int = 15) -> str:
#     async with httpx.AsyncClient(timeout=timeout, headers=HEADERS, follow_redirects=True) as client:
#         r = await client.get(url)
#         r.raise_for_status()
#         return r.text


# async def search_arxiv(query: str, max_results: int = 5, retry_count: int = 3) -> List[Dict]:
#     """
#     Simple arXiv search via arXiv API (rss/xml) with rate limiting and retry logic
#     """
#     # Clean the query first
#     cleaned_query = clean_search_query(query)
#     print(f"[search_arxiv] Searching for: {cleaned_query}")
    
#     q = cleaned_query.replace(" ", "+")
#     url = f"https://export.arxiv.org/api/query?search_query=all:{q}&start=0&max_results={max_results}"
    
#     for attempt in range(retry_count):
#         try:
#             # Wait if we need to respect rate limits
#             await arxiv_limiter.wait_if_needed()
            
#             # Add a base delay of 3 seconds (arXiv recommendation)
#             if attempt == 0:
#                 await asyncio.sleep(3)
            
#             async with httpx.AsyncClient(timeout=30) as client:
#                 r = await client.get(url)
                
#                 # Handle rate limiting
#                 if r.status_code == 429:
#                     wait_time = (2 ** attempt) * 3 + random.uniform(0, 2)
#                     print(f"[search_arxiv] Rate limited (429). Waiting {wait_time:.2f}s before retry {attempt + 1}/{retry_count}...")
#                     await asyncio.sleep(wait_time)
#                     continue
                
#                 r.raise_for_status()
#                 text = r.text
            
#             # lightweight parse for id/title/summary/link
#             soup = BeautifulSoup(text, "lxml")
#             entries = []
            
#             for e in soup.find_all("entry")[:max_results]:
#                 title = e.title.text.strip() if e.title else ""
#                 summary = e.summary.text.strip() if e.summary else ""
#                 link = ""
                
#                 # find PDF link in links
#                 for l in e.find_all("link"):
#                     if l.get("title") == "pdf":
#                         link = l.get("href")
#                         break
                
#                 if not link:
#                     # fallback to id
#                     link = e.id.text if e.id else ""
                
#                 if title and link:  # Only add if we have title and link
#                     entries.append({"title": title, "summary": summary, "url": link})
            
#             print(f"[search_arxiv] Found {len(entries)} entries")
#             return entries
            
#         except httpx.HTTPStatusError as e:
#             if e.response.status_code == 429 and attempt < retry_count - 1:
#                 wait_time = (2 ** attempt) * 3 + random.uniform(0, 2)
#                 print(f"[search_arxiv] Rate limited. Waiting {wait_time:.2f}s before retry {attempt + 1}/{retry_count}...")
#                 await asyncio.sleep(wait_time)
#                 continue
#             else:
#                 print(f"[search_arxiv] HTTP Error (attempt {attempt + 1}/{retry_count}): {e}")
#                 if attempt == retry_count - 1:
#                     return []
#         except Exception as e:
#             print(f"[search_arxiv] Error (attempt {attempt + 1}/{retry_count}): {e}")
#             if attempt == retry_count - 1:
#                 return []
#             # Exponential backoff
#             await asyncio.sleep(2 ** attempt)
    
#     return []


# async def github_search_repos(query: str, max_results: int = 5) -> List[Dict]:
#     """
#     Search GitHub repositories with cleaned query
#     """
#     cleaned_query = clean_search_query(query)
#     print(f"[github_search_repos] Searching for: {cleaned_query}")
    
#     url = f"https://github.com/search?q={cleaned_query.replace(' ', '+')}&type=repositories"
#     try:
#         text = await http_get(url, timeout=15)
#     except Exception as e:
#         print(f"[github_search_repos] Error: {e}")
#         return []
    
#     soup = BeautifulSoup(text, "html.parser")
#     items = []
    
#     # Updated primary selector (based on current GitHub structure as of 2025)
#     for item in soup.select('div[data-testid="results-list"] > div.Box-sc-g0xbh4-0')[:max_results]:
#         title_tag = item.select_one('a.Link__StyledLink-sc-14289j-0')  # Common class for repo name link
#         if title_tag:
#             title = title_tag.get_text(strip=True)
#             href = urljoin("https://github.com", title_tag.get("href", ""))
#             desc_tag = item.select_one('p.color-fg-muted')  # Common for description
#             desc = desc_tag.get_text(strip=True) if desc_tag else ""
#             if href:
#                 items.append({"title": title, "description": desc, "url": href})
    
#     # Broader fallback if above fails
#     if not items:
#         for item in soup.select('li.repo-list-item')[:max_results]:  # Another common wrapper
#             title_tag = item.select_one('a')
#             if title_tag:
#                 title = title_tag.get_text(strip=True)
#                 href = urljoin("https://github.com", title_tag.get("href", ""))
#                 desc_tag = item.select_one('p')
#                 desc = desc_tag.get_text(strip=True) if desc_tag else ""
#                 if href:
#                     items.append({"title": title, "description": desc, "url": href})
    
#     print(f"[github_search_repos] Found {len(items)} repositories")
#     return items


# async def download_file(url: str, dest_folder: str, retry_count: int = 3) -> str:
#     """
#     Download a file (PDF/CSV/HTML) and return local path with retry logic.
#     """
#     os.makedirs(dest_folder, exist_ok=True)
    
#     try:
#         parsed = urlparse(url)
#         filename = os.path.basename(parsed.path) or "download"
        
#         # Ensure filename has extension
#         if "." not in filename:
#             if ".pdf" in url.lower():
#                 filename += ".pdf"
#             else:
#                 filename += ".html"
        
#         local = os.path.join(dest_folder, filename)
        
#         # Skip if already exists
#         if os.path.exists(local):
#             print(f"[download_file] File already exists: {local}")
#             return local
        
#         # Enhanced headers for better compatibility
#         headers = HEADERS.copy()
        
#         # Add referer for bioRxiv/medRxiv
#         if 'biorxiv.org' in url or 'medrxiv.org' in url:
#             headers['Referer'] = 'https://www.biorxiv.org/'
        
#         async with httpx.AsyncClient(timeout=60, headers=headers, follow_redirects=True) as client:
#             for attempt in range(retry_count):
#                 try:
#                     print(f"[download_file] Attempting download (attempt {attempt + 1}/{retry_count}): {url}")
                    
#                     # Add delay between retries
#                     if attempt > 0:
#                         wait_time = 2 ** attempt + random.uniform(0, 1)
#                         print(f"[download_file] Waiting {wait_time:.2f}s before retry...")
#                         await asyncio.sleep(wait_time)
                    
#                     r = await client.get(url)
#                     r.raise_for_status()
#                     break  # Success, exit retry loop
                    
#                 except httpx.HTTPStatusError as e:
#                     if e.response.status_code == 403:
#                         print(f"[download_file] 403 Forbidden (attempt {attempt + 1}/{retry_count})")
                        
#                         # For bioRxiv, try alternative URL format
#                         if 'biorxiv.org' in url and '.pdf' in url and attempt < retry_count - 1:
#                             # Try without .full.pdf or with different format
#                             if '.full.pdf' in url:
#                                 # Try just removing .full
#                                 alt_url = url.replace('.full.pdf', '.pdf')
#                                 print(f"[download_file] Trying alternative URL: {alt_url}")
#                                 url = alt_url
#                                 continue
                        
#                         if attempt < retry_count - 1:
#                             continue
#                         else:
#                             print(f"[download_file] All retry attempts failed with 403")
#                             return ""
                            
#                     elif e.response.status_code == 429:
#                         print(f"[download_file] Rate limited (429)")
#                         if attempt < retry_count - 1:
#                             wait_time = (2 ** attempt) * 2 + random.uniform(0, 2)
#                             await asyncio.sleep(wait_time)
#                             continue
#                         else:
#                             return ""
#                     else:
#                         print(f"[download_file] HTTP error {e.response.status_code}")
#                         return ""
                        
#                 except httpx.TimeoutException:
#                     print(f"[download_file] Timeout (attempt {attempt + 1}/{retry_count})")
#                     if attempt == retry_count - 1:
#                         return ""
#                     continue
                    
#                 except Exception as e:
#                     print(f"[download_file] Unexpected error (attempt {attempt + 1}/{retry_count}): {e}")
#                     if attempt == retry_count - 1:
#                         return ""
#                     continue
            
#             # Check if we got HTML or PDF
#             content_type = r.headers.get("content-type", "").lower()
            
#             if "pdf" in content_type or url.endswith(".pdf"):
#                 # Save as PDF
#                 with open(local, "wb") as f:
#                     f.write(r.content)
#                 print(f"[download_file] Successfully downloaded PDF: {local}")
#                 return local
#             else:
#                 # Save as HTML
#                 html_path = local if local.endswith(".html") else local.replace(".pdf", ".html")
#                 with open(html_path, "wb") as f:
#                     f.write(r.content)
#                 print(f"[download_file] Successfully downloaded HTML: {html_path}")
#                 return html_path
                
#     except Exception as e:
#         print(f"[download_file] Failed for {url} after {retry_count} attempts: {e}")
#         return ""


# # Helper: aggregate multiple sources for a query
# async def find_disparate_sources(query: str, max_sources: int = 6) -> List[Dict]:
#     """
#     Return a list of candidate sources: arXiv, GitHub.
#     Returns list of dicts with keys: type, title, url, snippet
#     """
#     cleaned_query = clean_search_query(query)
#     print(f"[find_disparate_sources] Searching for: {cleaned_query}")
    
#     # run arXiv and GitHub concurrently
#     arxiv_task = search_arxiv(cleaned_query, max_results=4)
#     gh_task = github_search_repos(cleaned_query, max_results=4)
    
#     results = await asyncio.gather(arxiv_task, gh_task, return_exceptions=True)
#     arxiv_res, gh_res = results[0], results[1]
    
#     sources = []
    
#     if isinstance(arxiv_res, list):
#         for r in arxiv_res:
#             if r.get("url"):  # Only add if has URL
#                 sources.append({
#                     "type": "arXiv",
#                     "title": r.get("title", ""),
#                     "url": r.get("url", ""),
#                     "snippet": r.get("summary", "")
#                 })
    
#     if isinstance(gh_res, list):
#         for r in gh_res:
#             if r.get("url"):  # Only add if has URL
#                 sources.append({
#                     "type": "github",
#                     "title": r.get("title", ""),
#                     "url": r.get("url", ""),
#                     "snippet": r.get("description", "")
#                 })
    
#     print(f"[find_disparate_sources] Found {len(sources)} sources")
#     return sources[:max_sources]

# backend/tools/scraper.py  (FULLY FIXED VERSION)

import os
import httpx
from bs4 import BeautifulSoup
import asyncio
from typing import List, Dict
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta
import random
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

COVID_KEYWORDS = [
    "covid", "sars", "pandemic", "corona", "repurposing",
    "virus", "antiviral", "lockdown", "outbreak"
]

def is_covid_related(text: str) -> bool:
    """Block any COVID-related paper or repo."""
    t = text.lower()
    return any(k in t for k in COVID_KEYWORDS)

def clean_search_query(query: str) -> str:
    """Strip fallback prefixes like 'Fallback Q1:'"""
    query = re.sub(r"Fallback\s+Q\d+:\s*", "", query, flags=re.IGNORECASE)
    return query.strip()


# ---------------- RATE LIMITER ----------------
class AsyncRateLimiter:
    def __init__(self, calls_per_minute: int = 20):
        self.calls_per_minute = calls_per_minute
        self.calls = []

    async def wait_if_needed(self):
        now = datetime.now()
        self.calls = [t for t in self.calls if now - t < timedelta(minutes=1)]
        if len(self.calls) >= self.calls_per_minute:
            sleep = 60 - (now - self.calls[0]).total_seconds()
            print(f"[RateLimiter] Sleeping {sleep:.1f}s")
            await asyncio.sleep(sleep)
        self.calls.append(now)


arxiv_limiter = AsyncRateLimiter(calls_per_minute=20)


# ---------------- HTTP GET ----------------
async def http_get(url: str, timeout: int = 15) -> str:
    async with httpx.AsyncClient(timeout=timeout, headers=HEADERS, follow_redirects=True) as c:
        r = await c.get(url)
        r.raise_for_status()
        return r.text


# ---------------- FIXED ARXIV SEARCH ----------------
async def search_arxiv(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search arXiv AND enforce:
    ❗ post-2024 papers only
    ❗ excludes COVID content
    """

    q = clean_search_query(query).replace(" ", "+")

    # enforce modern research (post-2024)
    url = (
        f"https://export.arxiv.org/api/query"
        f"?search_query=all:{q}+AND+submittedDate:[20240101+TO+30000101]"
        f"&start=0&max_results={max_results}"
    )

    print(f"[search_arxiv] Query: {url}")

    await arxiv_limiter.wait_if_needed()
    await asyncio.sleep(2)

    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get(url)
            r.raise_for_status()
            text = r.text

        soup = BeautifulSoup(text, "xml")

        entries = []
        for e in soup.find_all("entry")[:max_results]:
            title = e.title.text.strip()
            summary = e.summary.text.strip()
            published = e.published.text[:4]  # year

            if int(published) < 2024:
                continue

            if is_covid_related(title) or is_covid_related(summary):
                continue

            pdf_link = None
            for link in e.find_all("link"):
                if link.get("title") == "pdf":
                    pdf_link = link.get("href")
                    break

            if pdf_link:
                entries.append({
                    "title": title,
                    "summary": summary,
                    "year": published,
                    "url": pdf_link,
                })

        print(f"[search_arxiv] Filtered entries: {len(entries)}")
        return entries

    except Exception as e:
        print(f"[search_arxiv] ERROR: {e}")
        return []


# ---------------- FIXED GITHUB SEARCH ----------------
async def github_search_repos(query: str, max_results: int = 5) -> List[Dict]:
    """
    GitHub search FIX:
    - use GitHub API (works better than HTML parsing)
    - enforce post-2024 repositories
    - exclude COVID repos
    """

    q = clean_search_query(query)

    url = (
        "https://api.github.com/search/repositories"
        f"?q={q}+created:>2024-01-01"
        "&sort=stars&order=desc&per_page=5"
    )

    print(f"[github_search_repos] Query: {url}")

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/vnd.github+json"
    }

    try:
        async with httpx.AsyncClient(timeout=15, headers=headers) as c:
            r = await c.get(url)
            if r.status_code == 403:
                print("[github_search_repos] Rate limited by GitHub.")
                return []

            items = r.json().get("items", [])

        results = []
        for repo in items:
            name = repo["name"]
            desc = repo.get("description") or ""
            if is_covid_related(name) or is_covid_related(desc):
                continue

            results.append({
                "title": name,
                "url": repo["html_url"],
                "description": desc,
            })

        print(f"[github_search_repos] Filtered repos: {len(results)}")
        return results[:max_results]

    except Exception as e:
        print(f"[github_search_repos] ERROR: {e}")
        return []


# ---------------- DOWNLOAD ----------------
async def download_file(url: str, dest_folder: str) -> str:
    os.makedirs(dest_folder, exist_ok=True)
    filename = os.path.basename(urlparse(url).path)
    if not filename.endswith(".pdf"):
        filename += ".pdf"

    local_path = os.path.join(dest_folder, filename)

    if os.path.exists(local_path):
        return local_path

    try:
        async with httpx.AsyncClient(timeout=40, headers=HEADERS, follow_redirects=True) as c:
            r = await c.get(url)
            r.raise_for_status()

        with open(local_path, "wb") as f:
            f.write(r.content)

        print(f"[download_file] Saved → {local_path}")
        return local_path

    except Exception as e:
        print(f"[download_file] FAIL {e}")
        return ""


# ---------------- FIND SOURCES ----------------
async def find_disparate_sources(query: str, max_sources: int = 6) -> List[Dict]:
    """
    Combined arXiv + GitHub search
    with all filtering applied.
    """
    print(f"[find_disparate_sources] Searching for: {query}")

    cleaned = clean_search_query(query)

    arxiv_task = search_arxiv(cleaned, max_results=4)
    github_task = github_search_repos(cleaned, max_results=4)

    arxiv_res, github_res = await asyncio.gather(arxiv_task, github_task)

    results = []

    if arxiv_res:
        for r in arxiv_res:
            results.append({
                "type": "arXiv",
                "title": r["title"],
                "url": r["url"],
                "snippet": r["summary"],
            })

    if github_res:
        for r in github_res:
            results.append({
                "type": "github",
                "title": r["title"],
                "url": r["url"],
                "snippet": r["description"],
            })

    print(f"[find_disparate_sources] Total final sources: {len(results)}")
    return results[:max_sources]
