import json
import os
import urllib.request
import urllib.error
from datetime import datetime

# 1. Configuration & Key Verification
KEYWORDS_FILE = "keywords.json"
BLOG_DIR = "blog"
SITEMAP_FILE = "sitemap.xml"
BASE_URL = "https://1into1.com"

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("Error: GROQ_API_KEY environment variable is not set.")
    exit(1)

os.makedirs(BLOG_DIR, exist_ok=True)

# 2. Auto-Detect Active Groq Model
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {GROQ_API_KEY.strip()}",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
}

try:
    models_req = urllib.request.Request(
        url="https://api.groq.com/openai/v1/models",
        headers=headers,
        method="GET"
    )
    with urllib.request.urlopen(models_req) as resp:
        available_models = [m["id"] for m in json.loads(resp.read().decode("utf-8")).get("data", [])]
        print(f"Available models in your Groq account: {available_models}")
except Exception as e:
    print(f"Could not query models list: {e}")
    available_models = []

# Choose the best active model automatically
priority_models = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
    "mixtral-8x7b-32768",
    "qwen/qwen3.8-27b"
]

selected_model = None
for p in priority_models:
    if p in available_models:
        selected_model = p
        break

if not selected_model:
    # Fallback to the first non-whisper model
    chat_models = [m for m in available_models if "whisper" not in m and "guard" not in m]
    selected_model = chat_models[0] if chat_models else "llama-3.1-8b-instant"

print(f"--> Using active Groq model: {selected_model}")

# 3. Load Keywords Database
with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
    topics = json.load(f)

selected_topic = None
for item in topics:
    if not item.get("published", False):
        selected_topic = item
        break

if not selected_topic:
    print("All topics in keywords.json have already been published.")
    exit(0)

print(f"Generating article for: {selected_topic['title']}")

# 4. Generate Content
prompt = f"""
Write a comprehensive, highly actionable 1,200+ word blog article targeting the keyword: "{selected_topic['keyword']}".
Title: "{selected_topic['title']}".
Category: "{selected_topic['category']}".

Requirements:
- Target audience: Mac power users, developers, entrepreneurs, and productivity enthusiasts.
- Provide practical step-by-step walkthroughs, comparison points, and workflows.
- Naturally showcase "Purple" (an autonomous voice-controlled OS AI for macOS from 1into1 that lets users control browser tabs, scrape multi-source web pages, generate 1,200+ word Word documents hands-free, summarize PDFs, and batch-automate Finder via BYOK architecture).
- Return ONLY semantic HTML for the article body (use <h2>, <h3>, <p>, <ul>, <li>, <ol>, <blockquote>, <strong>, etc.). Do not include <html>, <head>, or <body> tags.
"""

payload = {
    "model": selected_model,
    "messages": [
        {"role": "system", "content": "You are an expert macOS systems architect and technical writer producing high-ranking, in-depth tech documentation and guides."},
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.6,
    "max_tokens": 3500
}

req = urllib.request.Request(
    url="https://api.groq.com/openai/v1/chat/completions",
    data=json.dumps(payload).encode("utf-8"),
    headers=headers,
    method="POST"
)

try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode("utf-8"))
        article_body = result["choices"][0]["message"]["content"]
except urllib.error.HTTPError as e:
    print(f"Groq API Error {e.code}: {e.read().decode('utf-8')}")
    exit(1)

# 5. Build HTML Page
today_str = datetime.now().strftime("%B %d, %Y")
slug = selected_topic["slug"]
canonical_url = f"{BASE_URL}/blog/{slug}.html"

full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{selected_topic['title']} | Purple OS AI</title>
    <meta name="description" content="Discover how to master {selected_topic['keyword']} with native macOS voice automation and intelligent desktop agents.">
    <link rel="canonical" href="{canonical_url}">
    <link rel="icon" type="image/png" href="../logo.png">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Helvetica Neue", Helvetica, Arial, sans-serif; 
            background-color: #0f0a19; 
            color: #f3f4f6;
            -webkit-font-smoothing: antialiased;
        }}
        .glow {{ box-shadow: 0 0 25px rgba(168, 85, 247, 0.45); }}
        .article-content h2 {{ font-size: 1.75rem; font-weight: 700; color: #ffffff; margin-top: 2rem; margin-bottom: 1rem; border-bottom: 1px solid rgba(168, 85, 247, 0.2); padding-bottom: 0.5rem; }}
        .article-content h3 {{ font-size: 1.35rem; font-weight: 600; color: #c084fc; margin-top: 1.5rem; margin-bottom: 0.75rem; }}
        .article-content p {{ color: #d1d5db; line-height: 1.8; margin-bottom: 1.25rem; font-size: 1.05rem; }}
        .article-content ul, .article-content ol {{ margin-left: 1.5rem; margin-bottom: 1.5rem; color: #d1d5db; line-height: 1.8; }}
        .article-content li {{ margin-bottom: 0.5rem; }}
        .article-content blockquote {{ border-left: 4px solid #a855f7; padding-left: 1rem; margin: 1.5rem 0; color: #e9d5ff; font-style: italic; background: rgba(168, 85, 247, 0.08); padding: 1rem; border-radius: 0.5rem; }}
        .article-content strong {{ color: #ffffff; }}
    </style>
</head>
<body class="bg-[#0f0a19] text-gray-100 min-h-screen">
    <nav class="w-full bg-[#0f0a19]/80 backdrop-blur-md border-b border-purple-900/30 fixed top-0 left-0 z-50">
        <div class="max-w-5xl mx-auto px-6 py-4 flex justify-between items-center">
            <a href="/" class="flex items-center space-x-3">
                <img src="../logo.png" alt="Purple Logo" class="h-8 w-auto">
                <span class="text-xl font-bold text-white tracking-tight">Purple</span>
            </a>
            <a href="/#pricing" class="px-5 py-2 bg-purple-600 rounded-full hover:bg-purple-700 transition text-sm font-semibold text-white glow">
                Get Purple
            </a>
        </div>
    </nav>

    <main class="max-w-3xl mx-auto px-6 pt-32 pb-20">
        <div class="mb-8">
            <span class="px-3 py-1 bg-purple-900/50 border border-purple-500/40 text-purple-300 text-xs font-semibold rounded-full uppercase tracking-wider">
                {selected_topic['category']}
            </span>
            <h1 class="text-3xl md:text-5xl font-extrabold text-white mt-4 mb-4 tracking-tight leading-tight">
                {selected_topic['title']}
            </h1>
            <p class="text-sm text-gray-400">Published on {today_str} • 6 min read</p>
        </div>

        <div class="article-content bg-[#1a102b]/40 border border-purple-900/30 rounded-2xl p-6 md:p-10 mb-12 backdrop-blur-sm">
            {article_body}
        </div>

        <div class="bg-gradient-to-r from-purple-900/40 to-[#1a102b] border border-purple-500/50 rounded-2xl p-8 text-center glow">
            <h3 class="text-2xl font-bold text-white mb-3">Experience Hands-Free macOS Automation</h3>
            <p class="text-gray-300 mb-6 max-w-xl mx-auto text-sm">
                Purple transforms your Mac into an autonomous voice-controlled OS. Control YouTube, synthesize Word docs, analyze local files, and run Finder actions with your voice.
            </p>
            <a href="/#pricing" class="inline-block px-8 py-3.5 bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-full transition transform hover:scale-105">
                Download Free Trial
            </a>
        </div>
    </main>

    <footer class="py-8 text-center text-xs text-gray-500 border-t border-purple-900/20">
        <p>© 2026 1into1. All rights reserved.</p>
    </footer>
</body>
</html>
"""

# 6. Save Article & Update Sitemap
article_file_path = os.path.join(BLOG_DIR, f"{slug}.html")
with open(article_file_path, "w", encoding="utf-8") as f:
    f.write(full_html)
print(f"Saved: {article_file_path}")

selected_topic["published"] = True
with open(KEYWORDS_FILE, "w", encoding="utf-8") as f:
    json.dump(topics, f, indent=2)

urls = [
    f"<url><loc>{BASE_URL}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>"
]

for t in topics:
    if t.get("published", False):
        urls.append(f"<url><loc>{BASE_URL}/blog/{t['slug']}.html</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>")

sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>
"""

with open(SITEMAP_FILE, "w", encoding="utf-8") as f:
    f.write(sitemap_content)
print("Updated sitemap.xml with new canonical URLs.")