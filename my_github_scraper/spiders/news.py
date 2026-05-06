import scrapy
import requests
import os

class NewsSpider(scrapy.Spider):
    name = "news"
    allowed_domains = ["aljazeera.com"]
    start_urls = ["https://www.aljazeera.com/news/"]

    def parse(self, response):
        # Al Jazeera latest news items
        articles = response.css('article.gc')
        
        for article in articles:
            title = article.css('h3.gc__title a span::text').get()
            link = article.css('h3.gc__title a::attr(href)').get()
            image = article.css('div.gc__image-wrap img::attr(src)').get()
            
            if link and not link.startswith('http'):
                link = response.urljoin(link)
            
            if image and not image.startswith('http'):
                image = response.urljoin(image)

            item = {
                'title': title,
                'link': link,
                'image': image
            }
            
            # Send to Telegram if credentials exist
            self.send_to_telegram(item)
            yield item

    def send_to_telegram(self, item):
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not token or not chat_id:
            return

        message = f"🚨 *LATEST NEWS* 🚨\n\n*Title:* {item['title']}\n\n*Link:* {item['link']}"
        
        try:
            if item['image']:
                # Send with Photo
                url = f"https://api.telegram.org/bot{token}/sendPhoto"
                data = {
                    "chat_id": chat_id,
                    "photo": item['image'],
                    "caption": message,
                    "parse_mode": "Markdown"
                }
            else:
                # Send just text
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                data = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                }
            
            requests.post(url, data=data)
        except Exception as e:
            self.logger.error(f"Failed to send to Telegram: {e}")
