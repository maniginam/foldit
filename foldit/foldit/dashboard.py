"""Flask web dashboard for monitoring the FoldIt robot."""
import json
from flask import Flask, jsonify, request, Response


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
#events { max-height: 200px; overflow-y: auto; }
.event { padding: 2px 0; border-bottom: 1px solid #2a2a4e; }
</style>
</head>
<body>
<h1>FoldIt Robot Dashboard</h1>
<div class="card"><div class="label">Status</div><div id="status">Loading...</div></div>
<div class="card"><div class="label">Metrics</div><div id="metrics">Loading...</div></div>
<div class="card"><div class="label">Live Events</div><div id="events"></div></div>
<div class="card">
<button onclick="fetch('/api/control/start',{method:'POST'})">Start</button>
<button onclick="fetch('/api/control/stop',{method:'POST'})">Stop</button>
<button onclick="fetch('/api/control/shutdown',{method:'POST'})">Shutdown</button>
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
if (typeof EventSource !== 'undefined') {
  var es = new EventSource('/api/events');
  es.onmessage = function(e) {
    var div = document.getElementById('events');
    var item = document.createElement('div');
    item.className = 'event';
    item.textContent = e.data;
    div.insertBefore(item, div.firstChild);
  };
}
</script>
</body></html>"""


def create_app(metrics, state_dict, metrics_store=None, event_stream=None):
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
        minutes = request.args.get("minutes", 60, type=int)
        if metrics_store:
            return jsonify(metrics_store.query_recent(minutes=minutes))
        return jsonify([])

    @app.route("/api/metrics/export")
    def metrics_export():
        fmt = request.args.get("format", "json")
        snapshot = metrics.snapshot()
        recent = metrics_store.query_recent(minutes=60) if metrics_store else []
        if fmt == "prometheus":
            lines = [
                "# HELP foldit_total_folds Total number of folds",
                "# TYPE foldit_total_folds gauge",
                f"foldit_total_folds {snapshot.get('total_folds', 0)}",
                "# HELP foldit_success_rate Fold success rate",
                "# TYPE foldit_success_rate gauge",
                f"foldit_success_rate {snapshot.get('success_rate', 0.0)}",
                "# HELP foldit_avg_cycle_sec Average fold cycle time in seconds",
                "# TYPE foldit_avg_cycle_sec gauge",
                f"foldit_avg_cycle_sec {snapshot.get('avg_cycle_sec', 0.0)}",
            ]
            return Response("\n".join(lines) + "\n", mimetype="text/plain")
        return jsonify({"summary": snapshot, "recent": recent})

    @app.route("/api/events")
    def events():
        if not event_stream:
            return jsonify([])

        def generate():
            event = event_stream.pop(timeout=0.1)
            if event:
                yield f"data: {json.dumps(event)}\n\n"

        return Response(generate(), mimetype="text/event-stream")

    @app.route("/api/control/start", methods=["POST"])
    def control_start():
        state_dict["state"] = state_dict.get("start_callback", lambda: None)() or state_dict["state"]
        return jsonify({"status": "ok"})

    @app.route("/api/control/stop", methods=["POST"])
    def control_stop():
        state_dict["state"] = state_dict.get("stop_callback", lambda: None)() or state_dict["state"]
        return jsonify({"status": "ok"})

    @app.route("/api/control/shutdown", methods=["POST"])
    def control_shutdown():
        callback = state_dict.get("shutdown_callback")
        if callback:
            callback()
        return jsonify({"status": "ok"})

    return app
