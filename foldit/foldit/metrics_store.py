"""SQLite-based metrics persistence."""
import sqlite3
from datetime import datetime, timezone, timedelta


class MetricsStore:
    """Durable fold metrics stored in SQLite."""

    def __init__(self, db_path="data/metrics.db"):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS folds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                garment_type TEXT NOT NULL,
                success INTEGER NOT NULL,
                cycle_sec REAL NOT NULL,
                compactness REAL,
                orientation_angle REAL
            )
        """)
        self._conn.commit()

    def record(self, garment_type, success, cycle_sec, compactness=0.0, orientation_angle=0.0):
        ts = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "INSERT INTO folds (timestamp, garment_type, success, cycle_sec, compactness, orientation_angle) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (ts, garment_type, int(success), cycle_sec, compactness, orientation_angle),
        )
        self._conn.commit()

    def query_recent(self, minutes=60):
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
        cursor = self._conn.execute(
            "SELECT * FROM folds WHERE timestamp >= ? ORDER BY timestamp",
            (cutoff,),
        )
        rows = cursor.fetchall()
        return [
            {
                "garment_type": r["garment_type"],
                "success": bool(r["success"]),
                "cycle_sec": r["cycle_sec"],
                "compactness": r["compactness"],
                "orientation_angle": r["orientation_angle"],
                "timestamp": r["timestamp"],
            }
            for r in rows
        ]

    def summary(self, minutes=60):
        rows = self.query_recent(minutes=minutes)
        total = len(rows)
        if total == 0:
            return {
                "total_folds": 0,
                "success_count": 0,
                "success_rate": 0.0,
                "counts_by_type": {},
                "avg_cycle_sec": 0.0,
            }
        successes = sum(1 for r in rows if r["success"])
        by_type = {}
        for r in rows:
            by_type[r["garment_type"]] = by_type.get(r["garment_type"], 0) + 1
        avg_cycle = sum(r["cycle_sec"] for r in rows) / total
        return {
            "total_folds": total,
            "success_count": successes,
            "success_rate": successes / total,
            "counts_by_type": by_type,
            "avg_cycle_sec": avg_cycle,
        }

    def close(self):
        self._conn.close()
