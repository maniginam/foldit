"""Tests for dashboard API key authentication."""
import json


class FakeMetricsForAuth:
    def snapshot(self):
        return {"total_folds": 0}


class TestDashboardAuth:
    def _make_app(self, api_key=None):
        from foldit.dashboard import create_app
        from foldit.dashboard_auth import DashboardAuth
        from foldit.error_recovery import RobotState
        metrics = FakeMetricsForAuth()
        state = {"state": RobotState.IDLE, "uptime_sec": 0}
        app = create_app(metrics, state)
        if api_key:
            auth = DashboardAuth(api_key)
            auth.apply(app)
        app.config["TESTING"] = True
        return app

    def test_no_auth_allows_all(self):
        app = self._make_app()
        with app.test_client() as client:
            resp = client.get("/api/status")
            assert resp.status_code == 200

    def test_correct_key_in_header_allows(self):
        app = self._make_app(api_key="secret123")
        with app.test_client() as client:
            resp = client.get("/api/status", headers={"X-API-Key": "secret123"})
            assert resp.status_code == 200

    def test_wrong_key_denies(self):
        app = self._make_app(api_key="secret123")
        with app.test_client() as client:
            resp = client.get("/api/status", headers={"X-API-Key": "wrong"})
            assert resp.status_code == 401

    def test_missing_key_denies(self):
        app = self._make_app(api_key="secret123")
        with app.test_client() as client:
            resp = client.get("/api/status")
            assert resp.status_code == 401

    def test_key_in_query_param_allows(self):
        app = self._make_app(api_key="secret123")
        with app.test_client() as client:
            resp = client.get("/api/status?key=secret123")
            assert resp.status_code == 200

    def test_html_page_served_without_auth(self):
        app = self._make_app(api_key="secret123")
        with app.test_client() as client:
            resp = client.get("/")
            assert resp.status_code == 200
            assert b"FoldIt" in resp.data
