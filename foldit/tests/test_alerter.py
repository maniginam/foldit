"""Tests for failure pattern alerting."""


class TestAlerter:
    def test_no_alert_on_success(self):
        from foldit.alerter import Alerter
        alerter = Alerter()
        alert = alerter.check("shirt", success=True)
        assert alert is None

    def test_consecutive_failures_triggers_alert(self):
        from foldit.alerter import Alerter
        alerter = Alerter(consecutive_fail_threshold=3)
        alerter.check("shirt", success=False)
        alerter.check("shirt", success=False)
        alert = alerter.check("shirt", success=False)
        assert alert is not None
        assert alert.rule == "consecutive_failures"

    def test_consecutive_failures_resets_on_success(self):
        from foldit.alerter import Alerter
        alerter = Alerter(consecutive_fail_threshold=3)
        alerter.check("shirt", success=False)
        alerter.check("shirt", success=False)
        alerter.check("shirt", success=True)
        alert = alerter.check("shirt", success=False)
        assert alert is None

    def test_low_success_rate_triggers_alert(self):
        from foldit.alerter import Alerter
        alerter = Alerter(rate_window=4, min_success_rate=0.5)
        alerter.check("shirt", success=True)
        alerter.check("shirt", success=False)
        alerter.check("shirt", success=False)
        alert = alerter.check("shirt", success=False)
        assert alert is not None
        assert alert.rule == "low_success_rate"

    def test_no_rate_alert_when_above_threshold(self):
        from foldit.alerter import Alerter
        alerter = Alerter(rate_window=4, min_success_rate=0.5)
        alerter.check("shirt", success=True)
        alerter.check("shirt", success=True)
        alerter.check("shirt", success=True)
        alert = alerter.check("shirt", success=False)
        assert alert is None

    def test_alert_has_expected_fields(self):
        from foldit.alerter import Alerter
        alerter = Alerter(consecutive_fail_threshold=1)
        alert = alerter.check("shirt", success=False)
        assert hasattr(alert, "rule")
        assert hasattr(alert, "message")
