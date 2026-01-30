"""
Connect to the RTMD PostgreSQL database, run sample queries, seed a sample record, and create partitions for the next N months.
Requires: psycopg2-binary
"""
import os
import sys
import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'rtmd')
DB_USER = os.getenv('DB_USER', 'rtmd_user')
DB_PASS = os.getenv('DB_PASS', 'change_me')

def get_conn():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)


def show_counts(conn):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT count(*) AS total FROM social_posts;")
        print('social_posts:', cur.fetchone()['total'])
        cur.execute("SELECT count(*) AS total FROM disaster_detection;")
        print('disaster_detection:', cur.fetchone()['total'])
        cur.execute("SELECT count(*) AS total FROM credibility_assessment;")
        print('credibility_assessment:', cur.fetchone()['total'])
        cur.execute("SELECT count(*) AS total FROM alerts;")
        print('alerts:', cur.fetchone()['total'])


def seed_sample(conn):
    with conn.cursor() as cur:
        cur.execute("BEGIN;")
        cur.execute(
            "INSERT INTO social_posts (source_platform, source_post_id, text_content, image_reference, processing_status) VALUES (%s,%s,%s,%s,%s) RETURNING post_id;",
            ('demo','demo-001','Demo: small brush fire near riverbank','https://example.org/img.jpg','processed')
        )
        post_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO credibility_assessment (post_id, credibility_score, credibility_label, threshold_value) VALUES (%s,%s,%s,%s);",
            (post_id, 0.4, 'questionable', 0.5)
        )
        cur.execute(
            "INSERT INTO disaster_detection (post_id, disaster_type, text_confidence, image_confidence, fused_confidence) VALUES (%s,%s,%s,%s,%s) RETURNING detection_id;",
            (post_id, 'fire', 0.82, 0.6, 0.74)
        )
        detection_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO alerts (detection_id, alert_severity, alert_status) VALUES (%s,%s,%s);",
            (detection_id, 'medium', 'pending')
        )
        cur.execute("COMMIT;")
        print('Seeded sample post/detection/alert (post_id/detection_id):', post_id, detection_id)


def list_pending_high_alerts(conn, minutes=30):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT a.alert_id, a.alert_severity, a.alert_timestamp, d.disaster_type, d.fused_confidence FROM alerts a JOIN disaster_detection d ON a.detection_id = d.detection_id WHERE a.alert_status = 'pending' AND a.alert_severity = 'high' AND a.alert_timestamp >= now() - interval '%s minutes' ORDER BY a.alert_timestamp DESC;" % minutes
        )
        rows = cur.fetchall()
        print(f"Pending high alerts in last {minutes} minutes: {len(rows)}")
        for r in rows:
            print(r)


def create_partitions(conn, months_ahead=3):
    now = datetime.datetime.utcnow()
    with conn.cursor() as cur:
        for i in range(months_ahead):
            dt = now + datetime.timedelta(days=30 * i)
            year = dt.year
            month = dt.month
            for parent in ('social_posts','disaster_detection','credibility_assessment'):
                cur.execute("SELECT create_month_partition(%s, %s, %s);", (parent, year, month))
        conn.commit()
        print(f'Created partitions for next {months_ahead} months.')


if __name__ == '__main__':
    conn = None
    try:
        conn = get_conn()
    except Exception as e:
        print('Error connecting to DB:', e)
        sys.exit(1)

    show_counts(conn)
    seed_sample(conn)
    show_counts(conn)
    list_pending_high_alerts(conn, minutes=60)
    create_partitions(conn, months_ahead=3)
    conn.close()
