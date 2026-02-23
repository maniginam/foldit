"""Tests for Flask web dashboard."""
import json


class FakeMetricsForDashboard:
    def snapshot(self):
        return {
            "total_folds": 5,
            "success_count": 4,
            "success_rate": 0.8,
            "counts_by_type": {"shirt": 3, "pants": 2},
            "avg_cycle_sec": 7.5,
        }


class TestDashboard:
    def _make_app(self):
        from foldit.dashboard import create_app
        from foldit.error_recovery import RobotState
        metrics = FakeMetricsForDashboard()
        state = {"state": RobotState.IDLE, "current_garment": None, "uptime_sec": 120}
        app = create_app(metrics, state)
        app.config["TESTING"] = True
        return app

    def test_index_returns_html(self):
        app = self._make_app()
        with app.test_client() as client:
            response = client.get("/")
            assert response.status_code == 200
            assert b"FoldIt" in response.data

    def test_status_returns_json(self):
        app = self._make_app()
        with app.test_client() as client:
            response = client.get("/api/status")
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["state"] == "idle"
            assert "uptime_sec" in data

    def test_metrics_returns_json(self):
        app = self._make_app()
        with app.test_client() as client:
            response = client.get("/api/metrics")
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["total_folds"] == 5
            assert data["success_rate"] == 0.8

    def test_control_start_returns_ok(self):
        app = self._make_app()
        with app.test_client() as client:
            response = client.post("/api/control/start")
            assert response.status_code == 200

    def test_control_stop_returns_ok(self):
        app = self._make_app()
        with app.test_client() as client:
            response = client.post("/api/control/stop")
            assert response.status_code == 200
