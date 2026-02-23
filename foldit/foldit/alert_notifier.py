"""Webhook-based alert notifications."""
import json
from urllib.request import Request, urlopen


class AlertNotifier:
    """Sends alert notifications to a webhook URL."""

    def __init__(self, webhook_url=None):
        self._url = webhook_url

    def notify(self, alert):
        if not self._url:
            return
        try:
            payload = json.dumps({
                "rule": alert.rule,
                "message": alert.message,
            }).encode("utf-8")
            req = Request(self._url, data=payload, headers={"Content-Type": "application/json"})
            urlopen(req, timeout=5)
        except Exception:
            pass
