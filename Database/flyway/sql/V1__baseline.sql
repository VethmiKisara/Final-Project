-- Flyway baseline migration for RTMD
-- This migration marks the baseline state for Flyway-managed migrations.
-- The schema is managed in `migrations/`; set Flyway to baseline against the current database.

-- Example: baseline marker (no-op)
SELECT 1 AS flyway_baseline;
