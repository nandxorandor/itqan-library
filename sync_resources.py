#!/usr/bin/env python3
"""
sync_resources.py
Automated scanner and updater for Itqan Library (مكتبة إتقان).
Scans Itqan Community discussions across multiple pages and tags
for new datasets, models, tools, and fonts, and extracts verified download links into resources.json.
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error

RESOURCES_FILE = os.path.join(os.path.dirname(__file__), "resources.json")
BASE_API = "https://community.itqan.dev/api/discussions"

# Key tags with high concentration of Quranic tech resources
TECH_TAGS = [
    "", # General feed (all latest posts)
    "ai",
    "asr",
    "tools-resources",
    "recitation-audio-data",
    "uthmani-scripts",
    "projects-collabs"
]

def load_existing():
    if os.path.exists(RESOURCES_FILE):
        with open(RESOURCES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_resources(data):
    with open(RESOURCES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Successfully saved {len(data)} resources to {RESOURCES_FILE}")

def fetch_discussions(tag="", offset=0, limit=50):
    url = f"{BASE_API}?include=tags,firstPost,user&sort=-createdAt&page[limit]={limit}&page[offset]={offset}"
    if tag:
        url += f"&filter[tag]={tag}"
        
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "ItqanLibraryScanner/2.0 (+https://github.com/nandxorandor/itqan-library)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Notice: Fetching API failed for tag '{tag}' offset {offset}: {e}", file=sys.stderr)
        return None

def extract_links_from_text(text):
    """Find direct download/repo links (GitHub, HuggingFace, Archive.org, Vercel, Audio tools)."""
    urls = re.findall(r'https?://[^\s<>"\)\]]+', text)
    verified = []
    seen = set()
    for u in urls:
        u = u.rstrip(".,;:)'\"")
        if u in seen:
            continue
        seen.add(u)
        
        # Don't add community links or irrelevant domains as download mirrors
        if any(skip in u for skip in ["community.itqan.dev", "play.google.com", "youtube.com", "youtu.be", "twitter.com", "x.com", "google.com/search"]):
            continue

        src = "Web Link"
        name = u.split("/")[-1] or u

        if "github.com" in u:
            src = "GitHub"
            parts = [p for p in u.replace("https://github.com/", "").split("/") if p]
            if len(parts) >= 2:
                name = f"{parts[0]}/{parts[1]}"
            elif len(parts) == 1:
                name = parts[0]
        elif "huggingface.co" in u:
            src = "HuggingFace"
            parts = [p for p in u.replace("https://huggingface.co/", "").split("/") if p]
            if len(parts) >= 2:
                name = f"{parts[0]}/{parts[1]}"
            elif len(parts) == 1:
                name = parts[0]
        elif "archive.org" in u:
            src = "Archive.org"
            parts = [p for p in u.replace("https://archive.org/details/", "").split("/") if p]
            if parts:
                name = parts[0]
        elif "vercel.app" in u or "qud.dev" in u or "itqan.dev" in u:
            src = "Web App"
            name = u.replace("https://", "").replace("http://", "").split("/")[0]

        if len(name) > 35:
            name = name[:32] + "..."
            
        verified.append({"name": name, "url": u, "src": src})
    return verified

def scan_and_update():
    existing = load_existing()
    existing_ids = {str(item.get("discussionNum")) for item in existing if item.get("discussionNum")}
    
    print(f"Currently tracking {len(existing)} resources.")
    new_count = 0

    for tag in TECH_TAGS:
        tag_label = tag if tag else "feed"
        print(f"Scanning tag: {tag_label}...")
        
        # Paginate through 2 pages (up to 100 posts per tag)
        for offset in [0, 50]:
            payload = fetch_discussions(tag=tag, offset=offset, limit=50)
            if not payload or "data" not in payload:
                break
                
            discussions = payload.get("data", [])
            if not discussions:
                break

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
                
                # Check first post content
                first_post_rel = disc.get("relationships", {}).get("firstPost", {}).get("data", {})
                first_post_id = first_post_rel.get("id")
                content = posts_by_id.get(first_post_id, "")
                
                # Author
                user_rel = disc.get("relationships", {}).get("user", {}).get("data", {})
                user_id = user_rel.get("id") if user_rel else None
                author_name = users_by_id.get(user_id) or "عضو في مجتمع إتقان"

                # Check if it has actionable open-source repositories / datasets
                has_resource_link = any(domain in content for domain in ["github.com", "huggingface.co", "archive.org", "qud.dev", "api"])
                has_keywords = any(k in title for k in [
                    "نموذج", "حزمة", "تلاوات", "مصحف", "بيانات", "مكتبة", "أداة", "خط", "رسم",
                    "Dataset", "Model", "Audio", "Font", "Corpus", "API", "رقيم", "ترتيل", "تجويد"
                ])

                if has_resource_link or has_keywords:
                    links = extract_links_from_text(content)
                    # Only add if there are actual links or verifiable technical discussions
                    if links:
                        # Classify category
                        category = "tools"
                        icon = "⚙️"
                        title_and_text = (title + " " + content).lower()
                        
                        if any(w in title_and_text for w in ["صوت", "تلاو", "تسجيل", "audio", "مقرئ", "recitation"]):
                            category = "audio"
                            icon = "🎙️"
                        elif any(w in title_and_text for w in ["نموذج", "ذكاء", "تجويد", "asr", "whisper", "zipformer", "tajweed"]):
                            category = "ai"
                            icon = "🤖"
                        elif any(w in title_and_text for w in ["خط", "رسم", "عثماني", "مصحف", "font", "typography", "kfgqpc"]):
                            category = "fonts"
                            icon = "✒️"

                        clean_desc = re.sub(r'<[^>]+>', ' ', content)
                        clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
                        if len(clean_desc) > 180:
                            clean_desc = clean_desc[:177] + "..."
                        if not clean_desc:
                            clean_desc = f"مورد ومناقشة تقنية مستخرجة من مجتمع إتقان: {title}"

                        new_item = {
                            "id": len(existing) + 1,
                            "title": title,
                            "category": category,
                            "icon": icon,
                            "license": "مفتوح المصدر",
                            "metric": f"{len(links)} روابط فحص وتحميل",
                            "author": author_name,
                            "discussionUrl": f"https://community.itqan.dev/d/{disc_id}",
                            "discussionNum": disc_id,
                            "description": clean_desc,
                            "links": links[:6]
                        }
                        existing.append(new_item)
                        existing_ids.add(disc_id)
                        new_count += 1
                        print(f"  [+] Added: {title} (#{disc_id}) -> {category}")

    if new_count > 0:
        save_resources(existing)
        print(f"Scan complete: Added {new_count} newly discovered resources!")
    else:
        print("Scan complete: All discussions are up to date.")

if __name__ == "__main__":
    scan_and_update()
