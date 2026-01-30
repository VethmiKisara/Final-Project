-- V1__create_schema.sql
-- Migration: Create core schema for Real-Time Multimodal Disaster Detection

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Parent tables (partitioned by timestamp where appropriate)
CREATE TABLE IF NOT EXISTS social_posts (
  post_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_platform TEXT NOT NULL,
  source_post_id TEXT,
  ingestion_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  text_content TEXT,
  image_reference TEXT,
  processing_status TEXT NOT NULL CHECK (processing_status IN ('raw','queued','processing','processed','failed')),
  UNIQUE (source_platform, source_post_id)
) PARTITION BY RANGE (ingestion_timestamp);

CREATE TABLE IF NOT EXISTS credibility_assessment (
  assessment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  post_id UUID NOT NULL,
  credibility_score DOUBLE PRECISION NOT NULL CHECK (credibility_score >= 0 AND credibility_score <= 1),
  credibility_label TEXT NOT NULL CHECK (credibility_label IN ('credible','questionable','misinformation')),
  threshold_value DOUBLE PRECISION NOT NULL CHECK (threshold_value >= 0 AND threshold_value <= 1),
  assessment_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY (post_id) REFERENCES social_posts(post_id) ON DELETE CASCADE
) PARTITION BY RANGE (assessment_timestamp);

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

CREATE TABLE IF NOT EXISTS alerts (
  alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  detection_id UUID NOT NULL,
  alert_severity TEXT NOT NULL CHECK (alert_severity IN ('low','medium','high')),
  alert_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  alert_status TEXT NOT NULL CHECK (alert_status IN ('pending','sent','acknowledged','suppressed')),
  FOREIGN KEY (detection_id) REFERENCES disaster_detection(detection_id) ON DELETE CASCADE
);

-- Create example initial partitions (adjust or create dynamically)
CREATE TABLE IF NOT EXISTS social_posts_2026_01 PARTITION OF social_posts
  FOR VALUES FROM ('2026-01-01 00:00:00+00') TO ('2026-02-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS credibility_assessment_2026_01 PARTITION OF credibility_assessment
  FOR VALUES FROM ('2026-01-01 00:00:00+00') TO ('2026-02-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS disaster_detection_2026_01 PARTITION OF disaster_detection
  FOR VALUES FROM ('2026-01-01 00:00:00+00') TO ('2026-02-01 00:00:00+00');

-- Indexes
CREATE INDEX IF NOT EXISTS idx_posts_ingestion_ts ON social_posts (ingestion_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_posts_source ON social_posts (source_platform, source_post_id);

CREATE INDEX IF NOT EXISTS idx_cred_post_id ON credibility_assessment (post_id);
CREATE INDEX IF NOT EXISTS idx_cred_assess_ts_score ON credibility_assessment (assessment_timestamp DESC, credibility_score);

CREATE INDEX IF NOT EXISTS idx_detect_post_id ON disaster_detection (post_id);
CREATE INDEX IF NOT EXISTS idx_detect_ts_conf ON disaster_detection (detection_timestamp DESC, fused_confidence DESC);

CREATE INDEX IF NOT EXISTS idx_alert_detection_id ON alerts (detection_id);
CREATE INDEX IF NOT EXISTS idx_alert_status_time ON alerts (alert_status, alert_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_alert_active ON alerts (alert_timestamp) WHERE alert_status = 'pending';

-- Helper function for partition creation
CREATE OR REPLACE FUNCTION create_month_partition(parent_table TEXT, year INT, month INT) RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
  start_ts TIMESTAMPTZ := make_timestamptz(year, month, 1, 0, 0, 0);
  end_ts TIMESTAMPTZ := (start_ts + interval '1 month');
  partition_name TEXT := parent_table || '_' || year || '_' || lpad(month::text,2,'0');
  stmt TEXT;
BEGIN
  stmt := format('CREATE TABLE IF NOT EXISTS %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L);', partition_name, parent_table, start_ts, end_ts);
  EXECUTE stmt;
END;
$$;

-- Utility function to construct a timestamptz from components
CREATE OR REPLACE FUNCTION make_timestamptz(y INT, m INT, d INT, hh INT, mm INT, ss INT) RETURNS TIMESTAMPTZ LANGUAGE SQL AS $$
  SELECT to_timestamp(format('%s-%s-%s %s:%s:%s', y, lpad(m::text,2,'0'), lpad(d::text,2,'0'), lpad(hh::text,2,'0'), lpad(mm::text,2,'0'), lpad(ss::text,2,'0')), 'YYYY-MM-DD HH24:MI:SS') AT TIME ZONE 'UTC';
$$;

-- Helpful view
CREATE VIEW IF NOT EXISTS v_recent_high_confidence_detections AS
SELECT d.detection_id, d.post_id, d.disaster_type, d.fused_confidence, d.detection_timestamp
FROM disaster_detection d
WHERE d.fused_confidence >= 0.8
ORDER BY d.detection_timestamp DESC;
