"""Tests for YAML config loader."""
import os
import tempfile
import yaml


class TestConfigLoader:
    def test_load_returns_defaults_when_no_file(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        config = loader.load()
        assert config["conveyor"]["detection_distance_cm"] == 10.0
        assert config["conveyor"]["belt_speed_duty"] == 75

    def test_load_overrides_from_yaml(self):
        from foldit.config_loader import ConfigLoader
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"conveyor": {"detection_distance_cm": 15.0}}, f)
            f.flush()
            try:
                loader = ConfigLoader(path=f.name)
                config = loader.load()
                assert config["conveyor"]["detection_distance_cm"] == 15.0
                assert config["conveyor"]["belt_speed_duty"] == 75  # default preserved
            finally:
                os.unlink(f.name)

    def test_load_preserves_all_default_sections(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        config = loader.load()
        assert "servo" in config
        assert "classifier" in config
        assert "camera" in config
        assert "logging" in config
        assert "dashboard" in config
        assert "data_collection" in config
        assert "fold_verify" in config

    def test_servo_defaults(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        config = loader.load()
        assert config["servo"]["fold_angle"] == 180
        assert config["servo"]["home_angle"] == 0
        assert config["servo"]["step_delay_sec"] == 0.02

    def test_invalid_yaml_raises(self):
        from foldit.config_loader import ConfigLoader
        import pytest
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(": invalid: yaml: [[[")
            f.flush()
            try:
                loader = ConfigLoader(path=f.name)
                with pytest.raises(ValueError, match="Invalid YAML"):
                    loader.load()
            finally:
                os.unlink(f.name)

    def test_get_nested_value(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        loader.load()
        assert loader.get("conveyor.detection_distance_cm") == 10.0
        assert loader.get("servo.fold_angle") == 180

    def test_get_missing_key_returns_default(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        loader.load()
        assert loader.get("nonexistent.key", default=42) == 42


class TestConfigLoaderV4Sections:
    def test_frame_quality_defaults(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        config = loader.load()
        assert config["frame_quality"]["min_blur_score"] == 100.0
        assert config["frame_quality"]["min_contrast"] == 30.0
        assert config["frame_quality"]["min_brightness"] == 40.0
        assert config["frame_quality"]["max_brightness"] == 220.0

    def test_alerting_defaults(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        config = loader.load()
        assert config["alerting"]["consecutive_fail_threshold"] == 3
        assert config["alerting"]["rate_window"] == 20
        assert config["alerting"]["min_success_rate"] == 0.5

    def test_metrics_store_defaults(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        config = loader.load()
        assert config["metrics_store"]["db_path"] == "data/metrics.db"


class TestConfigLoaderV5Sections:
    def test_classifier_model_path_default(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        config = loader.load()
        assert config["classifier"]["model_path"] is None

    def test_classifier_min_confidence_default(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        config = loader.load()
        assert config["classifier"]["min_confidence"] == 0.7

    def test_dashboard_api_key_default(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        config = loader.load()
        assert config["dashboard"]["api_key"] is None

    def test_alerting_webhook_url_default(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        config = loader.load()
        assert config["alerting"]["webhook_url"] is None
