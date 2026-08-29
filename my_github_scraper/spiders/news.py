import os

import requests
import scrapy
from dotenv import load_dotenv

load_dotenv()


class NewsSpider(scrapy.Spider):
    name = "news"
    allowed_domains = ["aljazeera.com"]
    start_urls = ["https://www.aljazeera.com/news/"]

    def parse(self, response):
        # Al Jazeera latest news items
        articles = response.css("article.gc")

        for article in articles:
            title = article.css("h3.gc__title a span::text").get()
            link = article.css("h3.gc__title a::attr(href)").get()
            image = article.css("div.gc__image-wrap img::attr(src)").get()

            if link and not link.startswith("http"):
                link = response.urljoin(link)

            if image and not image.startswith("http"):
                image = response.urljoin(image)

            item = {
                "title": title,
                "link": link,
                "image": image,
            }

            # Send to Telegram if credentials exist
            self.send_to_telegram(item)
            yield item

    def send_to_telegram(self, item):
        token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID")

        if not token or not chat_id:
            self.logger.warning(
                "Telegram credentials missing. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID (or BOT_TOKEN/CHAT_ID)."
            )
            return

        message = f"🚨 *LATEST NEWS* 🚨\n\n*Title:* {item['title']}\n\n*Link:* {item['link']}"

        try:
            if item.get("image"):
                url = f"https://api.telegram.org/bot{token}/sendPhoto"
                data = {
                    "chat_id": chat_id,
                    "photo": item["image"],
                    "caption": message,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True,
                }
            else:
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                data = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True,
                }

            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            payload = response.json()
            if not payload.get("ok"):
                self.logger.error(f"Telegram rejected the send: {payload}")
        except requests.RequestException as exc:
            self.logger.error(f"Failed to send to Telegram: {exc}")
