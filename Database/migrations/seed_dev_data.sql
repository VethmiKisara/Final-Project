-- seed_dev_data.sql
-- Inserts sample records for development/testing

-- Sample post
INSERT INTO social_posts (source_platform, source_post_id, text_content, image_reference, processing_status)
VALUES ('twitter','test123','Small fire at 5th and Main. Flames visible, people evacuating.','http://example.org/image1.jpg','processed')
RETURNING post_id INTO TEMP TABLE tmp_post;

-- Another post
INSERT INTO social_posts (source_platform, source_post_id, text_content, image_reference, processing_status)
VALUES ('instagram','insta-001','Flooding in downtown area after heavy rains.','http://example.org/image2.jpg','processed')
RETURNING post_id INTO TEMP TABLE tmp_post2;

-- For predictable sample, grab ids
WITH p AS (SELECT post_id FROM social_posts ORDER BY ingestion_timestamp DESC LIMIT 2)
INSERT INTO credibility_assessment (post_id, credibility_score, credibility_label, threshold_value)
SELECT post_id, 0.15, 'misinformation', 0.5 FROM p
RETURNING assessment_id;

WITH p AS (SELECT post_id FROM social_posts ORDER BY ingestion_timestamp DESC LIMIT 2)
INSERT INTO disaster_detection (post_id, disaster_type, text_confidence, image_confidence, fused_confidence)
SELECT post_id, 'fire', 0.9, 0.7, 0.85 FROM p
RETURNING detection_id;

-- Create alerts for last inserted detections
INSERT INTO alerts (detection_id, alert_severity, alert_status)
SELECT detection_id, 'high', 'pending' FROM (
  SELECT detection_id FROM disaster_detection ORDER BY detection_timestamp DESC LIMIT 2
) d;
