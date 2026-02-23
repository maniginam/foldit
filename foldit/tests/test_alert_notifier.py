"""Tests for webhook alert notifications."""
import json
from unittest.mock import patch, MagicMock


class TestAlertNotifier:
    def test_notify_sends_post(self):
        from foldit.alert_notifier import AlertNotifier
        from foldit.alerter import Alert
        notifier = AlertNotifier(webhook_url="http://example.com/hook")
        alert = Alert(rule="consecutive_failures", message="3 failures in a row")
        with patch("foldit.alert_notifier.urlopen") as mock_urlopen:
            mock_urlopen.return_value = MagicMock()
            notifier.notify(alert)
            mock_urlopen.assert_called_once()
            call_args = mock_urlopen.call_args
            req = call_args[0][0]
            body = json.loads(req.data.decode())
            assert body["rule"] == "consecutive_failures"
            assert body["message"] == "3 failures in a row"

    def test_notify_failure_does_not_raise(self):
        from foldit.alert_notifier import AlertNotifier
        from foldit.alerter import Alert
        notifier = AlertNotifier(webhook_url="http://example.com/hook")
        alert = Alert(rule="test", message="test")
        with patch("foldit.alert_notifier.urlopen", side_effect=Exception("network error")):
            notifier.notify(alert)  # should not raise

    def test_no_url_skips_notify(self):
        from foldit.alert_notifier import AlertNotifier
        from foldit.alerter import Alert
        notifier = AlertNotifier(webhook_url=None)
        alert = Alert(rule="test", message="test")
        with patch("foldit.alert_notifier.urlopen") as mock_urlopen:
            notifier.notify(alert)
            mock_urlopen.assert_not_called()
