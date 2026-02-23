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


class TestDashboardSSE:
    def _make_app_with_stream(self):
        from foldit.dashboard import create_app
        from foldit.event_stream import EventStream
        from foldit.error_recovery import RobotState
        metrics = FakeMetricsForDashboard()
        state = {"state": RobotState.IDLE, "uptime_sec": 0}
        stream = EventStream()
        app = create_app(metrics, state, event_stream=stream)
        app.config["TESTING"] = True
        return app, stream

    def test_events_endpoint_exists(self):
        app, stream = self._make_app_with_stream()
        stream.push({"type": "fold", "garment": "shirt"})
        with app.test_client() as client:
            resp = client.get("/api/events")
            assert resp.status_code == 200


class TestDashboardExport:
    def _make_app_with_store(self):
        from foldit.dashboard import create_app
        from foldit.error_recovery import RobotState
        metrics = FakeMetricsForDashboard()
        store = FakeMetricsStoreForDashboard()
        state = {"state": RobotState.IDLE, "uptime_sec": 0}
        app = create_app(metrics, state, metrics_store=store)
        app.config["TESTING"] = True
        return app

    def test_export_returns_json(self):
        app = self._make_app_with_store()
        with app.test_client() as client:
            resp = client.get("/api/metrics/export")
            assert resp.status_code == 200
            data = json.loads(resp.data)
            assert "summary" in data
            assert "recent" in data

    def test_export_prometheus_format(self):
        app = self._make_app_with_store()
        with app.test_client() as client:
            resp = client.get("/api/metrics/export?format=prometheus")
            assert resp.status_code == 200
            text = resp.data.decode()
            assert "foldit_total_folds" in text
            assert "foldit_success_rate" in text


class TestDashboardShutdown:
    def _make_app_with_stop(self):
        from foldit.dashboard import create_app
        from foldit.error_recovery import RobotState
        metrics = FakeMetricsForDashboard()
        stopped = {"flag": False}
        state = {
            "state": RobotState.IDLE,
            "uptime_sec": 0,
            "shutdown_callback": lambda: stopped.update(flag=True),
        }
        app = create_app(metrics, state)
        app.config["TESTING"] = True
        return app, stopped

    def test_shutdown_endpoint(self):
        app, stopped = self._make_app_with_stop()
        with app.test_client() as client:
            resp = client.post("/api/control/shutdown")
            assert resp.status_code == 200
            assert stopped["flag"] is True
