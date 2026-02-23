"""Tests for default config YAML fallback."""
import os


class TestDefaultConfig:
    def test_default_yaml_exists(self):
        path = os.path.join(os.path.dirname(__file__), "..", "foldit", "config.default.yaml")
        assert os.path.exists(path)

    def test_default_yaml_loads_all_sections(self):
        import yaml
        path = os.path.join(os.path.dirname(__file__), "..", "foldit", "config.default.yaml")
        with open(path) as f:
            config = yaml.safe_load(f)
        assert "conveyor" in config
        assert "servo" in config
        assert "camera" in config
        assert "classifier" in config
        assert "dashboard" in config
        assert "alerting" in config
        assert "frame_quality" in config
        assert "metrics_store" in config

    def test_config_loader_uses_default_yaml_fallback(self):
        from foldit.config_loader import ConfigLoader
        import os
        default_path = os.path.join(os.path.dirname(__file__), "..", "foldit", "config.default.yaml")
        loader = ConfigLoader(path="/nonexistent/config.yaml", default_path=default_path)
        config = loader.load()
        assert config["dashboard"]["port"] == 5000
