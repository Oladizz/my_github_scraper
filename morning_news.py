import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
TELEGRAM_CHAT_ID = str(os.getenv("TELEGRAM_CHAT_ID") or "").strip()


def strip_url_text(value):
    return re.sub(r"https?://\S+", "", value or "")


def clean_summary(text):
    text = text or ""
    text = BeautifulSoup(text, "html.parser").get_text("\n", strip=False)
    keep_lines = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.match(r"(?i)^Article URL\s*:", line):
            continue
        if re.match(r"(?i)^Comments URL\s*:", line):
            continue
        if re.match(r"(?i)^Points\s*:", line):
            continue
        if re.match(r"(?i)^#\s*Comments\s*:", line):
            continue
        keep_lines.append(line)

    text = " ".join(keep_lines)
    text = strip_url_text(text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    if not text:
        return ""
    return text[:260] + ("..." if len(text) > 260 else "")


def fetch_article_summary(url):
    if not url:
        return ""

    try:
        response = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        meta_tags = [
            soup.select_one('meta[name="description"]'),
            soup.select_one('meta[property="og:description"]'),
            soup.select_one('meta[name="twitter:description"]'),
        ]
        for tag in meta_tags:
            if tag and tag.get("content"):
                summary = clean_summary(tag["content"])
                if summary:
                    return summary

        paragraphs = [
            p.get_text(" ", strip=True)
            for p in soup.select("article p, main p, .entry-content p, .post-content p")[:4]
            if p.get_text(" ", strip=True)
        ]
        text = " ".join(paragraphs)
        summary = clean_summary(text)
        return summary if summary else ""
    except Exception:
        return ""


def is_low_quality_story(title, link, summary):
    text = f"{title} {summary} {link}".lower()
    low_quality_markers = [
        "personal blog",
        "my blog",
        "blog post",
        "thoughts",
        "notes",
        "musings",
        "just a quick note",
        "tiny writeup",
        "daily notes",
        "what i learned",
        "life update",
        "my journey",
        "rant",
        "opinion",
        "this is my take",
        "short post",
        "substack",
        "medium.com",
        "blogspot",
        "wordpress.com",
    ]

    if any(marker in text for marker in low_quality_markers):
        return True

    domain = urlparse(link).netloc.lower()
    if domain in {"medium.com", "substack.com", "blogspot.com", "wordpress.com", "www.medium.com"}:
        return True

    return False


def fetch_rss_items(feed_url, limit=3):
    response = requests.get(feed_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    root = ET.fromstring(response.content)
    items = []
    seen = set()

    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = item.findtext("description") or ""

        if not title or not link or link in seen:
            continue

        cleaned_description = clean_summary(description)
        summary = cleaned_description or fetch_article_summary(link)
        if not summary:
            summary = "This story is moving quickly and is worth a deeper read."

        if is_low_quality_story(title, link, summary):
            continue

        seen.add(link)
        items.append({
            "title": title,
            "link": link,
            "summary": summary,
        })

        if len(items) >= limit:
            break

    return items


def merge_items(feed_urls, limit=3):
    merged = []
    seen = set()
    for feed_url in feed_urls:
        for item in fetch_rss_items(feed_url, limit=2):
            if item["link"] in seen:
                continue
            seen.add(item["link"])
            merged.append(item)
            if len(merged) >= limit:
                return merged
    return merged


def fetch_developer_news(limit=3):
    feeds = [
        "https://hnrss.org/frontpage",
        "https://www.theverge.com/rss/index.xml",
        "https://www.wired.com/feed/rss",
    ]
    items = merge_items(feeds, limit=limit)
    return [item for item in items if not is_low_quality_story(item["title"], item["link"], item["summary"])]


def fetch_nigeria_news(limit=3):
    feeds = [
        "https://www.premiumtimesng.com/feed",
        "https://guardian.ng/feed/",
        "https://www.vanguardngr.com/feed/",
        "https://businessday.ng/feed/",
    ]
    items = merge_items(feeds, limit=limit)
    return [item for item in items if not is_low_quality_story(item["title"], item["link"], item["summary"])]


def fetch_crypto_news(limit=3):
    feeds = [
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://cointelegraph.com/rss",
        "https://www.theblock.co/feed",
        "https://decrypt.co/feed",
    ]
    items = merge_items(feeds, limit=limit)
    return [item for item in items if not is_low_quality_story(item["title"], item["link"], item["summary"])]


def fetch_tech_news(limit=3):
    feeds = [
        "https://openai.com/news/rss/",
        "https://www.anthropic.com/news.rss",
        "https://blog.google/feed/",
        "https://blogs.microsoft.com/feed/",
        "https://about.meta.com/blog/rss/",
        "https://www.nvidia.com/en-us/ai-data-science/rss/",
        "https://x.ai/rss",
        "https://www.mistral.ai/en/news/rss/",
        "https://cohere.com/news/rss",
        "https://www.perplexity.ai/rss",
        "https://news.google.com/rss/search?q=site:openai.com+ChatGPT+news&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=site:anthropic.com+Claude+news&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=site:google.com+Gemini+AI+news&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=site:microsoft.com+Copilot+AI+news&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=site:manus.im+AI+news&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=AI+agents+launch+news&hl=en-US&gl=US&ceid=US:en",
    ]

    filtered = []
    seen = set()
    ai_domains = (
        "openai.com",
        "anthropic.com",
        "blog.google",
        "blogs.microsoft.com",
        "meta.com",
        "nvidia.com",
        "x.ai",
        "mistral.ai",
        "cohere.com",
        "perplexity.ai",
        "manus.im",
    )

    for feed_url in feeds:
        try:
            for item in fetch_rss_items(feed_url, limit=2):
                link = item["link"]
                if link in seen:
                    continue
                seen.add(link)

                domain = urlparse(link).netloc.lower()
                title = item["title"].lower()
                if not any(keyword in title for keyword in [
                    "openai", "anthropic", "chatgpt", "claude", "microsoft",
                    "google", "gemini", "manus", "ai", "agent", "llm",
                    "copilot", "meta", "nvidia", "xai", "mistral", "cohere",
                    "perplexity", "model"
                ]):
                    if not any(domain.startswith(prefix) for prefix in ai_domains):
                        continue

                if is_low_quality_story(item["title"], item["link"], item["summary"]):
                    continue

                filtered.append(item)
                if len(filtered) >= limit:
                    return filtered
        except Exception:
            continue

    return filtered[:limit]


def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")

    chunks = []
    current = ""
    for paragraph in text.split("\n\n"):
        if len(current) + len(paragraph) + 2 <= 3500:
            current = (current + "\n\n" if current else "") + paragraph
        else:
            if current:
                chunks.append(current)
            current = paragraph
    if current:
        chunks.append(current)

    for idx, chunk in enumerate(chunks):
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        response = requests.post(url, data=data, timeout=30)
        response.raise_for_status()
        print(f"✓ Sent chunk {idx + 1}/{len(chunks)} ({len(chunk)} chars)")


def build_section(title, items, summary):
    if not items:
        return f"*{title}*\n{summary}\nNo updates right now."

    lines = [f"*{title}*", summary]
    for item in items:
        title_text = item["title"].replace("*", "").strip()
        description = item["summary"].replace("*", "").strip()
        link = item["link"]
        lines.append(f"- *{title_text}* — {description}\nMore: [Read more]({link})")
    return "\n\n".join(lines)


def build_morning_message(data):
    time_now = datetime.now().strftime("%A, %B %d, %Y")
    greeting = f"Good morning! Here is your deep-dive briefing for *{time_now}*:\n\n"

    sections = [
        build_section(
            "DEV NEWS",
            data["developer"],
            "The main stories today are shaping product strategy, AI tooling, and the next wave of engineering decisions.",
        ),
        build_section(
            "TECH NEWS",
            data["tech"],
            "The most important signals are coming from AI launches, platform moves, and the companies redefining the next generation of software and search.",
        ),
        build_section(
            "NIGERIA NEWS",
            data["nigeria"],
            "The most important headlines are those affecting policy, the economy, and public life across Nigeria.",
        ),
        build_section(
            "CRYPTO NEWS",
            data["crypto"],
            "The crypto market is moving on regulation, macro sentiment, and major institutional moves that matter for builders and traders.",
        ),
    ]

    return greeting + "\n\n".join(sections)


def main():
    data = {
        "developer": fetch_developer_news(limit=2),
        "tech": fetch_tech_news(limit=2),
        "nigeria": fetch_nigeria_news(limit=2),
        "crypto": fetch_crypto_news(limit=2),
    }

    message = build_morning_message(data)
    send_telegram_message(message)
    print("Morning briefing sent successfully.")


if __name__ == "__main__":
    main()
