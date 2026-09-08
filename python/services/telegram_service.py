import os
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class TelegramService:
    """Simple Telegram Bot sender for Smart Alerts."""

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        self.enabled = bool(self.bot_token and self.chat_id)

        if not self.enabled:
            logger.warning(
                "Telegram alerts disabled. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env"
            )

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message to the configured chat. Returns True on success."""
        if not self.enabled:
            logger.info("Telegram not configured — skipping message")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as exc:
            logger.error("Failed to send Telegram message: %s", exc)
            return False

    def send_alert(self, alert: dict, snapshot: dict) -> bool:
        """Format and send a triggered alert."""
        name = alert.get("name", "Unnamed Alert")
        condition = alert.get("condition", "")
        threshold = alert.get("threshold")
        signal = alert.get("signal")

        condition_text = {
            "spot_above": f"Spot > {threshold}",
            "spot_below": f"Spot < {threshold}",
            "pcr_above": f"PCR > {threshold}",
            "pcr_below": f"PCR < {threshold}",
            "signal_is": f"Signal is {signal}",
            "breakout_resistance": "Breakout above Resistance",
            "breakdown_support": "Breakdown below Support",
        }.get(condition, condition)

        message = (
            f"🚨 <b>Smart Alert Triggered</b>\n\n"
            f"<b>{name}</b>\n"
            f"Condition: <code>{condition_text}</code>\n\n"
            f"📊 <b>Market Snapshot</b>\n"
            f"• Spot: <b>{snapshot.get('spot')}</b>\n"
            f"• PCR: <b>{snapshot.get('pcr')}</b>\n"
            f"• Signal: <b>{snapshot.get('signal')}</b>\n"
            f"• Support: {snapshot.get('support')}\n"
            f"• Resistance: {snapshot.get('resistance')}\n\n"
            f"⏰ {snapshot.get('evaluatedAt', '')}"
        )

        return self.send_message(message)


# Global instance
telegram_service = TelegramService()
