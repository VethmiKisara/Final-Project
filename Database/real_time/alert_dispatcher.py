"""
Simple alert dispatcher: polls `alerts` table for pending alerts and marks them sent after dispatching.
Replace the `dispatch_alert` function with real notification integration (email, SMS, webhook).

Run: python real_time/alert_dispatcher.py
"""
import os
import time
from typing import List

from python.db import get_session

ALERT_POLL_INTERVAL = float(os.getenv("ALERT_POLL_INTERVAL", "15"))


def dispatch_alert(alert_row: dict):
    # Placeholder: replace with integration to email/SMS/webhook
    print(f"Dispatching alert {alert_row['alert_id']} severity={alert_row['alert_severity']} timestamp={alert_row['alert_timestamp']}")


def poll_and_dispatch():
    while True:
        session = get_session()
        try:
            rows = session.execute("SELECT alert_id, alert_severity, alert_timestamp FROM alerts WHERE alert_status = 'pending' ORDER BY alert_timestamp ASC LIMIT 20").mappings().all()
            if rows:
                for r in rows:
                    dispatch_alert(r)
                    session.execute("UPDATE alerts SET alert_status = 'sent' WHERE alert_id = %s", (r['alert_id'],))
                session.commit()
            else:
                session.close()
                time.sleep(ALERT_POLL_INTERVAL)
        except Exception as exc:
            session.rollback()
            print('Alert dispatcher error:', exc)
            time.sleep(5)


if __name__ == "__main__":
    poll_and_dispatch()
