#!/usr/bin/env python3
"""
sync_resources.py
Automated curated scanner for Itqan Library (مكتبة إتقان).
Strictly extracts verified Quranic technical assets:
- AI Models & Weights
- Audio Datasets & Corpora
- Fonts & Mushaf Typography
- Open-Source Software & Tools
- Published Research & Studies
- Video Workshops & Tutorials
Excludes general chatter, proposals, inquiries, and forum issues.
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error

RESOURCES_FILE = os.path.join(os.path.dirname(__file__), "resources.json")
BASE_API = "https://community.itqan.dev/api/discussions"

TECH_TAGS = [
    "", # General feed
    "ai",
    "asr",
    "tools-resources",
    "recitation-audio-data",
    "uthmani-scripts",
    "tech-knowledge"
]

EXCLUDE_TITLE_KEYWORDS = [
    "مقترح", "فكرة", "استطلاع", "رأي", "دعوة", "سؤال", "مشكلة", 
    "استفسار", "طلب مساعدة", "تحديت نفسي", "أحتاج مساعدة", "كيف تبني",
    "خطأ في", "تحديث بخصوص", "شراكات واستثمار"
]

EXCLUDE_LINK_PATTERNS = [
    "/issues/", "/pull/", "before.html", "play.google.com", 
    "twitter.com", "x.com", "facebook.com", "google.com/search",
    "mailerlite.com", "t.me"
]

def load_existing():
    if os.path.exists(RESOURCES_FILE):
        with open(RESOURCES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_resources(data):
    with open(RESOURCES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Successfully saved {len(data)} curated resources to {RESOURCES_FILE}")

def fetch_discussions(tag="", offset=0, limit=50):
    url = f"{BASE_API}?include=tags,firstPost,user&sort=-createdAt&page[limit]={limit}&page[offset]={offset}"
    if tag:
        url += f"&filter[tag]={tag}"
        
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "ItqanLibraryCurator/3.0 (+https://github.com/nandxorandor/itqan-library)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Notice: Failed to fetch API for tag '{tag}': {e}", file=sys.stderr)
        return None

def extract_links_from_text(text):
    """Find and cleanly format genuine resource links."""
    urls = re.findall(r'https?://[^\s<>"\)\]]+', text)
    verified = []
    seen = set()
    for u in urls:
        u = u.rstrip(".,;:)'\"")
        if u in seen:
            continue
        seen.add(u)
        
        # Exclude unwanted patterns
        if any(pat in u for pat in EXCLUDE_LINK_PATTERNS) or "community.itqan.dev" in u:
            continue

        src = "رابط مباشر"
        name = u.split("/")[-1] or u

        if "github.com" in u:
            src = "GitHub"
            parts = [p for p in u.replace("https://github.com/", "").split("/") if p]
            if len(parts) >= 2:
                name = f"مستودع {parts[0]}/{parts[1]}"
            elif len(parts) == 1:
                name = f"مستودع {parts[0]}"
        elif "huggingface.co" in u:
            src = "HuggingFace"
            parts = [p for p in u.replace("https://huggingface.co/", "").split("/") if p]
            if len(parts) >= 2:
                name = f"حزمة {parts[-2]}/{parts[-1]}"
            elif len(parts) == 1:
                name = f"منظومة {parts[0]}"
        elif "archive.org" in u:
            src = "Archive.org"
            parts = [p for p in u.replace("https://archive.org/details/", "").split("/") if p]
            if parts:
                name = f"أرشيف {parts[0]}"
        elif "arxiv.org" in u or "doi.org" in u or u.endswith(".pdf"):
            src = "ورقة علمية"
            name = "الورقة البحثية المنشورة (PDF)"
        elif "youtube.com" in u or "youtu.be" in u:
            src = "فيديو مسجل"
            name = "مشاهدة الورشة المرئية"
        elif "audio.qud.dev" in u or "vercel.app" in u or "api" in u:
            src = "أداة ويب / API"
            name = u.replace("https://", "").replace("http://", "").split("/")[0]
        else:
            # Skip ambiguous external links
            continue

        verified.append({"name": name, "url": u, "src": src})
    return verified

def scan_and_update():
    existing = load_existing()
    existing_ids = {str(item.get("discussionNum")) for item in existing if item.get("discussionNum")}
    
    print(f"Curated library currently contains {len(existing)} resources.")
    new_count = 0

    for tag in TECH_TAGS:
        payload = fetch_discussions(tag=tag, offset=0, limit=50)
        if not payload or "data" not in payload:
            continue
            
        discussions = payload.get("data", [])
        included = payload.get("included", [])
        posts_by_id = {
            item["id"]: item["attributes"].get("contentHtml") or item["attributes"].get("content", "")
            for item in included if item.get("type") == "posts"
        }
        users_by_id = {
            item["id"]: item["attributes"].get("displayName") or item["attributes"].get("username", "")
            for item in included if item.get("type") == "users"
        }

        for disc in discussions:
            disc_id = str(disc["id"])
            if disc_id in existing_ids:
                continue

            attrs = disc.get("attributes", {})
            title = attrs.get("title", "")
            
            # Strict rejection of non-resource discussions
            if any(bad in title for bad in EXCLUDE_TITLE_KEYWORDS):
                continue
            
            first_post_rel = disc.get("relationships", {}).get("firstPost", {}).get("data", {})
            first_post_id = first_post_rel.get("id")
            content = posts_by_id.get(first_post_id, "")
            
            links = extract_links_from_text(content)
            # Require at least one verified repository, dataset, model, paper, or workshop
            has_gold_link = any(l["src"] in ["GitHub", "HuggingFace", "Archive.org", "ورقة علمية", "فيديو مسجل"] for l in links)
            
            if has_gold_link:
                user_rel = disc.get("relationships", {}).get("user", {}).get("data", {})
                author_name = users_by_id.get(user_rel.get("id") if user_rel else None) or "عضو في مجتمع إتقان"

                # Classify category
                title_and_text = (title + " " + content).lower()
                category = "tools"
                icon = "⚙️"
                
                if any(w in title_and_text for w in ["huggingface.co/models", "نموذج", "whisper", "zipformer", "tajweedformer", "asr"]):
                    category = "ai"
                    icon = "🤖"
                elif any(w in title_and_text for w in ["archive.org", "حزمة صوت", "تسجيلات", "تلاوات", "corpus", "dataset"]):
                    category = "audio"
                    icon = "🎙️"
                elif any(w in title_and_text for w in ["خط", "رسم عثماني", "مصحف", "ttf", "woff2", "svg"]):
                    category = "fonts"
                    icon = "✒️"
                elif any(w in title_and_text for w in ["arxiv", "paper", "ورقة بحثية", "دراسة", "معيار"]):
                    category = "research"
                    icon = "📚"
                elif any(w in title_and_text for w in ["ورشة", "محاضرة", "لقاء تقني", "شرح عملي", "youtube"]):
                    category = "workshops"
                    icon = "🎬"

                clean_desc = re.sub(r'<[^>]+>', ' ', content)
                clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
                if len(clean_desc) > 175:
                    clean_desc = clean_desc[:172] + "..."
                if not clean_desc:
                    clean_desc = f"مورد تقني معتمد مستخرج من أطروحات المجتمع: {title}"

                new_item = {
                    "id": len(existing) + 1,
                    "title": title,
                    "category": category,
                    "icon": icon,
                    "license": "مفتوح المصدر",
                    "metric": f"{len(links)} روابط فحص وتحميل مباشرة",
                    "author": author_name,
                    "discussionUrl": f"https://community.itqan.dev/d/{disc_id}",
                    "discussionNum": disc_id,
                    "description": clean_desc,
                    "links": links[:5]
                }
                existing.append(new_item)
                existing_ids.add(disc_id)
                new_count += 1
                print(f"  [+] Curated and added: {title} (#{disc_id}) -> {category}")

    if new_count > 0:
        save_resources(existing)
        print(f"Curation complete: Added {new_count} verified technical assets.")
    else:
        print("Curation complete: Library is fully up to date.")

if __name__ == "__main__":
    scan_and_update()
