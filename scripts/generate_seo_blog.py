import os
import json
import re
from datetime import datetime
from groq import Groq

# 1. Configuration & Directories
KEYWORDS_FILE = "keywords.json"
BLOG_DIR = "blog"
SITEMAP_FILE = "sitemap.xml"
BLOG_INDEX_FILE = os.path.join(BLOG_DIR, "index.html")
BASE_URL = "https://1into1.com"

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("Error: GROQ_API_KEY environment variable is not set.")
    exit(1)

client = Groq(api_key=GROQ_API_KEY.strip())
os.makedirs(BLOG_DIR, exist_ok=True)

# 2. Dynamic Live Model Detection
try:
    models_response = client.models.list()
    available_models = [m.id for m in models_response.data]
    print(f"Active Groq models: {available_models}")
except Exception as e:
    available_models = []

priority_preference = [
    "llama-3.1-70b-versatile",
    "llama3-70b-8192",
    "llama-3.2-90b-text-preview",
    "llama-3.1-8b-instant",
    "llama3-8b-8192"
]

selected_model = None
for pref in priority_preference:
    if pref in available_models:
        selected_model = pref
        break

if not selected_model:
    chat_models = [
        m for m in available_models 
        if not any(x in m.lower() for x in ["whisper", "guard", "vision", "embed"])
    ]
    selected_model = chat_models[0] if chat_models else "llama3-8b-8192"

print(f"--> Using live verified Groq model: {selected_model}")

def call_groq(messages, temperature=0.5, max_tokens=5000):
    response = client.chat.completions.create(
        model=selected_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content

def sanitize_html_output(raw_text):
    """Strips all AI thinking traces, preambles, markdown artifacts, and fences."""
    text = raw_text.strip()
    # Remove <think>...</think> blocks
    text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
    # Remove 'Here is a thinking process...' or markdown intros
    text = re.sub(r"^.*?Here(?:'s| is) a thinking process:?[\s\S]*?(?=<h[1-6]|<p|<div|<article)", "", text, flags=re.IGNORECASE)
    # Remove markdown code block fences
    text = re.sub(r"^```(?:html)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text.strip())
    return text.strip()

# 3. Load & Auto-Replenish Keywords
with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
    topics = json.load(f)

pending_topics = [t for t in topics if not t.get("published", False)]

if len(pending_topics) < 2:
    print("Keyword queue low. Generating 10 new SEO keywords...")
    existing_titles = [t["title"] for t in topics]
    
    prompt_topics = f"""
You are an expert SEO Strategist for Purple (https://1into1.com), an autonomous voice-controlled OS AI for macOS.

Recently generated titles (DO NOT REPEAT):
{json.dumps(existing_titles[-25:], indent=2)}

Generate 10 BRAND NEW, high-ranking, unique SEO topics for macOS users, developers, and power users.
Focus on:
- macOS voice automation and terminal workflow shortcuts
- Hands-free document drafting, PDF analysis, and spreadsheet math
- Desktop AI agents vs cloud chatbots
- Privacy, Bring-Your-Own-Key (BYOK) architecture
- Spotify/media playback by voice, automated web scraping, window management

Return STRICTLY a JSON array of 10 objects with keys: "slug", "keyword", "title", "category", "published".
Set "published": false for all. Ensure slugs are URL-safe with hyphens only.
Output pure JSON only. No preamble, no thinking block, no markdown formatting.
"""
    try:
        raw_json = call_groq([
            {"role": "system", "content": "You output only pure, raw JSON without any markdown formatting or commentary."},
            {"role": "user", "content": prompt_topics}
        ], temperature=0.7, max_tokens=2000)
        
        raw_json = re.sub(r"^```(?:json)?\s*", "", raw_json.strip())
        raw_json = re.sub(r"\s*```$", "", raw_json.strip())
        new_topics = json.loads(raw_json)
        
        topics.extend(new_topics)
        with open(KEYWORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(topics, f, indent=2)
        print(f"Successfully added {len(new_topics)} new topics to queue.")
    except Exception as e:
        print(f"Topic auto-generation error: {e}")

selected_topic = None
for item in topics:
    if not item.get("published", False):
        selected_topic = item
        break

# 4. Generate 1,200+ Word Clean SEO Guide
if selected_topic:
    print(f"Generating clean, high-ranking SEO article for: {selected_topic['title']}")
    today_str = datetime.now().strftime("%B %d, %Y")
    slug = selected_topic["slug"]
    canonical_url = f"{BASE_URL}/blog/{slug}.html"

    prompt_article = f"""
Write an authoritative, highly comprehensive 1,200+ word technical guide and tutorial targeting the primary search keyword: "{selected_topic['keyword']}".
Title: "{selected_topic['title']}".
Category: "{selected_topic['category']}".

SEO & Structural Requirements:
1. Word Count: 1,200+ words of actionable content.
2. Structure:
   - Compelling introduction explaining the core problem and workflow transition.
   - At least 4 detailed <h2> sections with descriptive <h3> sub-headings.
   - Practical step-by-step implementation guide with real macOS terminal/voice commands.
   - A comparison breakdown or workflow pros/cons list.
   - A dedicated <h2>Frequently Asked Questions</h2> section answering 3 real user search questions.
3. Natural Product Integration: Highlight "Purple" (https://1into1.com) as the native voice-driven autonomous OS AI for macOS that executes browser workflows, scrapes web data, drafts Word documents hands-free, summarizes PDFs, and automates Finder tasks securely with BYOK architecture.
4. CRITICAL OUTPUT FORMAT RULE:
   - Output ONLY the raw semantic HTML for the article body (<h2>, <h3>, <p>, <ul>, <ol>, <li>, <blockquote>, <pre><code>, <strong>).
   - DO NOT include <!DOCTYPE>, <html>, <head>, or <body> tags.
   - DO NOT write any thought process, introduction, or "Here is...". Start directly with the first <h2> or <p> tag.
"""

    raw_article = call_groq([
        {"role": "system", "content": "You are a senior macOS systems architect and lead technical writer. You output ONLY valid inner semantic HTML. You NEVER output thinking processes, greetings, or conversational preambles."},
        {"role": "user", "content": prompt_article}
    ], temperature=0.4, max_tokens=5000)

    article_body = sanitize_html_output(raw_article)

    # Inject JSON-LD Schema
    schema_json = json.dumps({
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": selected_topic['title'],
        "description": f"Learn how to master {selected_topic['keyword']} with native macOS voice commands and desktop AI automation.",
        "author": {
            "@type": "Organization",
            "name": "Purple AI",
            "url": BASE_URL
        },
        "publisher": {
            "@type": "Organization",
            "name": "1into1",
            "logo": {
                "@type": "ImageObject",
                "url": f"{BASE_URL}/logo.png"
            }
        },
        "datePublished": datetime.now().strftime("%Y-%m-%d"),
        "mainEntityOfPage": canonical_url
    }, indent=2)

    article_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{selected_topic['title']} | Purple OS AI</title>
    <meta name="description" content="Discover how to master {selected_topic['keyword']} with native macOS voice automation and intelligent desktop agents.">
    <link rel="canonical" href="{canonical_url}">
    <link rel="icon" type="image/png" href="../logo.png">
    <script src="https://cdn.tailwindcss.com"></script>
    
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-W7WZRVJE0Z"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', 'G-W7WZRVJE0Z');
    </script>

    <script type="application/ld+json">
    {schema_json}
    </script>

    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", sans-serif; background-color: #0f0a19; color: #f3f4f6; }}
        .glow {{ box-shadow: 0 0 25px rgba(168, 85, 247, 0.45); }}
        .article-content h2 {{ font-size: 1.75rem; font-weight: 700; color: #ffffff; margin-top: 2.5rem; margin-bottom: 1rem; border-bottom: 1px solid rgba(168, 85, 247, 0.25); padding-bottom: 0.5rem; }}
        .article-content h3 {{ font-size: 1.35rem; font-weight: 600; color: #c084fc; margin-top: 1.75rem; margin-bottom: 0.75rem; }}
        .article-content p {{ color: #d1d5db; line-height: 1.85; margin-bottom: 1.25rem; font-size: 1.05rem; }}
        .article-content ul, .article-content ol {{ margin-left: 1.5rem; margin-bottom: 1.5rem; color: #d1d5db; line-height: 1.85; }}
        .article-content li {{ margin-bottom: 0.5rem; }}
        .article-content blockquote {{ border-left: 4px solid #a855f7; padding: 1rem 1.25rem; margin: 1.5rem 0; color: #e9d5ff; font-style: italic; background: rgba(168, 85, 247, 0.08); border-radius: 0.5rem; }}
        .article-content pre {{ background: #140d24; border: 1px solid rgba(168, 85, 247, 0.25); padding: 1.25rem; border-radius: 0.75rem; overflow-x: auto; margin: 1.5rem 0; }}
        .article-content code {{ color: #f3e8ff; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 0.95rem; }}
        .article-content strong {{ color: #ffffff; }}
    </style>
</head>
<body class="bg-[#0f0a19] text-gray-100 min-h-screen">
    <nav class="w-full bg-[#0f0a19]/80 backdrop-blur-md border-b border-purple-900/30 fixed top-0 left-0 z-50">
        <div class="max-w-5xl mx-auto px-6 py-4 flex justify-between items-center">
            <a href="/" class="flex items-center space-x-3">
                <img src="../logo.png" alt="Purple Logo" class="h-8 w-auto drop-shadow-[0_0_10px_rgba(168,85,247,0.6)]">
                <span class="text-xl font-bold text-white tracking-tight">Purple</span>
            </a>
            <div class="flex items-center space-x-6">
                <a href="/blog/" class="text-gray-300 hover:text-white transition text-sm font-medium">All Guides</a>
                <a href="/#pricing" class="px-5 py-2 bg-purple-600 rounded-full hover:bg-purple-700 transition text-sm font-semibold text-white glow">Get Purple</a>
            </div>
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
                Purple transforms your Mac into an autonomous voice-controlled OS. Control your browser, synthesize documents, and run automated workflows with your voice.
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
    article_file_path = os.path.join(BLOG_DIR, f"{slug}.html")
    with open(article_file_path, "w", encoding="utf-8") as f:
        f.write(article_html)
    print(f"Saved: {article_file_path}")

    selected_topic["published"] = True
    selected_topic["published_date"] = today_str
    with open(KEYWORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(topics, f, indent=2)

# 5. Rebuild Blog Hub
published_posts = [t for t in topics if t.get("published", False)]
cards_html = ""

for post in reversed(published_posts):
    p_date = post.get("published_date", "Recently Added")
    cards_html += f"""
    <a href="/blog/{post['slug']}.html" class="block bg-[#1a102b]/60 border border-purple-900/40 hover:border-purple-500/60 rounded-2xl p-6 transition-all duration-200 transform hover:-translate-y-1 hover:shadow-lg hover:shadow-purple-900/30">
        <div class="flex items-center justify-between mb-3">
            <span class="px-3 py-0.5 bg-purple-900/50 border border-purple-500/30 text-purple-300 text-xs font-semibold rounded-full uppercase tracking-wider">
                {post['category']}
            </span>
            <span class="text-xs text-gray-400">{p_date}</span>
        </div>
        <h2 class="text-xl font-bold text-white mb-2 leading-snug">{post['title']}</h2>
        <p class="text-gray-300 text-sm line-clamp-2 mb-4">Learn how to leverage native macOS architecture and voice-driven agentic workflows for {post['keyword']}.</p>
        <div class="text-purple-400 text-xs font-semibold flex items-center space-x-1">
            <span>Read Guide</span>
            <span>&rarr;</span>
        </div>
    </a>
    """

blog_index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>macOS Automation & AI Guides | Purple Blog</title>
    <meta name="description" content="Official technical guides, tutorials, and workflows for voice-controlled macOS automation, productivity, and desktop AI agents.">
    <link rel="canonical" href="{BASE_URL}/blog/">
    <link rel="icon" type="image/png" href="../logo.png">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", sans-serif; background-color: #0f0a19; color: #f3f4f6; }}
        .glow {{ box-shadow: 0 0 25px rgba(168, 85, 247, 0.45); }}
    </style>
</head>
<body class="bg-[#0f0a19] text-gray-100 min-h-screen">
    <nav class="w-full bg-[#0f0a19]/80 backdrop-blur-md border-b border-purple-900/30 fixed top-0 left-0 z-50">
        <div class="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
            <a href="/" class="flex items-center space-x-3">
                <img src="../logo.png" alt="Purple Logo" class="h-8 w-auto">
                <span class="text-xl font-bold text-white tracking-tight">Purple</span>
            </a>
            <div class="flex items-center space-x-6">
                <a href="/" class="text-gray-300 hover:text-white transition text-sm font-medium">Home</a>
                <a href="/#pricing" class="px-5 py-2 bg-purple-600 rounded-full hover:bg-purple-700 transition text-sm font-semibold text-white glow">Get Purple</a>
            </div>
        </div>
    </nav>

    <main class="max-w-6xl mx-auto px-6 pt-32 pb-20">
        <div class="text-center max-w-2xl mx-auto mb-16">
            <span class="px-3 py-1 bg-purple-900/50 border border-purple-500/40 text-purple-300 text-xs font-semibold rounded-full uppercase tracking-wider">
                Resources & Tutorials
            </span>
            <h1 class="text-4xl md:text-5xl font-extrabold text-white mt-4 mb-4 tracking-tight">
                macOS Automation Guides
            </h1>
            <p class="text-gray-400 text-base">
                Discover step-by-step guides on voice control, desktop agent automation, and macOS power workflows.
            </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {cards_html}
        </div>
    </main>

    <footer class="py-8 text-center text-xs text-gray-500 border-t border-purple-900/20">
        <p>© 2026 1into1. All rights reserved.</p>
    </footer>
</body>
</html>
"""

with open(BLOG_INDEX_FILE, "w", encoding="utf-8") as f:
    f.write(blog_index_html)
print(f"Saved Blog Hub: {BLOG_INDEX_FILE}")

# 6. Rebuild sitemap.xml
urls = [
    f"<url><loc>{BASE_URL}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>",
    f"<url><loc>{BASE_URL}/blog/</loc><changefreq>daily</changefreq><priority>0.9</priority></url>"
]

for t in published_posts:
    urls.append(f"<url><loc>{BASE_URL}/blog/{t['slug']}.html</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>")

sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>
"""

with open(SITEMAP_FILE, "w", encoding="utf-8") as f:
    f.write(sitemap_content)
print("Updated sitemap.xml with canonical URLs.")