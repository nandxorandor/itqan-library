#!/usr/bin/env python3
"""
sync_resources.py
Automated scanner and updater for Itqan Library (مكتبة إتقان).
Scans Itqan Community discussions for new datasets, models, tools, and fonts,
and extracts verified download links into resources.json.
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error

RESOURCES_FILE = os.path.join(os.path.dirname(__file__), "resources.json")
COMMUNITY_API = "https://community.itqan.dev/api/discussions?include=tags,firstPost&sort=-createdAt&page[limit]=20"

def load_existing():
    if os.path.exists(RESOURCES_FILE):
        with open(RESOURCES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_resources(data):
    with open(RESOURCES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Successfully saved {len(data)} resources to {RESOURCES_FILE}")

def fetch_discussions():
    req = urllib.request.Request(
        COMMUNITY_API,
        headers={"User-Agent": "ItqanLibraryScanner/1.0 (+https://github.com/nandxorandor/itqan-library)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Error fetching community API: {e}", file=sys.stderr)
        return None

def extract_links_from_text(text):
    """Find direct download/repo links (GitHub, HuggingFace, Archive.org, Vercel)."""
    urls = re.findall(r'https?://[^\s<>"\)\]]+', text)
    verified = []
    seen = set()
    for u in urls:
        # Strip trailing punctuation
        u = u.rstrip(".,;:")
        if u in seen:
            continue
        seen.add(u)
        src = "Web"
        if "github.com" in u:
            src = "GitHub"
        elif "huggingface.co" in u:
            src = "HuggingFace"
        elif "archive.org" in u:
            src = "Archive.org"
        elif "vercel.app" in u:
            src = "Vercel"
        elif "audio.qud.dev" in u:
            src = "Audio Portal"
        elif "everyayah.com" in u:
            src = "EveryAyah"
        
        # Don't add community links as mirrors
        if "community.itqan.dev" in u or "play.google.com" in u:
            continue

        name = u.split("/")[-1] or u
        if len(name) > 35:
            name = name[:32] + "..."
        verified.append({"name": name, "url": u, "src": src})
    return verified

def scan_and_update():
    existing = load_existing()
    existing_ids = {str(item.get("discussionNum")) for item in existing if item.get("discussionNum")}
    
    print(f"Currently tracking {len(existing)} resources.")
    payload = fetch_discussions()
    if not payload or "data" not in payload:
        print("No new data fetched from Itqan Community.")
        return

    included = payload.get("included", [])
    posts_by_id = {
        item["id"]: item["attributes"].get("contentHtml") or item["attributes"].get("content", "")
        for item in included if item.get("type") == "posts"
    }

    new_count = 0
    for disc in payload.get("data", []):
        disc_id = str(disc["id"])
        if disc_id in existing_ids:
            continue

        attrs = disc.get("attributes", {})
        title = attrs.get("title", "")
        
        # Check first post content
        first_post_rel = disc.get("relationships", {}).get("firstPost", {}).get("data", {})
        first_post_id = first_post_rel.get("id")
        content = posts_by_id.get(first_post_id, "")

        # Look for resource keywords or repository links
        has_resource_link = any(domain in content for domain in ["github.com", "huggingface.co", "archive.org"])
        has_keywords = any(k in title for k in ["نموذج", "حزمة", "تلاوات", "مصحف", "بيانات", "مكتبة", "أداة", "خط"])

        if has_resource_link or has_keywords:
            links = extract_links_from_text(content)
            if links:
                # Classify category
                category = "tools"
                icon = "⚙️"
                if any(w in title for w in ["صوت", "تلاو", "تسجيل", "Audio"]):
                    category = "audio"
                    icon = "🎙️"
                elif any(w in title for w in ["نموذج", "ذكاء", "تجويد", "ASR", "AI"]):
                    category = "ai"
                    icon = "🤖"
                elif any(w in title for w in ["خط", "رسم", "عثماني", "مصحف", "Font"]):
                    category = "fonts"
                    icon = "✒️"

                new_item = {
                    "id": len(existing) + 1,
                    "title": title,
                    "category": category,
                    "icon": icon,
                    "license": "مفتوح المصدر",
                    "metric": f"{len(links)} روابط مباشرة",
                    "author": "عضو في مجتمع إتقان",
                    "discussionUrl": f"https://community.itqan.dev/d/{disc_id}",
                    "discussionNum": disc_id,
                    "description": f"مورد تقني مستخرج آلياً من نقاشات المجتمع: {title}",
                    "links": links[:6]
                }
                existing.append(new_item)
                existing_ids.add(disc_id)
                new_count += 1
                print(f"[+] Found and added new resource: {title} (#{disc_id})")

    if new_count > 0:
        save_resources(existing)
        print(f"Added {new_count} new resources!")
    else:
        print("All resources are currently up to date.")

if __name__ == "__main__":
    scan_and_update()
