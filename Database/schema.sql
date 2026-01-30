-- schema.sql
-- Real-Time Multimodal Disaster Detection database schema
-- PostgreSQL DDL: tables, indexes, and partition templates

-- 1) Extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 2) Core tables
-- social_posts is prepared for range partitioning on ingestion_timestamp
CREATE TABLE IF NOT EXISTS social_posts (
  post_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_platform TEXT NOT NULL,
  source_post_id TEXT, -- external platform id (optional, helpful for dedup)
  ingestion_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  text_content TEXT,
  image_reference TEXT,
  processing_status TEXT NOT NULL CHECK (processing_status IN ('raw','queued','processing','processed','failed')),
  UNIQUE (source_platform, source_post_id)
) PARTITION BY RANGE (ingestion_timestamp);

-- example partition for January 2026 (replace with appropriate months)
CREATE TABLE IF NOT EXISTS social_posts_2026_01 PARTITION OF social_posts
  FOR VALUES FROM ('2026-01-01 00:00:00+00') TO ('2026-02-01 00:00:00+00');

-- credibility_assessment (linked to posts)
CREATE TABLE IF NOT EXISTS credibility_assessment (
  assessment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  post_id UUID NOT NULL,
  credibility_score DOUBLE PRECISION NOT NULL CHECK (credibility_score >= 0 AND credibility_score <= 1),
  credibility_label TEXT NOT NULL CHECK (credibility_label IN ('credible','questionable','misinformation')),
  threshold_value DOUBLE PRECISION NOT NULL CHECK (threshold_value >= 0 AND threshold_value <= 1),
  assessment_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY (post_id) REFERENCES social_posts(post_id) ON DELETE CASCADE
) PARTITION BY RANGE (assessment_timestamp);

CREATE TABLE IF NOT EXISTS credibility_assessment_2026_01 PARTITION OF credibility_assessment
  FOR VALUES FROM ('2026-01-01 00:00:00+00') TO ('2026-02-01 00:00:00+00');

-- disaster_detection
CREATE TABLE IF NOT EXISTS disaster_detection (
  detection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  post_id UUID NOT NULL,
  disaster_type TEXT NOT NULL,
  text_confidence DOUBLE PRECISION NOT NULL CHECK (text_confidence >=0 AND text_confidence <=1),
  image_confidence DOUBLE PRECISION NOT NULL CHECK (image_confidence >=0 AND image_confidence <=1),
  fused_confidence DOUBLE PRECISION NOT NULL CHECK (fused_confidence >=0 AND fused_confidence <=1),
  detection_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY (post_id) REFERENCES social_posts(post_id) ON DELETE CASCADE
) PARTITION BY RANGE (detection_timestamp);

CREATE TABLE IF NOT EXISTS disaster_detection_2026_01 PARTITION OF disaster_detection
  FOR VALUES FROM ('2026-01-01 00:00:00+00') TO ('2026-02-01 00:00:00+00');

-- alerts
CREATE TABLE IF NOT EXISTS alerts (
  alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  detection_id UUID NOT NULL,
  alert_severity TEXT NOT NULL CHECK (alert_severity IN ('low','medium','high')),
  alert_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  alert_status TEXT NOT NULL CHECK (alert_status IN ('pending','sent','acknowledged','suppressed')),
  FOREIGN KEY (detection_id) REFERENCES disaster_detection(detection_id) ON DELETE CASCADE
);

-- 3) Index recommendations (create on partitions or parent depending on Postgres version)
CREATE INDEX IF NOT EXISTS idx_posts_ingestion_ts ON social_posts (ingestion_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_posts_source ON social_posts (source_platform, source_post_id);

CREATE INDEX IF NOT EXISTS idx_cred_post_id ON credibility_assessment (post_id);
CREATE INDEX IF NOT EXISTS idx_cred_assess_ts_score ON credibility_assessment (assessment_timestamp DESC, credibility_score);

CREATE INDEX IF NOT EXISTS idx_detect_post_id ON disaster_detection (post_id);
CREATE INDEX IF NOT EXISTS idx_detect_ts_conf ON disaster_detection (detection_timestamp DESC, fused_confidence DESC);

CREATE INDEX IF NOT EXISTS idx_alert_detection_id ON alerts (detection_id);
CREATE INDEX IF NOT EXISTS idx_alert_status_time ON alerts (alert_status, alert_timestamp DESC);
-- partial index for active/pending alerts
CREATE INDEX IF NOT EXISTS idx_alert_active ON alerts (alert_timestamp) WHERE alert_status = 'pending';

-- 4) Helpful views for common queries
CREATE VIEW IF NOT EXISTS v_recent_high_confidence_detections AS
SELECT d.detection_id, d.post_id, d.disaster_type, d.fused_confidence, d.detection_timestamp
FROM disaster_detection d
WHERE d.fused_confidence >= 0.8
ORDER BY d.detection_timestamp DESC;

-- 5) Partition maintenance helper (example function to create monthly partition)
-- Note: run this periodically (e.g., daily via cron or scheduler) to create partitions ahead of time.
CREATE OR REPLACE FUNCTION create_month_partition(parent_table TEXT, year INT, month INT) RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
  start_ts TIMESTAMPTZ := to_timestamp(format('%s-%s-01 00:00:00','"'||year||'"', lpad(month::text,2,'0')), 'YYYY-MM-DD HH24:MI:SS') AT TIME ZONE 'UTC';
  end_ts TIMESTAMPTZ := (start_ts + interval '1 month');
  partition_name TEXT := parent_table || '_' || year || '_' || lpad(month::text,2,'0');
  stmt TEXT;
BEGIN
  stmt := format('CREATE TABLE IF NOT EXISTS %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L);', partition_name, parent_table, start_ts, end_ts);
  EXECUTE stmt;
END;
$$;

-- Example usage:
-- SELECT create_month_partition('social_posts', 2026, 02);
-- SELECT create_month_partition('disaster_detection', 2026, 02);

-- 6) Example queries
-- Get pending high severity alerts created in the last 30 minutes
-- parameterize as needed in application code
-- SELECT a.* FROM alerts a
-- JOIN disaster_detection d USING (detection_id)
-- WHERE a.alert_status = 'pending' AND a.alert_severity = 'high' AND a.alert_timestamp >= now() - interval '30 minutes'
-- ORDER BY a.alert_timestamp DESC;

-- Get posts with low credibility in the last 24 hours
-- SELECT p.* FROM social_posts p
-- JOIN credibility_assessment c ON c.post_id = p.post_id
-- WHERE c.credibility_label = 'misinformation' AND c.assessment_timestamp >= now() - interval '24 hours'
-- ORDER BY c.assessment_timestamp DESC;

-- Insert templates
-- INSERT INTO social_posts (source_platform, source_post_id, text_content, image_reference, processing_status)
-- VALUES ('twitter','12345','Fire near downtown','https://blob/...','processed');

-- INSERT INTO credibility_assessment (post_id, credibility_score, credibility_label, threshold_value)
-- VALUES ('<post_uuid>', 0.12, 'misinformation', 0.5);

-- INSERT INTO disaster_detection (post_id, disaster_type, text_confidence, image_confidence, fused_confidence)
-- VALUES ('<post_uuid>', 'fire', 0.9, 0.75, 0.85);

-- INSERT INTO alerts (detection_id, alert_severity, alert_status)
-- VALUES ('<detection_uuid>', 'high', 'pending');

-- 7) Maintenance notes
-- - Use connection pooling (pgbouncer) and bulk insert (COPY) for high-throughput ingestion.
-- - Regularly create/drop partitions; keep retention policy to drop old partitions for cost control.
-- - Monitor autovacuum and tune settings for insert-heavy workloads.

-- End of schema.sql
