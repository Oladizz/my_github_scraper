#!/usr/bin/env python3
"""
Morning routine script: sends a daily digest with developer, Nigeria, and crypto news.
Run this daily via cron at 8:00 AM or whenever you prefer.
"""

import sys
from datetime import datetime

from dotenv import load_dotenv

from morning_news import main as send_morning_briefing

load_dotenv()


def main():
    print("=" * 60)
    print("📬 Morning Briefing Started")
    print(datetime.now().strftime("%A, %B %d, %Y %H:%M"))
    print("=" * 60)

    try:
        send_morning_briefing()
        print("\n✅ Morning briefing sent successfully.")
        return 0
    except Exception as exc:
        print(f"\n❌ Morning briefing failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())