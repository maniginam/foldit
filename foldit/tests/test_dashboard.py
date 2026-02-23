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


class FakeMetricsStoreForDashboard:
    def query_recent(self, minutes=60):
        return [
            {"garment_type": "shirt", "success": True, "cycle_sec": 5.0,
             "compactness": 0.85, "orientation_angle": 0.0, "timestamp": "2026-02-23T10:00:00"},
            {"garment_type": "pants", "success": False, "cycle_sec": 7.0,
             "compactness": 0.30, "orientation_angle": 12.0, "timestamp": "2026-02-23T10:01:00"},
        ]


class TestDashboardHistory:
    def _make_app_with_store(self):
        from foldit.dashboard import create_app
        from foldit.error_recovery import RobotState
        metrics = FakeMetricsForDashboard()
        store = FakeMetricsStoreForDashboard()
        state = {"state": RobotState.IDLE, "current_garment": None, "uptime_sec": 120}
        app = create_app(metrics, state, metrics_store=store)
        app.config["TESTING"] = True
        return app

    def test_history_returns_json_array(self):
        app = self._make_app_with_store()
        with app.test_client() as client:
            response = client.get("/api/metrics/history?minutes=60")
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 2
            assert data[0]["garment_type"] == "shirt"

    def test_history_default_minutes(self):
        app = self._make_app_with_store()
        with app.test_client() as client:
            response = client.get("/api/metrics/history")
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 2
