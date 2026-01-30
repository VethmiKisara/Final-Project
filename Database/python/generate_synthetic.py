"""
Generate synthetic social posts, credibility assessments, disaster detections, and alerts for load testing.
Usage: python generate_synthetic.py --count 1000
"""
import os
import argparse
import random
import uuid
from datetime import datetime
import psycopg2

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'rtmd')
DB_USER = os.getenv('DB_USER', 'rtmd_user')
DB_PASS = os.getenv('DB_PASS', 'change_me')

SOURCES = ['twitter','instagram','facebook','telegram']
DISASTERS = ['fire','flood','earthquake','storm']

def get_conn():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)


def gen_text(i):
    return f"Synthetic post #{i} - possible {random.choice(DISASTERS)} reported."


def seed(count):
    conn = get_conn()
    cur = conn.cursor()
    for i in range(count):
        source = random.choice(SOURCES)
        source_post_id = str(uuid.uuid4())
        text = gen_text(i)
        image_ref = None
        status = 'processed'
        cur.execute("INSERT INTO social_posts (post_id, source_platform, source_post_id, text_content, image_reference, processing_status) VALUES (gen_random_uuid(), %s, %s, %s, %s, %s) RETURNING post_id;", (source, source_post_id, text, image_ref, status))
        post_id = cur.fetchone()[0]
        # credibility
        score = round(random.random(), 2)
        label = 'credible' if score > 0.6 else ('questionable' if score > 0.25 else 'misinformation')
        threshold = 0.5
        cur.execute("INSERT INTO credibility_assessment (assessment_id, post_id, credibility_score, credibility_label, threshold_value) VALUES (gen_random_uuid(), %s, %s, %s, %s);", (post_id, score, label, threshold))
        # detection
        dtype = random.choice(DISASTERS)
        tconf = round(random.random(), 2)
        iconf = round(random.random(), 2)
        fused = round((tconf + iconf) / 2, 2)
        cur.execute("INSERT INTO disaster_detection (detection_id, post_id, disaster_type, text_confidence, image_confidence, fused_confidence) VALUES (gen_random_uuid(), %s, %s, %s, %s, %s) RETURNING detection_id;", (post_id, dtype, tconf, iconf, fused))
        detection_id = cur.fetchone()[0]
        if fused > 0.75:
            sev = 'high'
            status = 'pending'
        elif fused > 0.5:
            sev = 'medium'
            status = 'pending'
        else:
            sev = 'low'
            status = 'suppressed'
        cur.execute("INSERT INTO alerts (alert_id, detection_id, alert_severity, alert_status) VALUES (gen_random_uuid(), %s, %s, %s);", (detection_id, sev, status))
        if i % 500 == 0:
            conn.commit()
    conn.commit()
    cur.close()
    conn.close()
    print(f"Seeded {count} synthetic posts.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=1000)
    args = parser.parse_args()
    seed(args.count)
