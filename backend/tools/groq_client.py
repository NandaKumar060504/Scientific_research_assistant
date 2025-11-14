# # backend/tools/groq_client.py

# import os
# import httpx
# import asyncio
# from typing import Optional, List

# GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
# GROQ_API_URL = os.getenv("GROQ_API_URL", "").strip()
# MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# async def call_groq(prompt: str, max_tokens: int = 1024, timeout: int = 40) -> Optional[str]:
#     """
#     Calls Groq using the OpenAI-compatible Chat Completions API.
#     Returns assistant message content or None.
#     """

#     if not GROQ_API_KEY or not GROQ_API_URL:
#         print("[groq_client] Missing GROQ_API_KEY or GROQ_API_URL.")
#         return None

#     headers = {
#         "Authorization": f"Bearer {GROQ_API_KEY}",
#         "Content-Type": "application/json",
#     }

#     payload = {
#         "model": MODEL_NAME,
#         "messages": [
#             {"role": "system", "content": "You are a scientific reasoning and analysis engine."},
#             {"role": "user", "content": prompt}
#         ],
#         "max_tokens": max_tokens,
#         "temperature": 0.2
#     }

#     # Retry 3 times
#     for attempt in range(3):
#         try:
#             async with httpx.AsyncClient(timeout=timeout) as client:
#                 resp = await client.post(GROQ_API_URL, json=payload, headers=headers)
#                 resp.raise_for_status()
#                 data = resp.json()

#                 # Correct field for Groq:
#                 return data["choices"][0]["message"]["content"]

#         except Exception as e:
#             wait = 1 + attempt * 2
#             print(f"[groq_client] Attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
#             await asyncio.sleep(wait)

#     print("[groq_client] All attempts failed.")
#     return None


# backend/tools/groq_client.py (replace call_groq)
import asyncio
import httpx
import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_API_URL = os.getenv("GROQ_API_URL", "").strip()
MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

async def call_groq(prompt: str, max_tokens: int = 1024, timeout: int = 40):
    if not GROQ_API_KEY or not GROQ_API_URL:
        print("[groq_client] Missing GROQ_API_KEY or GROQ_API_URL.")
        return None

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are a scientific reasoning and analysis engine."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2
    }

    for attempt in range(1, 6):  # 5 attempts
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(GROQ_API_URL, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else None
            if status == 429:
                wait = min(10, attempt * 2)
                print(f"[groq_client] 429 rate limit. Attempt {attempt}. Waiting {wait}s...")
                await asyncio.sleep(wait)
                continue
            print(f"[groq_client] HTTP error (attempt {attempt}): {e}")
        except Exception as e:
            wait = attempt * 2
            print(f"[groq_client] Attempt {attempt} failed: {e}. Retrying in {wait}s...")
            await asyncio.sleep(wait)

    print("[groq_client] All attempts failed.")
    return None
