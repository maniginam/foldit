"""Flask web dashboard for monitoring the FoldIt robot."""
from flask import Flask, jsonify


DASHBOARD_HTML = """<!DOCTYPE html>
<html>
<head><title>FoldIt Dashboard</title>
<style>
body { font-family: monospace; background: #1a1a2e; color: #e0e0e0; padding: 20px; }
h1 { color: #00d4ff; }
.card { background: #16213e; padding: 15px; margin: 10px 0; border-radius: 8px; }
.stat { font-size: 24px; color: #00d4ff; }
.label { color: #a0a0a0; font-size: 14px; }
#status, #metrics { white-space: pre; }
</style>
</head>
<body>
<h1>FoldIt Robot Dashboard</h1>
<div class="card"><div class="label">Status</div><div id="status">Loading...</div></div>
<div class="card"><div class="label">Metrics</div><div id="metrics">Loading...</div></div>
<div class="card">
<button onclick="fetch('/api/control/start',{method:'POST'})">Start</button>
<button onclick="fetch('/api/control/stop',{method:'POST'})">Stop</button>
</div>
<script>
function update() {
  fetch('/api/status').then(r=>r.json()).then(d=>{
    document.getElementById('status').textContent=JSON.stringify(d,null,2);
  });
  fetch('/api/metrics').then(r=>r.json()).then(d=>{
    document.getElementById('metrics').textContent=JSON.stringify(d,null,2);
  });
}
update(); setInterval(update, 5000);
</script>
</body></html>"""


def create_app(metrics, state_dict, metrics_store=None):
    """Create Flask app with metrics and state references."""
    app = Flask(__name__)

    @app.route("/")
    def index():
        return DASHBOARD_HTML

    @app.route("/api/status")
    def status():
        return jsonify({
            "state": state_dict["state"].value,
            "current_garment": state_dict.get("current_garment"),
            "uptime_sec": state_dict.get("uptime_sec", 0),
        })

    @app.route("/api/metrics")
    def metrics_endpoint():
        return jsonify(metrics.snapshot())

    @app.route("/api/metrics/history")
    def metrics_history():
        from flask import request
        minutes = request.args.get("minutes", 60, type=int)
        if metrics_store:
            return jsonify(metrics_store.query_recent(minutes=minutes))
        return jsonify([])

    @app.route("/api/control/start", methods=["POST"])
    def control_start():
        state_dict["state"] = state_dict.get("start_callback", lambda: None)() or state_dict["state"]
        return jsonify({"status": "ok"})

    @app.route("/api/control/stop", methods=["POST"])
    def control_stop():
        state_dict["state"] = state_dict.get("stop_callback", lambda: None)() or state_dict["state"]
        return jsonify({"status": "ok"})

    return app
